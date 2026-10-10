"""BN folding is equivalent to the received model, including trained offsets."""
import sys
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_model import PrototypeClassifier
from model_reference import folded_layers


def main():
    torch.set_num_threads(4)
    model = PrototypeClassifier(ROOT / "models/cnn-border-fill-best.pt").model
    layers = folded_layers(model)
    inputs = torch.from_numpy(np.random.default_rng(2026).random((3, 1, 64, 64), dtype=np.float32))
    with torch.inference_mode():
        expected = model(inputs)
        actual = inputs
        for layer in layers:
            if layer["kind"] == "conv_relu":
                actual = F.conv2d(actual, torch.from_numpy(layer["weight"]), torch.from_numpy(layer["bias"]),
                                  stride=layer["stride"], padding=layer["padding"]).relu()
            elif layer["kind"] == "global_average":
                actual = actual.mean(dim=(2, 3))
            else:
                actual = F.linear(actual, torch.from_numpy(layer["weight"]), torch.from_numpy(layer["bias"]))
        error = float((actual - expected).abs().max())
        torch.testing.assert_close(actual, expected, rtol=2e-5, atol=2e-5)
        assert torch.equal(actual.argmax(1), expected.argmax(1))
    assert all(layer["weight"].dtype == np.float32 for layer in layers if "weight" in layer)
    model.train()
    try:
        folded_layers(model)
    except ValueError:
        pass
    else:
        raise AssertionError("training-mode BN accepted")
    print(f"PASS: four BN folds and logits parity; max_abs_error={error:.9g}; training mode rejected")


if __name__ == "__main__":
    main()
