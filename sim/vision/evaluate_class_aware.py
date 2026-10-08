"""Class-aware test of YOLO or OpenCV localization plus the small crop CNN."""

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from evaluate_fastener_classifier import crop_tensor
from localization_opencv import box_iou, detect_boxes
from train_fastener_classifier import CLASSES, FastenerCNN
from train_scene_classifier import preprocess


def truths(path, width, height):
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        class_id, cx, cy, bw, bh = map(float, line.split())
        result.append((int(class_id), (round((cx-bw/2)*width), round((cy-bh/2)*height),
                                      round((cx+bw/2)*width), round((cy+bh/2)*height))))
    return result


def count_matches(predicted, actual, classes, threshold=0.5):
    pairs = sorted(((box_iou(p[1], t[1]), i, j) for i, p in enumerate(predicted)
                    for j, t in enumerate(actual)), reverse=True)
    used_p, used_t, matrix = set(), set(), [[0]*(classes+1) for _ in range(classes)]
    for overlap, i, j in pairs:
        if overlap < threshold:
            break
        if i not in used_p and j not in used_t:
            used_p.add(i); used_t.add(j)
            predicted_class = predicted[i][0] if 0 <= predicted[i][0] < classes else classes
            if 0 <= actual[j][0] < classes:
                matrix[actual[j][0]][predicted_class] += 1
    # Fixed-IoU, same-class greedy matching; confusion above is diagnostic only.
    used_p, used_t = set(), set()
    for overlap, i, j in pairs:
        if overlap < threshold:
            break
        if predicted[i][0] == actual[j][0] and i not in used_p and j not in used_t:
            used_p.add(i); used_t.add(j)
    tp = len(used_p)
    return tp, len(predicted)-tp, len(actual)-tp, matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--engine", choices=("hybrid", "hog", "yolo"), required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.55)
    parser.add_argument("--class-confidence", type=float, default=0.0,
                        help="reject hybrid crop classes below this softmax score")
    parser.add_argument("--color-threshold", type=float, default=22)
    parser.add_argument("--min-area-ratio", type=float, default=0.00008)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(4)
    cv2.setNumThreads(1)
    if args.engine == "yolo":
        from ultralytics import YOLO
        model = YOLO(str(args.weights))
    elif args.engine == "hog":
        model = cv2.ml.SVM_load(str(args.weights))
        hog = cv2.HOGDescriptor((64,64), (16,16), (8,8), (8,8), 9)
    else:
        state = torch.load(args.weights, map_location="cpu", weights_only=False)
        model = FastenerCNN(); model.load_state_dict(state["state_dict"]); model.eval()
        input_size = state.get("input_size", 64)

    totals, confusion, elapsed, count = [0, 0, 0], [[0]*(len(CLASSES)+1) for _ in CLASSES], 0.0, 0
    records = []
    for path in sorted((args.dataset / "images").glob("*.png")):
        image = cv2.imread(str(path)); height, width = image.shape[:2]
        actual = truths(args.dataset / "labels" / f"{path.stem}.txt", width, height)
        start = time.perf_counter()
        if args.engine == "yolo":
            result = model.predict(image, verbose=False, conf=args.confidence)[0]
            predicted = [(int(label), tuple(map(int, box))) for box, label in
                         zip(result.boxes.xyxy.cpu().tolist(), result.boxes.cls.cpu().tolist())]
        elif args.engine == "hybrid":
            boxes = detect_boxes(image, args.color_threshold, args.min_area_ratio)
            tensors = [crop_tensor(image, box, input_size, state.get('preprocess_mode', 'opposite')) for box in boxes]
            if tensors:
                with torch.no_grad():
                    probabilities = torch.softmax(model(torch.stack(tensors)), dim=1)
                    scores, labels = probabilities.max(1)
                    labels = [label.item() if score.item() >= args.class_confidence
                              else len(CLASSES) for score, label in zip(scores, labels)]
                predicted = list(zip(labels, boxes))
            else:
                predicted = []
        else:
            boxes = detect_boxes(image, args.color_threshold, args.min_area_ratio)
            features = [hog.compute(preprocess(image, box, 64)[0]).reshape(-1) for box in boxes]
            if features:
                labels = model.predict(np.asarray(features, np.float32))[1].reshape(-1).astype(int)
                predicted = list(zip(labels.tolist(), boxes))
            else:
                predicted = []
        elapsed += time.perf_counter() - start
        tp, fp, fn, matrix = count_matches(predicted, actual, len(CLASSES))
        accepted = [p for p in predicted if 0 <= p[0] < len(CLASSES)]
        accepted_tp = count_matches(accepted, actual, len(CLASSES))[0]
        exact_counts = all(sum(p[0] == c for p in accepted) == sum(t[0] == c for t in actual)
                           for c in range(len(CLASSES))) and len(accepted) == len(predicted)
        records.append({'image': path.name, 'tp': tp, 'fp': fp, 'fn': fn,
                        'proposals': len(predicted), 'accepted': len(accepted),
                        'accepted_tp': accepted_tp, 'review': len(accepted) != len(predicted),
                        'exact_counts': exact_counts, 'perfect_detection': fp == 0 and fn == 0})
        totals[0] += tp; totals[1] += fp; totals[2] += fn
        for row in range(len(CLASSES)):
            for col in range(len(CLASSES)+1):
                confusion[row][col] += matrix[row][col]
        count += 1
    tp, fp, fn = totals
    if count == 0:
        raise ValueError(f'no PNG images found under {args.dataset / "images"}')
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
    print(f"engine={args.engine} images={count} class_TP={tp} FP={fp} FN={fn} P={precision:.4f} R={recall:.4f} F1={f1:.4f}")
    print(f"mean_ms_per_image={1000*elapsed/count:.2f}; confusion rows=true cols=predicted: {confusion}")
    accepted = sum(r['accepted'] for r in records)
    proposals = sum(r['proposals'] for r in records)
    summary = {'precision': precision, 'recall': recall, 'f1': f1,
               'exact_count_accuracy': sum(r['exact_counts'] for r in records)/count,
               'perfect_detection_rate': sum(r['perfect_detection'] for r in records)/count,
               'accepted_precision': sum(r['accepted_tp'] for r in records)/max(1, accepted),
               'proposal_coverage': accepted/max(1, proposals),
               'review_image_rate': sum(r['review'] for r in records)/count,
               'mean_ms_including_cold_start': 1000*elapsed/count}
    print(json.dumps(summary))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({'config': {k:str(v) for k,v in vars(args).items()},
                                          'summary': summary, 'images': records}, indent=2), encoding='utf-8')


if __name__ == "__main__":
    main()
