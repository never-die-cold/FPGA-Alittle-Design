"""Contrast-based OpenCV baseline and class-agnostic box evaluation."""

import cv2
import numpy as np


def detect_boxes(image, color_threshold=22, min_area_ratio=0.00008):
    """Find separated objects that contrast with the four image corners."""
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("image must be a BGR color image")
    height, width = image.shape[:2]
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    patch = max(2, min(height, width) // 40)
    corners = np.concatenate((lab[:patch, :patch].reshape(-1, 3),
                              lab[:patch, -patch:].reshape(-1, 3),
                              lab[-patch:, :patch].reshape(-1, 3),
                              lab[-patch:, -patch:].reshape(-1, 3)))
    background = np.median(corners, axis=0)
    distance = np.linalg.norm(lab.astype(np.float32) - background, axis=2)
    mask = (distance >= color_threshold).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    minimum = max(9, int(height * width * min_area_ratio))
    return [(int(x), int(y), int(x + w), int(y + h))
            for x, y, w, h, area in stats[1:] if area >= minimum]


def box_iou(a, b):
    """Intersection-over-union for half-open XYXY boxes."""
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return intersection / (area_a + area_b - intersection) if area_a + area_b > intersection else 0.0


def score_boxes(predicted, truth, threshold=0.5):
    """Greedily match boxes once; return precision, recall, and matched mean IoU."""
    candidates = sorted(((box_iou(p, t), i, j) for i, p in enumerate(predicted)
                         for j, t in enumerate(truth)), reverse=True)
    matched_p, matched_t, overlaps = set(), set(), []
    for overlap, i, j in candidates:
        if overlap < threshold:
            break
        if i not in matched_p and j not in matched_t:
            matched_p.add(i)
            matched_t.add(j)
            overlaps.append(overlap)
    tp = len(overlaps)
    return {"precision": tp / len(predicted) if predicted else float(not truth),
            "recall": tp / len(truth) if truth else float(not predicted),
            "mean_iou": float(np.mean(overlaps)) if overlaps else 0.0,
            "tp": tp, "fp": len(predicted) - tp, "fn": len(truth) - tp}
