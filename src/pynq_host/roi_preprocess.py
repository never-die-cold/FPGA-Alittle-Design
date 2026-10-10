"""Shared scene crop preprocessing; border/64 is inspection V0's candidate."""
import cv2
import numpy as np

PREPROCESS_VERSION = "scene-gray-border-padding-v1"


def preprocess(image, box, input_size=64, mode="border"):
    """Return uint8 square pixels and fill level; XYXY boxes are half-open."""
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
            or image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 1):
        raise ValueError("image must be nonempty uint8 BGR")
    if (not isinstance(box, (tuple, list)) or len(box) != 4
            or any(type(value) is not int for value in box)):
        raise ValueError("box must contain four integer coordinates")
    x0, y0, x1, y1 = box
    height, width = image.shape[:2]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("invalid half-open box bounds")
    if type(input_size) is not int or input_size not in (64, 96):
        raise ValueError("input size must be 64 or 96")
    if mode not in ("border", "opposite"):
        raise ValueError("unknown preprocessing mode")
    crop = cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    height, width = crop.shape
    object_size = round(input_size * 0.65625)
    scale = min(object_size / width, object_size / height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    crop = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
    if mode == "border":
        level = int(np.median(np.concatenate((crop[0], crop[-1], crop[:, 0], crop[:, -1]))))
    else:
        level = 50 if float(crop.mean()) > 128 else 205
    canvas = np.full((input_size, input_size), level, dtype=np.uint8)
    y, x = (input_size - size[1]) // 2, (input_size - size[0]) // 2
    canvas[y:y + size[1], x:x + size[0]] = crop
    return canvas, level
