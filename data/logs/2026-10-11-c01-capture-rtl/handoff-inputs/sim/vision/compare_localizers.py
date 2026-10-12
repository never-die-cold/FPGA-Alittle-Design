"""Compare class-agnostic localization on the same YOLO-labeled split."""

import argparse
import sys
import time
from pathlib import Path

import cv2
from localization_opencv import detect_boxes, score_boxes


def truth_boxes(label_path, width, height):
    boxes = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        _, cx, cy, box_w, box_h = map(float, line.split())
        boxes.append((round((cx-box_w/2)*width), round((cy-box_h/2)*height),
                      round((cx+box_w/2)*width), round((cy+box_h/2)*height)))
    return boxes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True, help="split folder with images/ and labels/")
    parser.add_argument("--engine", choices=("opencv", "yolo"), default="opencv")
    parser.add_argument("--weights", help="Ultralytics detector weights; required for yolo")
    parser.add_argument("--confidence", type=float, default=0.25, help="YOLO score cutoff")
    parser.add_argument("--color-threshold", type=float, default=22, help="OpenCV Lab distance")
    parser.add_argument("--min-area-ratio", type=float, default=0.00008)
    parser.add_argument("--limit", type=int, default=0, help="evaluate first N images; 0 means all")
    args = parser.parse_args()
    model = None
    if args.engine == "yolo":
        if not args.weights:
            parser.error("--weights is required for --engine yolo")
        from ultralytics import YOLO
        model = YOLO(args.weights)

    totals, elapsed, images = {"tp": 0, "fp": 0, "fn": 0, "iou_sum": 0.0}, 0.0, 0
    paths = sorted((args.dataset / "images").glob("*.png"))
    if args.limit:
        paths = paths[:args.limit]
    for path in paths:
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"could not read {path}")
        height, width = image.shape[:2]
        truth = truth_boxes(args.dataset / "labels" / f"{path.stem}.txt", width, height)
        start = time.perf_counter()
        if model is None:
            predicted = detect_boxes(image, args.color_threshold, args.min_area_ratio)
        else:
            result = model.predict(image, verbose=False, conf=args.confidence)[0]
            predicted = [tuple(map(int, box)) for box in result.boxes.xyxy.cpu().tolist()]
        elapsed += time.perf_counter() - start
        score = score_boxes(predicted, truth)
        for key in ("tp", "fp", "fn"):
            totals[key] += score[key]
        totals["iou_sum"] += score["mean_iou"] * score["tp"]
        images += 1

    tp, fp, fn = totals["tp"], totals["fp"], totals["fn"]
    precision = tp / (tp + fp) if tp + fp else float(not fn)
    recall = tp / (tp + fn) if tp + fn else float(not fp)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    mean_iou = totals["iou_sum"] / tp if tp else 0.0
    print(f"engine={args.engine} images={images} TP={tp} FP={fp} FN={fn}")
    print(f"precision={precision:.4f} recall={recall:.4f} f1={f1:.4f} mean_iou={mean_iou:.4f}")
    print(f"mean_ms_per_image={1000*elapsed/images:.2f}" if images else "no images found")


if __name__ == "__main__":
    main()
