"""从训练好的 FP32 .pt 导出 C02 INT8 参数与 payload（真权重，不是诊断网）。

复用硬件已验证的三段路径，只替换数值：
- 打包：sim/coprocessor/generate_conv_vectors.pack_weights（O16_KH_KW_I8）
- 整数语义：src/coprocessor/int8_network_reference.run_network（C02 冻结契约）
- 容器：sim/coprocessor/generate_payload_manifest.py（manifest v1，36032 B）

判据：INT8 argmax 与 FP32 argmax 在标定图上一致率 >= --min-agreement（默认 0.9）。
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[2]
for extra in ("src/coprocessor", "src/pynq_host", "sim/coprocessor"):
    sys.path.insert(0, str(ROOT / extra))

from int8_network_reference import run_network  # noqa: E402
from generate_conv_vectors import pack_activations, pack_weights  # noqa: E402
from roi_preprocess import preprocess  # noqa: E402

EPS = 1e-5
BIT_WIDTH = 31
FLOOR = 1e-9


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, 2, 1, bias=False), nn.BatchNorm2d(16), nn.ReLU(),
            nn.Conv2d(16, 32, 3, 1, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 32, 3, 2, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 1, 1, bias=False), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 3))

    def forward(self, x):
        return self.features(x)


def load_weights(path):
    blob = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(blob, dict) or "state_dict" not in blob:
        raise ValueError("checkpoint must be a dict with state_dict")
    meta = {key: blob.get(key) for key in
            ("classes", "input_size", "architecture", "preprocess", "preprocess_mode")}
    if meta["architecture"] != "fastener-4conv-bn-v1" or meta["input_size"] != 64:
        raise ValueError(f"unexpected metadata: {meta}")
    if tuple(meta["classes"]) != ("bolt", "nut", "washer"):
        raise ValueError(f"unexpected classes: {meta['classes']}")
    model = Net()
    model.load_state_dict(blob["state_dict"])
    model.eval()
    return model, meta


def fold_bn(model):
    folded = []
    for conv_index, bn_index in ((0, 1), (3, 4), (6, 7), (9, 10)):
        conv, bn = model.features[conv_index], model.features[bn_index]
        gamma = bn.weight.detach().numpy().astype(np.float64)
        beta = bn.bias.detach().numpy().astype(np.float64)
        mean = bn.running_mean.detach().numpy().astype(np.float64)
        var = bn.running_var.detach().numpy().astype(np.float64)
        scale = gamma / np.sqrt(var + EPS)
        weight = conv.weight.detach().numpy().astype(np.float64) * scale[:, None, None, None]
        folded.append((weight, beta - mean * scale))
    folded.append((model.features[14].weight.detach().numpy().astype(np.float64),
                   model.features[14].bias.detach().numpy().astype(np.float64)))
    return folded


def activation_stats(model, images):
    captured, handles = {}, []
    for index, name in ((2, "conv1"), (5, "conv2"), (8, "conv3"), (11, "conv4")):
        handles.append(model.features[index].register_forward_hook(
            lambda _m, _i, out, key=name: captured.__setitem__(key, out.detach().numpy())))
    peaks = {name: 0.0 for name in ("conv1", "conv2", "conv3", "conv4")}
    logits_peak, logits = 0.0, []
    with torch.no_grad():
        for pixels in images:
            out = model(torch.from_numpy((pixels.astype(np.float32) / 255.0)[None, None])).numpy()[0]
            logits.append(out)
            logits_peak = max(logits_peak, float(np.abs(out).max()))
            for name, blob in captured.items():
                peaks[name] = max(peaks[name], float(np.abs(blob).max()))
    for handle in handles:
        handle.remove()
    return peaks, np.asarray(logits, np.float64), logits_peak


def _fit(weight, bias, scale_in, out_scale):
    """搜索不裁权重的最大 weight scale，保证 INT32 累加不溢出。"""
    weight_scale = np.maximum(np.abs(weight).max(axis=(1, 2, 3)), FLOOR) / 127.0
    for _ in range(10):
        weight_q = np.clip(np.round(weight / weight_scale[:, None, None, None]), -127, 127).astype(np.int8)
        bias_q = np.round(bias / (scale_in * weight_scale)).astype(np.int64)
        bound = np.abs(weight_q.astype(np.int64)).sum(axis=(1, 2, 3)) * 127
        if np.all(bias_q - bound >= -2 ** 31) and np.all(bias_q + bound <= 2 ** 31 - 1):
            break
        weight_scale = weight_scale * 2.0
    else:
        raise ValueError("cannot fit INT32 accumulation")
    ratio = scale_in * weight_scale / out_scale
    multiplier = np.clip(np.round(ratio * (1 << BIT_WIDTH)).astype(np.int64), 1, 2 ** 31 - 1)
    return {"weight": weight_q, "bias": bias_q.astype(np.int32),
            "multiplier": multiplier.astype(np.int32),
            "shift": np.full(len(ratio), BIT_WIDTH, np.uint8)}


def quantize(folded, peaks, logits_peak):
    scale_in = 1.0 / 127.0
    layers = []
    for index, name in enumerate(("conv1", "conv2", "conv3", "conv4")):
        out_scale = max(peaks[name] / 127.0, FLOOR)
        layer = _fit(folded[index][0], folded[index][1], scale_in, out_scale)
        layer["name"] = name
        layers.append(layer)
        scale_in = out_scale
    out_scale = max(logits_peak / 127.0, FLOOR)
    layer = _fit(folded[4][0][:, :, None, None], folded[4][1], scale_in, out_scale)
    layer["name"] = "logits"
    layers.append(layer)
    return layers, out_scale


def quantized_input(pixels):
    value = np.round(pixels.astype(np.float64) * 127.0 / 255.0)
    return np.clip(value, -127, 127).astype(np.int8)[None]


def emit(network, layers, cases, meta):
    weights = [word for layer in layers for word in pack_weights(layer["weight"])]
    biases = [int(v) for layer in layers for v in layer["bias"]] + [0] * 13
    multipliers = [int(v) for layer in layers for v in layer["multiplier"]] + [0] * 13
    shifts = [int(v) for layer in layers for v in layer["shift"]] + [0] * 13

    def save_hex(folder, name, values, digits):
        body = ("\n".join(f"{int(v) & ((1 << (4 * digits)) - 1):0{digits}x}" for v in values) + "\n").encode("ascii")
        (folder / name).write_bytes(body)
        return hashlib.sha256(body).hexdigest()

    manifest = {"kind": "TRAINED_PTQ_NETWORK",
                "source": {k: list(v) if isinstance(v, tuple) else v for k, v in meta.items()},
                "weight_words": len(weights),
                "layout": {"activation": "C8HW8; ROI low byte per 64-bit word",
                           "weight": "O16_KH_KW_I8; input lane fastest"},
                "model_files_sha256": {"weights.hex": save_hex(network, "weights.hex", weights, 256),
                                       "bias.hex": save_hex(network, "bias.hex", biases, 8),
                                       "multipliers.hex": save_hex(network, "multipliers.hex", multipliers, 8),
                                       "shifts.hex": save_hex(network, "shifts.hex", shifts, 2)},
                "cases": {}}
    for name, (q_input, result, fp32_class) in cases.items():
        folder = network / name
        folder.mkdir(parents=True, exist_ok=True)
        tensors, _ = run_network(q_input, layers, 5)
        hashes = {"input.hex": save_hex(folder, "input.hex", q_input.reshape(-1), 2)}
        for index in range(1, 5):
            hashes[f"conv{index}.hex"] = save_hex(folder, f"conv{index}.hex",
                                                  pack_activations(tensors[f"conv{index}"]), 16)
        hashes["gap.hex"] = save_hex(folder, "gap.hex", pack_activations(tensors["gap"][:, None, None]), 16)
        hashes["logits.hex"] = save_hex(folder, "logits.hex",
                                        pack_activations(tensors["logits"][:, None, None]), 16)
        body = (f"{result['class_id']} {result['margin_q']} {result['score_q15']} "
                f"{int(result['low_conf'])} 5\n").encode("ascii")
        (folder / "result.txt").write_bytes(body)
        hashes["result.txt"] = hashlib.sha256(body).hexdigest()
        manifest["cases"][name] = {"result": {k: int(v) for k, v in result.items()},
                                   "logits": [int(v) for v in tensors["logits"]],
                                   "fp32_class": int(fp32_class),
                                   "shapes": {k: list(v.shape) for k, v in tensors.items()},
                                   "files_sha256": hashes}
    (network / "cases.txt").write_bytes(("\n".join(cases) + "\n").encode("ascii"))
    (network / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=ROOT / "models/cnn-border-fill-best.pt")
    parser.add_argument("--images", type=Path, required=True, help="calibration image directory")
    parser.add_argument("--limit", type=int, default=32)
    parser.add_argument("--min-agreement", type=float, default=0.9)
    parser.add_argument("--model-id", type=lambda text: int(text, 0), default=0x4A303251,
                        help="distinct from the J02 diagnostic id 0x4A303250")
    parser.add_argument("--output", type=Path, default=ROOT / "sim/build/payload-trained")
    args = parser.parse_args()

    output = args.output.resolve()
    if ROOT not in output.parents:
        raise SystemExit("output must be inside the repository")
    paths = sorted(p for pattern in ("*.png", "*.jpg", "*.jpeg")
                   for p in args.images.rglob(pattern))[: args.limit]
    if not paths:
        raise SystemExit(f"no calibration images under {args.images}")

    model, meta = load_weights(args.weights)
    pixels_list = []
    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            continue
        height, width = image.shape[:2]
        canvas, _ = preprocess(image, (0, 0, width, height), 64, meta.get("preprocess_mode") or "border")
        pixels_list.append((path.stem, canvas))
    if not pixels_list:
        raise SystemExit("no readable images")

    peaks, fp32_logits, logits_peak = activation_stats(model, [item[1] for item in pixels_list])
    layers = quantize(fold_bn(model), peaks, logits_peak)[0]

    network = output / "network-vectors"
    network.mkdir(parents=True, exist_ok=True)
    cases, agreement, detail = {}, 0, []
    for index, (name, pixels) in enumerate(pixels_list):
        q_input = quantized_input(pixels)
        _, result = run_network(q_input, layers, 5)
        fp32_class = int(np.argmax(fp32_logits[index]))
        same = int(result["class_id"]) == fp32_class
        agreement += int(same)
        detail.append(f"{name}: int8={result['class_id']} fp32={fp32_class} "
                      f"score={result['score_q15']} margin={result['margin_q']} "
                      f"{'AGREE' if same else 'DIFF'}")
        cases[name] = (q_input, result, fp32_class)

    emit(network, layers, cases, meta)
    subprocess.run([sys.executable, str(ROOT / "sim/coprocessor/generate_payload_manifest.py"),
                    "--network-dir", str(network), "--output", str(output / "payload-v1"),
                    "--model-id", hex(args.model_id)], check=True)

    rate = agreement / len(pixels_list)
    print(f"agreement={agreement}/{len(pixels_list)} ({rate:.3f})")
    print("\n".join(detail[:40]))
    if rate < args.min_agreement:
        raise SystemExit(f"FAIL: agreement {rate:.3f} < {args.min_agreement}")
    digest = hashlib.sha256((output / "payload-v1/payload.bin").read_bytes()).hexdigest()
    print(f"PASS: trained payload {output / 'payload-v1'} sha256={digest}")


if __name__ == "__main__":
    main()
