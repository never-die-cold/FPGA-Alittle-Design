"""Measure the small CNN on labeled object crops from a synthetic split."""

import argparse
from pathlib import Path

import cv2
import numpy as np
import torch

from train_fastener_classifier import CLASSES, FastenerCNN
from train_scene_classifier import preprocess


def crop_tensor(image, box, input_size, mode='opposite'):
    canvas, _ = preprocess(image, box, input_size, mode)
    return torch.from_numpy(canvas.astype(np.float32)[None] / 255)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True, help="split folder with images/ and labels/")
    parser.add_argument("--weights", type=Path, required=True)
    args = parser.parse_args()
    checkpoint = torch.load(args.weights, map_location="cpu", weights_only=False)
    if tuple(checkpoint["classes"]) != CLASSES:
        raise ValueError("classifier class order does not match")
    model = FastenerCNN()
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    input_size = checkpoint.get("input_size", 64)
    crops, targets = [], []
    for path in sorted((args.dataset / "images").glob("*.png")):
        image = cv2.imread(str(path))
        height, width = image.shape[:2]
        label_path = args.dataset / "labels" / f"{path.stem}.txt"
        for line in label_path.read_text(encoding="utf-8").splitlines():
            class_id, cx, cy, bw, bh = map(float, line.split())
            class_id = int(class_id)
            if class_id >= len(CLASSES):
                continue
            box = (round((cx-bw/2)*width), round((cy-bh/2)*height),
                   round((cx+bw/2)*width), round((cy+bh/2)*height))
            crops.append(crop_tensor(image, box, input_size, checkpoint.get('preprocess_mode', 'opposite')))
            targets.append(class_id)
    confusion = torch.zeros(len(CLASSES), len(CLASSES), dtype=torch.int64)
    with torch.no_grad():
        for start in range(0, len(crops), 128):
            predictions = model(torch.stack(crops[start:start+128])).argmax(1)
            for truth, prediction in zip(targets[start:start+128], predictions):
                confusion[truth, prediction] += 1
    total = int(confusion.sum())
    accuracy = float(confusion.diag().sum()) / total if total else 0.0
    print(f"images={len(list((args.dataset / 'images').glob('*.png')))} target_crops={total} accuracy={accuracy:.4f}")
    print("confusion_rows=true_cols=predicted:", confusion.tolist())


if __name__ == "__main__":
    main()
