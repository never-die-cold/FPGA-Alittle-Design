"""Select PTQ range headroom using calibration data only, never development holdout."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
import torch
from export_trained_payload import load_weights, activation_stats, fold_bn, quantize, quantized_input
from compare_cop_rois import predict

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-assistant-reviewed", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or ROOT not in args.output.resolve().parents:
        parser.error("use a new output file inside the repository")
    annotations = json.loads(args.annotations.read_text(encoding="utf-8"))
    reviewed = (args.allow_assistant_reviewed and annotations["annotation_status"] == "MIXED_ASSISTANT_REVIEWED")
    if (annotations["annotation_status"] != "HUMAN_CONFIRMED" and not reviewed) or annotations["split"] != "TRAIN_DEVELOPMENT_ONLY":
        parser.error("calibration requires confirmed training-only ROIs")
    pixels = []
    for frame in annotations["frames"]:
        folder = (ROOT / frame["comparison_source"]).resolve().parent
        if ROOT not in folder.parents:
            parser.error("input escapes repository")
        for row in frame["targets"]:
            image = cv2.imread(str(folder / f"roi-{row['index']:02d}.png"), 0)
            if image is None or image.shape != (64, 64):
                raise ValueError("invalid calibration ROI")
            pixels.append(image)
    torch.set_num_threads(4)
    model, _ = load_weights(args.weights)
    peaks, logits, logits_peak = activation_stats(model, pixels)
    folded = fold_bn(model)
    raw_inputs = [quantized_input(image).tobytes() for image in pixels]
    candidates = []
    for factor in (1.0, 1.05, 1.1, 1.2, 1.35, 0.95, 0.9):
        layers, _ = quantize(folded, {k: v*factor for k,v in peaks.items()}, logits_peak*factor)
        predictions = [int(np.argmax(predict(raw, layers))) for raw in raw_inputs]
        correct = sum(p == int(np.argmax(fp)) for p,fp in zip(predictions, logits))
        candidates.append({"headroom": factor, "agreement_count": correct, "total": len(pixels), "predictions": predictions})
        print("CALIBRATION_RANGE " + json.dumps({"headroom": factor, "agreement": correct, "total": len(pixels)}), flush=True)
    best = max(candidates, key=lambda row: (row["agreement_count"], -abs(row["headroom"]-1)))
    report = {"kind": "TRAINING_ONLY_PTQ_CALIBRATION", "formal_validation": False,
              "selection_uses_holdout": False, "selected": best, "candidates": candidates}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("SELECTED_HEADROOM " + str(best["headroom"]), flush=True)


if __name__ == "__main__":
    main()
