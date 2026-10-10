"""File-only inspection candidate: localization -> shared ROI -> FP32 -> counts."""
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim/vision"))
from localization_opencv import detect_boxes
from roi_preprocess import preprocess, PREPROCESS_VERSION
from inspection_rules import judge


def inspect_frame(frame, classifier, order, min_score, max_targets=16):
    empty = judge([], order, min_score, max_targets)
    if (not isinstance(frame, np.ndarray) or frame.dtype != np.uint8
            or frame.ndim != 3 or frame.shape[2] != 3 or min(frame.shape[:2]) < 1):
        raise ValueError("frame must be nonempty uint8 BGR")
    height, width = frame.shape[:2]
    boxes = detect_boxes(frame)
    result = {"schema_version": 1, "mode": "FILE_REPLAY", "hardware_connected": False,
              "width": width, "height": height, "bbox_format": "XYXY_HALF_OPEN",
              "preprocess": PREPROCESS_VERSION, "model": classifier.metadata,
              "parameters": {"min_score": min_score, "max_targets": max_targets,
                             "color_threshold": 22, "min_area_ratio": 0.00008},
              "target_count": len(boxes), "targets": []}
    if len(boxes) > max_targets:
        result["decision"] = {**empty, "verdict": "RECHECK", "actual": None,
                              "delta": None, "missing": None, "extra": None,
                              "reasons": ["target_limit"]}
        return result, []
    crops = [preprocess(frame, box)[0] for box in boxes]
    predictions = classifier.predict(crops)
    if len(predictions) != len(boxes):
        raise ValueError("prediction count does not match targets")
    for identity, (box, prediction) in enumerate(zip(boxes, predictions)):
        x0, y0, x1, y1 = box
        result["targets"].append({**prediction, "target_id": identity, "bbox": list(box),
                                  "touches_border": x0 == 0 or y0 == 0 or x1 == width or y1 == height})
    result["decision"] = judge(result["targets"], order, min_score, max_targets)
    return result, crops


def annotate(frame, result):
    canvas = frame.copy()
    for target in result["targets"]:
        x0, y0, x1, y1 = target["bbox"]
        cv2.rectangle(canvas, (x0, y0), (x1 - 1, y1 - 1), (0, 180, 255), 2)
        text = f"T{target['target_id']} {target['class']} {target['score']:.3f}"
        cv2.putText(canvas, text, (x0, max(12, y0 - 4)), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 0, 255), 1)
    banner = f"FILE REPLAY | FP32 PROTOTYPE | {result['decision']['verdict']} | NOT HARDWARE"
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1] - 1, 24), (0, 0, 0), -1)
    cv2.putText(canvas, banner, (3, 16), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 1)
    return canvas
