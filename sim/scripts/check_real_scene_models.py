"""Compare existing FP32/INT8 models on real ROIs; no work order or accuracy claim."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "sim/vision"))
from localization_opencv import detect_boxes
from roi_preprocess import preprocess
from export_trained_payload import load_weights, quantized_input
from compare_cop_rois import layers_from_payload, predict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weights", type=Path, default=ROOT / "models/cnn-border-fill-best.pt")
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--reference-package", type=Path,
                        help="known validated package for checking the integer evaluator")
    parser.add_argument("--color-threshold", type=float, default=25)
    parser.add_argument("--background-mode", choices=("local", "local-fast"), default="local")
    parser.add_argument("--truth-counts", type=int, nargs=3, metavar=("BOLT", "NUT", "WASHER"))
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents or output.exists():
        parser.error("output must be a new directory inside the repository")
    frame = cv2.imread(str(args.frame))
    if frame is None:
        parser.error("frame cannot be decoded")
    torch.set_num_threads(4)
    model, meta = load_weights(args.weights)
    layers = layers_from_payload(args.package / "payload/provisional-model")
    reference = args.reference_package or args.package
    reference_layers = layers_from_payload(reference / "payload/provisional-model")
    golden = bytes(int(v, 16) for v in (reference / "golden/roi_001/input.hex").read_text().split())
    if predict(golden, reference_layers) != [-12, -30, 41]:
        raise RuntimeError("packaged integer golden mismatch")
    boxes = detect_boxes(frame, args.color_threshold, 0.00008, args.background_mode)
    output.mkdir(parents=True)
    classes, rows = list(meta["classes"]), []
    annotated = frame.copy()
    tiles = []
    for index, box in enumerate(boxes):
        canvas, _ = preprocess(frame, box, 64, meta.get("preprocess_mode") or "border")
        raw = quantized_input(canvas).tobytes()
        with torch.no_grad():
            fp = model(torch.from_numpy((canvas.astype(np.float32) / 255)[None, None]))[0]
        iq = predict(raw, layers)
        fp_class, iq_class = classes[int(fp.argmax())], classes[int(np.argmax(iq))]
        rows.append({"index": index, "bbox": list(box), "fp32_class": fp_class,
                     "fp32_logits": fp.tolist(), "int8_class": iq_class, "int8_logits": iq,
                     "agree": fp_class == iq_class, "roi_sha256": hashlib.sha256(raw).hexdigest()})
        (output / f"roi-{index:02d}.bin").write_bytes(raw)
        if not cv2.imwrite(str(output / f"roi-{index:02d}.png"), canvas):
            raise RuntimeError("ROI PNG save failed")
        x0, y0, x1, y1 = box
        cv2.rectangle(annotated, (x0, y0), (x1-1, y1-1), (0, 255, 0), 2)
        cv2.putText(annotated, str(index), (x0, max(18, y0-5)), 0, 0.6, (0, 255, 0), 2)
        tile = np.full((180, 256, 3), 40, np.uint8)
        tile[0:128, 64:192] = cv2.cvtColor(cv2.resize(canvas, (128, 128)), cv2.COLOR_GRAY2BGR)
        cv2.putText(tile, f"{index}: FP32 {fp_class}", (5, 148), 0, 0.45, (255, 255, 255), 1)
        cv2.putText(tile, f"INT8 {iq_class} {iq}", (5, 170), 0, 0.4, (255, 255, 255), 1)
        tiles.append(tile)
    report = {"kind": "REAL_SCENE_DEVELOPMENT", "accuracy_evaluated": False,
              "frame_sha256": hashlib.sha256(args.frame.read_bytes()).hexdigest(),
              "weights_sha256": hashlib.sha256(args.weights.read_bytes()).hexdigest(),
              "payload_sha256": hashlib.sha256((args.package / "payload/provisional-model/payload.bin").read_bytes()).hexdigest(),
              "localization": {"mode": args.background_mode, "threshold": args.color_threshold, "min_area_ratio": 0.00008},
              "human_scene_counts": dict(zip(classes, args.truth_counts)) if args.truth_counts else None,
              "roi_count": len(rows), "agreement_count": sum(r["agree"] for r in rows), "rois": rows}
    (output / "comparison.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    if not cv2.imwrite(str(output / "numbered.png"), annotated):
        raise RuntimeError("annotation save failed")
    if tiles:
        tiles.extend([np.zeros_like(tiles[0])] * ((-len(tiles)) % 3))
        cv2.imwrite(str(output / "roi-grid.png"), np.vstack([np.hstack(tiles[i:i+3]) for i in range(0, len(tiles), 3)]))
    print(json.dumps({"roi_count": len(rows), "agreement_count": report["agreement_count"], "rows": rows}))


if __name__ == "__main__":
    main()
