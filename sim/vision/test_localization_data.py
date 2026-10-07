"""Small deterministic checks for localization data helpers."""

import csv
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from localization_data import (compose_scene, iter_dataset_crops,
                               cache_split_crops, random_contrast_background, save_yolo_scene,
                               generate_yolo_scene_from_cache,
                               generate_yolo_scenes_from_cache, source_split)
from localization_opencv import detect_boxes, score_boxes


def run():
    crop = np.zeros((32, 32, 4), dtype=np.uint8)
    crop[4:28, 8:24] = (190, 150, 90, 255)
    parts = [(name, crop.copy()) for name in ("bolt", "nut", "washer")]
    image, labels = compose_scene(parts, (320, 240), seed=19)
    repeat, repeated_labels = compose_scene(parts, (320, 240), seed=19)
    assert image.shape == (240, 320, 3)
    assert labels == repeated_labels and np.array_equal(image, repeat)
    assert {item["class_name"] for item in labels} == {"bolt", "nut", "washer"}
    for index, item in enumerate(labels):
        x0, y0, x1, y1 = item["bbox"]
        assert 0 <= x0 < x1 <= 320 and 0 <= y0 < y1 <= 240
        for other in labels[index + 1:]:
            a, b, c, d = other["bbox"]
            assert x1 <= a or c <= x0 or y1 <= b or d <= y0
    print("PASS: deterministic RGB scene, labels, bounds, and non-overlap")


def check_dataset_crops():
    build = Path(__file__).parents[1] / "build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as folder:
        root = Path(folder)
        images = root / "train" / "train"
        images.mkdir(parents=True)
        name = "fixture.png"
        image = Image.new("RGB", (48, 32), "white")
        draw = ImageDraw.Draw(image)
        for box in ((4, 4, 12, 12), (20, 4, 28, 12), (36, 20, 44, 28)):
            draw.rectangle(box, fill="black")
        image.save(images / name)
        with (root / "train_bboxes.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=("image_name", "class", "x_min", "y_min", "x_max", "y_max"))
            writer.writeheader()
            writer.writerows(({"image_name": name, "class": label, "x_min": x0, "y_min": y0,
                               "x_max": x1, "y_max": y1}
                              for label, x0, y0, x1, y1 in (("bolt", 0, 0, 16, 16),
                                                           ("bolt", 16, 0, 32, 16),
                                                           ("nut", 32, 16, 48, 32))))
        split = source_split(name)
        crops = list(iter_dataset_crops(root, split))
        other = next(value for value in ("train", "val", "test") if value != split)
        assert len(crops) == 3 and not list(iter_dataset_crops(root, other))
        assert {item[0] for item in crops} == {"bolt", "nut"}
        assert all(item[2] == name and item[1].shape[2] == 4 for item in crops)
        counts = cache_split_crops(root, root / "cache", split, per_class_limit=1, seed=4)
        files = list((root / "cache" / split / "seed-4").rglob("*.png"))
        assert counts == {"bolt": 1, "nut": 1} and len(files) == 2
        stem = generate_yolo_scene_from_cache(root / "cache", root / "generated", split,
                                              4, 13, 2, {"bolt": 0, "nut": 1}, (320, 240))
        labels = (root / "generated" / split / "labels" / f"{stem}.txt").read_text().splitlines()
        with Image.open(root / "generated" / split / "images" / f"{stem}.png") as saved:
            assert len(labels) == 2 and saved.size == (320, 240)
        stems = generate_yolo_scenes_from_cache(root / "cache", root / "generated", split,
                                                4, 20, 3, 2, {"bolt": 0, "nut": 1}, (320, 240))
        assert stems == [f"{split}-000020", f"{split}-000021", f"{split}-000022"]
        assert all((root / "generated" / split / "labels" / f"{value}.txt").exists()
                   for value in stems)
    print("PASS: source-image split is shared by all extracted crops")


def check_background_contrast():
    bright = np.full((8, 8, 4), (220, 210, 200, 255), dtype=np.uint8)
    dark = np.full((8, 8, 4), (30, 35, 40, 255), dtype=np.uint8)
    bright_bg = random_contrast_background([("bolt", bright)], np.random.default_rng(4), (32, 24))
    dark_bg = random_contrast_background([("bolt", dark)], np.random.default_rng(4), (32, 24))
    repeat = random_contrast_background([("bolt", bright)], np.random.default_rng(4), (32, 24))
    assert bright_bg.shape == (24, 32, 3) and np.array_equal(bright_bg, repeat)
    assert np.std(bright_bg) > 0.5
    assert np.max(bright_bg) < 96 and np.min(dark_bg) > 160
    print("PASS: seeded backgrounds contrast with bright and dark crops")


def check_yolo_save():
    build = Path(__file__).parents[1] / "build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as folder:
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        annotations = [{"class_name": "bolt", "bbox": [10, 20, 30, 40]}]
        save_yolo_scene(folder, "sample", image, annotations, {"bolt": 0})
        label = (Path(folder) / "labels" / "sample.txt").read_text().strip()
        saved = np.asarray(Image.open(Path(folder) / "images" / "sample.png"))
        assert label == "0 0.100000 0.300000 0.100000 0.200000"
        assert saved.shape == image.shape and np.array_equal(saved, image)
    print("PASS: PNG and normalized YOLO label agree")


def check_opencv_baseline():
    image = np.full((120, 160, 3), 220, dtype=np.uint8)
    image[30:81, 40:91] = (20, 40, 60)
    boxes = detect_boxes(image)
    assert len(boxes) == 1 and score_boxes(boxes, [(40, 30, 91, 81)])["recall"] == 1
    result = score_boxes([(40, 30, 91, 81), (1, 1, 8, 8)], [(40, 30, 91, 81)])
    assert result == {"precision": 0.5, "recall": 1.0, "mean_iou": 1.0,
                      "tp": 1, "fp": 1, "fn": 0}
    print("PASS: OpenCV contrast localization and one-to-one box scoring")


if __name__ == "__main__":
    run()
    check_dataset_crops()
    check_background_contrast()
    check_yolo_save()
    check_opencv_baseline()
