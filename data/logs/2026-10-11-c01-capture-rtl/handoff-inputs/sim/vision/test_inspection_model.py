"""Real prototype load/infer repeatability; missing metadata must be rejected."""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_model import PrototypeClassifier


def main():
    model = PrototypeClassifier(ROOT / "models/cnn-border-fill-best.pt")
    crops = [np.full((64, 64), value, np.uint8) for value in (0, 127, 255)]
    first = model.predict(crops)
    assert first == model.predict(crops) and model.predict([]) == []
    for row in first:
        assert row["class"] in ("bolt", "nut", "washer")
        assert 0 <= row["score"] <= 1 and abs(sum(row["probabilities"]) - 1) < 1e-6
    try:
        PrototypeClassifier(ROOT / "models/cnn-bn64-baseline.pt")
    except ValueError:
        pass
    else:
        raise AssertionError("metadata-free model accepted")
    for crop in (np.zeros((63, 64), np.uint8), np.zeros((64, 64), np.float32)):
        try:
            model.predict([crop])
        except ValueError:
            continue
        raise AssertionError("invalid model input accepted")
    print("PASS: FP32 prototype load/repeatable inference and model/input rejection")


if __name__ == "__main__":
    main()
