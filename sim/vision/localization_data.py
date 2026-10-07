"""Small helpers for leakage-safe fastener crop preparation."""

import hashlib
import csv
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def source_split(image_name, salt="fastener-v1"):
    """Assign every crop from one source image to the same 80/10/10 split."""
    digest = hashlib.sha256((salt + image_name).encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    return "train" if bucket < 80 else "val" if bucket < 90 else "test"


def iter_dataset_crops(dataset_root, split):
    """Yield class, RGBA crop, source name, and box from one source-image split."""
    if split not in {"train", "val", "test"}:
        raise ValueError("split must be train, val, or test")
    root = Path(dataset_root)
    grouped = defaultdict(list)
    with (root / "train_bboxes.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            grouped[row["image_name"]].append(row)

    for name, rows in sorted(grouped.items()):
        if source_split(name) != split:
            continue
        with Image.open(root / "train" / "train" / name) as image:
            for row in rows:
                box = tuple(int(row[key]) for key in ("x_min", "y_min", "x_max", "y_max"))
                rgba, tight_box = foreground_crop(image, box)
                yield row["class"], rgba, name, tight_box


def cache_split_crops(dataset_root, cache_root, split, per_class_limit=100, seed=0):
    """Save a seeded, capped crop pool under split/seed/class directories."""
    if per_class_limit < 1:
        raise ValueError("per_class_limit must be positive")
    rng, seen, samples = np.random.default_rng(seed), Counter(), defaultdict(list)
    for class_name, crop, source, box in iter_dataset_crops(dataset_root, split):
        seen[class_name] += 1
        bucket = samples[class_name]
        item = (crop, source, box)
        if len(bucket) < per_class_limit:
            bucket.append(item)
        else:
            index = int(rng.integers(seen[class_name]))
            if index < per_class_limit:
                bucket[index] = item

    counts = {}
    for class_name, items in samples.items():
        folder = Path(cache_root) / split / f"seed-{seed}" / class_name
        folder.mkdir(parents=True, exist_ok=True)
        for crop, source, box in items:
            stem = f"{Path(source).stem}_{box[0]}_{box[1]}_{box[2]}_{box[3]}"
            Image.fromarray(crop).save(folder / f"{stem}.png")
        counts[class_name] = len(items)
    return counts


def random_contrast_background(parts, rng, canvas_size=(1280, 720)):
    """Make a seeded, softly textured background opposite the crop luminance."""
    pixels = np.concatenate([crop[crop[:, :, 3] > 127, :3] for _, crop in parts])
    luminance = float(np.mean(pixels @ np.array((0.299, 0.587, 0.114))))
    level = rng.integers(24, 81) if luminance >= 128 else rng.integers(176, 233)
    width, height = canvas_size
    tint = rng.integers(-7, 8, size=(1, 1, 3))
    vertical = np.linspace(-8, 8, height, dtype=np.float32)[:, None, None]
    horizontal = np.linspace(-8, 8, width, dtype=np.float32)[None, :, None]
    noise = rng.normal(0, 2.5, (height, width, 1))
    texture = level + tint + vertical + horizontal + noise
    return np.clip(np.rint(texture), 0, 255).astype(np.uint8)


def save_yolo_scene(output_dir, stem, image, annotations, class_to_id):
    """Save an RGB scene and normalized YOLO boxes in images/ and labels/."""
    height, width = image.shape[:2]
    lines = []
    for item in annotations:
        x0, y0, x1, y1 = item["bbox"]
        if item["class_name"] not in class_to_id or not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError("unknown class or box outside image")
        center_x, center_y = (x0 + x1) / (2 * width), (y0 + y1) / (2 * height)
        box_w, box_h = (x1 - x0) / width, (y1 - y0) / height
        lines.append(f"{class_to_id[item['class_name']]} {center_x:.6f} {center_y:.6f} {box_w:.6f} {box_h:.6f}")

    root = Path(output_dir)
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "labels").mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(root / "images" / f"{stem}.png")
    label_path = root / "labels" / f"{stem}.txt"
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def foreground_crop(image, xyxy, deviation=24):
    """Extract a tight RGBA object crop from a white-background slot box."""
    x0, y0, x1, y1 = map(int, xyxy)
    if x0 < 0 or y0 < 0 or x1 > image.width or y1 > image.height:
        raise ValueError("box is outside the source image")
    if x0 >= x1 or y0 >= y1 or not 1 <= deviation <= 254:
        raise ValueError("invalid box or foreground deviation")

    rgb = np.asarray(image.crop((x0, y0, x1, y1)).convert("RGB"))
    mask = (255 - rgb.min(axis=2) >= deviation).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("no foreground pixels in box")

    left, right = xs.min(), xs.max() + 1
    top, bottom = ys.min(), ys.max() + 1
    alpha = mask[top:bottom, left:right] * 255
    rgba = np.dstack((rgb[top:bottom, left:right], alpha))
    return rgba, (x0 + left, y0 + top, x0 + right, y0 + bottom)


def compose_scene(parts, canvas_size=(1280, 720), seed=0,
                  background=None, object_fraction=(0.08, 0.20), gap=6):
    """Place (class_name, RGBA crop) items randomly; return RGB image and XYXY boxes."""
    width, height = canvas_size
    rng = np.random.default_rng(seed)
    if background is None:
        canvas = random_contrast_background(parts, rng, canvas_size)
    else:
        canvas = np.empty((height, width, 3), dtype=np.uint8)
        canvas[:] = background
    boxes, annotations = [], []

    for index in rng.permutation(len(parts)):
        class_name, crop = parts[index]
        if crop.ndim != 3 or crop.shape[2] != 4:
            raise ValueError("each crop must be an RGBA image")
        scale = (rng.uniform(*object_fraction) * min(width, height)
                 / max(crop.shape[:2]))
        size = (max(1, round(crop.shape[1] * scale)),
                max(1, round(crop.shape[0] * scale)))
        resized = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
        h, w = resized.shape[:2]
        angle = rng.uniform(0, 360)
        radians = np.deg2rad(angle)
        out_w = int(np.ceil(h * abs(np.sin(radians)) + w * abs(np.cos(radians))))
        out_h = int(np.ceil(h * abs(np.cos(radians)) + w * abs(np.sin(radians))))
        matrix = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), angle, 1)
        matrix[0, 2] += (out_w - w) / 2
        matrix[1, 2] += (out_h - h) / 2
        rotated = cv2.warpAffine(resized, matrix, (out_w, out_h))
        ys, xs = np.nonzero(rotated[:, :, 3] > 127)
        if not len(xs) or out_w > width or out_h > height:
            raise ValueError("crop is empty or too large for the canvas")
        local = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

        for _ in range(200):
            x, y = int(rng.integers(width - out_w + 1)), int(rng.integers(height - out_h + 1))
            box = (x + local[0], y + local[1], x + local[2], y + local[3])
            if all(box[2] + gap <= b[0] or b[2] + gap <= box[0]
                   or box[3] + gap <= b[1] or b[3] + gap <= box[1] for b in boxes):
                break
        else:
            raise ValueError("could not place all objects without overlap")

        roi = canvas[y:y + out_h, x:x + out_w].astype(np.float32)
        alpha = rotated[:, :, 3:4].astype(np.float32) / 255
        canvas[y:y + out_h, x:x + out_w] = np.rint(
            rotated[:, :, :3] * alpha + roi * (1 - alpha)).astype(np.uint8)
        boxes.append(box)
        annotations.append({"class_name": str(class_name), "bbox": list(box)})
    return canvas, annotations


def generate_yolo_scene_from_cache(cache_root, output_root, split, cache_seed,
                                   scene_seed, object_count, class_to_id,
                                   canvas_size=(1280, 720)):
    """Sample a balanced scene from one cached split and save its YOLO files."""
    if split not in {"train", "val", "test"} or object_count < 1 or not class_to_id:
        raise ValueError("invalid split, object_count, or class map")
    rng = np.random.default_rng(scene_seed)
    root = Path(cache_root) / split / f"seed-{cache_seed}"
    pools = {name: sorted((root / name).glob("*.png")) for name in class_to_id}
    missing = [name for name, files in pools.items() if not files]
    if missing:
        raise ValueError(f"no cached crops for classes: {missing}")

    classes = list(class_to_id)
    selected = [classes[index % len(classes)] for index in range(object_count)]
    rng.shuffle(selected)
    parts = []
    for name in selected:
        path = pools[name][int(rng.integers(len(pools[name])))]
        with Image.open(path) as crop:
            parts.append((name, np.asarray(crop.convert("RGBA"))))
    image, annotations = compose_scene(parts, canvas_size, scene_seed)
    stem = f"{split}-{scene_seed:06d}"
    save_yolo_scene(Path(output_root) / split, stem, image, annotations, class_to_id)
    return stem


def generate_yolo_scenes_from_cache(cache_root, output_root, split, cache_seed,
                                    first_scene_seed, scene_count, object_count,
                                    class_to_id, canvas_size=(1280, 720)):
    """Generate a reproducible sequence of scenes for one dataset split."""
    if scene_count < 1:
        raise ValueError("scene_count must be positive")
    return [generate_yolo_scene_from_cache(
        cache_root, output_root, split, cache_seed, seed, object_count,
        class_to_id, canvas_size)
        for seed in range(first_scene_seed, first_scene_seed + scene_count)]
