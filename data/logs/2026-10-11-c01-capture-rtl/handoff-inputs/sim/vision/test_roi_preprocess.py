"""Pixel parity with the received training implementation, plus invalid inputs."""
import sys
import ast
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from roi_preprocess import preprocess

snapshot = ROOT / "sim/vision/archive/fastener-vision-2026-10-07/train_scene_classifier.py"
source = ast.parse(snapshot.read_text(encoding="utf-8"))
function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "preprocess")
namespace = {"cv2": cv2, "np": np}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(snapshot), "exec"), namespace)
training_preprocess = namespace["preprocess"]


def main():
    image = np.random.default_rng(2026).integers(0, 256, (85, 101, 3), dtype=np.uint8)
    boxes = [(0, 0, 101, 85), (2, 3, 86, 8), (0, 0, 1, 1),
             (3, 2, 8, 81), (7, 9, 12, 16), (97, 80, 101, 85)]
    for size in (64, 96):
        for mode in ("border", "opposite"):
            for box in boxes:
                actual, level = preprocess(image, box, size, mode)
                expected, expected_level = training_preprocess(image, box, size, mode)
                assert actual.dtype == np.uint8 and actual.shape == (size, size)
                assert level == expected_level and np.array_equal(actual, expected)
    for bgr, gray in (((255, 0, 0), 29), ((0, 255, 0), 150), ((0, 0, 255), 76)):
        pixels, level = preprocess(np.array([[bgr]], dtype=np.uint8), (0, 0, 1, 1))
        assert level == gray and np.all(pixels == gray)
    bad = [(image, box, 64, "border") for box in
           ((0, 0, 0, 1), (-1, 0, 1, 1), (0, 0, 102, 1), (0, 0, True, 1))]
    bad += [(None, (0, 0, 1, 1), 64, "border"),
            (image.astype(np.float32), (0, 0, 1, 1), 64, "border"),
            (image, (0, 0, 1, 1), 32, "border"), (image, (0, 0, 1, 1), 64, "bad")]
    for args in bad:
        try:
            preprocess(*args)
        except ValueError:
            continue
        raise AssertionError("invalid preprocessing input accepted")
    print("PASS: ROI 24 training parity cases, BGR channels and 8 invalid inputs")


if __name__ == "__main__":
    main()
