"""Calibrate a development model on confirmed training ROIs and emit C02 payload."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import cv2
import numpy as np
import torch
from export_trained_payload import load_weights, activation_stats, fold_bn, quantize, quantized_input
from compare_cop_rois import predict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sim/coprocessor"))
from generate_conv_vectors import pack_weights
from int8_network_reference import validate_model
from int8_reference import classify_logits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-id", type=lambda v: int(v, 0), default=0x4A303252)
    parser.add_argument("--activation-headroom", type=float, default=1.0)
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents or output.exists() or args.activation_headroom <= 0:
        parser.error("output must be new and inside the repository")
    annotations = json.loads(args.annotations.read_text(encoding="utf-8"))
    if annotations["annotation_status"] != "HUMAN_CONFIRMED":
        parser.error("human-confirmed per-object labels required")
    pixels, samples = [], []
    for frame in annotations["frames"]:
        folder = (ROOT / frame["comparison_source"]).resolve().parent
        if ROOT not in folder.parents:
            parser.error("ROI path escapes repository")
        for item in frame["targets"]:
            image = cv2.imread(str(folder / f"roi-{item['index']:02d}.png"), 0)
            if image is None or image.shape != (64, 64):
                raise ValueError("calibration requires already-preprocessed 64x64 ROIs")
            if hashlib.sha256(quantized_input(image).tobytes()).hexdigest() != item["roi_sha256"]:
                raise ValueError("calibration ROI provenance mismatch")
            pixels.append(image)
            samples.append({"layout": frame["layout"], "index": item["index"], "label": item["class_label"]})
    torch.set_num_threads(4)
    model, meta = load_weights(args.weights)
    peaks, fp_logits, logits_peak = activation_stats(model, pixels)
    ranges = {name: value * args.activation_headroom for name, value in peaks.items()}
    layers, logits_scale = quantize(fold_bn(model), ranges, logits_peak * args.activation_headroom)
    validate_model(layers)
    network = output / "network-vectors"
    network.mkdir(parents=True)
    def hex_file(name, values, width):
        mask = (1 << width) - 1
        (network / name).write_text("".join(f"{int(v) & mask:0{width//4}x}\n" for v in values), encoding="ascii")
    hex_file("weights.hex", [v for layer in layers for v in pack_weights(layer["weight"])], 1024)
    for key, name, width in (("bias", "bias.hex", 32), ("multiplier", "multipliers.hex", 32), ("shift", "shifts.hex", 8)):
        hex_file(name, [int(v) for layer in layers for v in layer[key]] + [0] * 13, width)
    subprocess.run([sys.executable, str(ROOT / "sim/coprocessor/generate_payload_manifest.py"),
                    "--network-dir", str(network), "--output", str(output / "payload/provisional-model"),
                    "--model-id", hex(args.model_id)], check=True)
    from compare_cop_rois import layers_from_payload
    packaged = layers_from_payload(output / "payload/provisional-model")
    rows = []
    for index, image in enumerate(pixels):
        raw = quantized_input(image).tobytes()
        logits = predict(raw, packaged)
        fp_class, iq_class = int(fp_logits[index].argmax()), int(np.argmax(logits))
        rows.append({**samples[index], "fp32_class": meta["classes"][fp_class],
                     "int8_class": meta["classes"][iq_class], "int8_logits": logits,
                     "agree": fp_class == iq_class})
    reference = output / "golden/roi_001"
    reference.mkdir(parents=True)
    (reference / "input.hex").write_text("".join(f"{v:02x}\n" for v in quantized_input(pixels[0]).tobytes()), encoding="ascii")
    (reference / "result.json").write_text(json.dumps(classify_logits(rows[0]["int8_logits"], 5), indent=2)+"\n")
    report = {"kind": "DEVELOPMENT_PTQ", "formal_validation": False,
              "calibration_count": len(pixels), "calibration_only_training_rois": True,
              "weights_sha256": hashlib.sha256(args.weights.read_bytes()).hexdigest(),
              "annotations_sha256": hashlib.sha256(args.annotations.read_bytes()).hexdigest(),
              "activation_peaks": peaks, "logits_scale": logits_scale,
              "activation_headroom": args.activation_headroom,
              "agreement_count": sum(row["agree"] for row in rows), "rows": rows}
    (output / "quantization.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    manifest_path = output / "payload/provisional-model/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["generation_command"] = "python sim/scripts/quantize_real_rois.py " + " ".join(sys.argv[1:])
    manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    (manifest_path.parent / "manifest.json.sha256").write_text(hashlib.sha256(manifest_path.read_bytes()).hexdigest()+"  manifest.json\n")
    print("PTQ_COMPLETE " + json.dumps({"calibration": len(rows), "agreement": report["agreement_count"]}), flush=True)


if __name__ == "__main__":
    main()
