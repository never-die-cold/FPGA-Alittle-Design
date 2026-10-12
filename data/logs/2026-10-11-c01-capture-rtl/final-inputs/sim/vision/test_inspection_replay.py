"""File replay pipeline, exact crops, restart-safe reuse and conflicting requests."""
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_run import run
from inspection_replay import inspect_frame
from roi_preprocess import preprocess


class StubClassifier:
    metadata = {"name": "TEST STUB ONLY"}

    def predict(self, crops):
        return [{"class": "bolt", "score": 0.9} for _ in crops]


def main():
    frame = np.full((120, 240, 3), 220, np.uint8)
    frame[40:75, 30:55] = 40
    frame[45:80, 150:185] = (50, 80, 60)
    order = {"bolt": 2, "nut": 0, "washer": 0}
    result, crops = inspect_frame(frame, StubClassifier(), order, 0.8)
    assert result["target_count"] == 2 and result["decision"]["verdict"] == "CHECK_PASS"
    assert result["mode"] == "FILE_REPLAY" and not result["hardware_connected"]
    assert len(crops) == 2 and result["targets"][0]["bbox"] == [30, 40, 55, 75]
    empty, _ = inspect_frame(np.full_like(frame, 220), StubClassifier(), order, 0.8)
    assert empty["decision"]["verdict"] == "CHECK_FAIL" and empty["target_count"] == 0
    limited, limited_crops = inspect_frame(frame, StubClassifier(), {**order, "bolt": 1}, .8, 1)
    assert limited["decision"]["verdict"] == "RECHECK" and limited_crops == []
    assert limited["decision"]["actual"] is None and limited["target_count"] == 2
    border = np.full_like(frame, 220)
    border[40:75, 0:25] = 40
    checked, _ = inspect_frame(border, StubClassifier(), {**order, "bolt": 1}, .8)
    assert checked["decision"]["verdict"] == "RECHECK" and checked["targets"][0]["touches_border"]
    build = ROOT / "sim/build/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as directory:
        folder = Path(directory)
        source = folder / "input.png"
        assert cv2.imwrite(str(source), frame)
        weights = ROOT / "models/cnn-border-fill-best.pt"
        real_order = {"bolt": 1, "nut": 1, "washer": 0}
        first = run(source, weights, real_order, folder / "out", "request-1", 0.0)
        assert first["target_count"] == 2 and first["model"]["precision"] == "FP32"
        assert first == run(source, weights, real_order, folder / "out", "request-1", 0.0)
        assert len(list((folder / "out").iterdir())) == 1
        for target in first["targets"]:
            pixels = cv2.imread(str(folder / "out/request-1" / target["roi_path"]), cv2.IMREAD_GRAYSCALE)
            assert np.array_equal(pixels, preprocess(frame, target["bbox"])[0])
        try:
            run(source, weights, real_order, folder / "out", "request-1", 0.99)
        except ValueError:
            pass
        else:
            raise AssertionError("changed request parameters reused old result")
        (folder / "out/request-1/source.bin").write_bytes(b"tampered")
        try:
            run(source, weights, real_order, folder / "out", "request-1", 0.0)
        except ValueError:
            pass
        else:
            raise AssertionError("tampered replay reused")
        source.write_bytes(b"not an image")
        try:
            run(source, weights, real_order, folder / "out", "invalid-image", 0.0)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid image accepted")
        assert not (folder / "out/invalid-image").exists()
    print("PASS: replay detection/ROI/rules, real FP32 inference, persistent reuse and error gates")


if __name__ == "__main__":
    main()
