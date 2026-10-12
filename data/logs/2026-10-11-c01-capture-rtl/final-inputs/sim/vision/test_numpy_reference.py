"""Independent convolution indexing and all model stages against PyTorch."""
import sys
from pathlib import Path
import numpy as np
import torch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_model import PrototypeClassifier
from model_reference import folded_layers
from numpy_reference import conv2d, reference_trace, RTOL, ATOL


def folded_double_trace(crop, layers):
    value = torch.from_numpy(crop.astype(np.float32)[None, None] / 255).double()
    trace = {}
    with torch.inference_mode():
        for layer in layers:
            if layer["kind"] == "conv_relu":
                value = torch.nn.functional.conv2d(value, torch.from_numpy(layer["weight"]).double(),
                    torch.from_numpy(layer["bias"]).double(), stride=layer["stride"], padding=layer["padding"]).relu()
            elif layer["kind"] == "global_average":
                value = value.mean(dim=(2, 3))
            else:
                value = torch.nn.functional.linear(value, torch.from_numpy(layer["weight"]).double(),
                                                  torch.from_numpy(layer["bias"]).double())
            trace[layer["name"]] = value[0].numpy().copy()
    return trace


def main():
    torch.set_num_threads(4)
    image = np.arange(40, dtype=np.float32).reshape(2, 4, 5)
    weight = np.arange(18, dtype=np.float32).reshape(1, 2, 3, 3) / 10
    actual = conv2d(image, weight, np.array([1], np.float32), [2, 2], [1, 1])
    padded = np.pad(image, ((0, 0), (1, 1), (1, 1)))
    expected = np.array([[[1 + np.sum(padded[:, y:y + 3, x:x + 3] * weight[0])
                           for x in (0, 2, 4)] for y in (0, 2)]], np.float32)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-5)
    model = PrototypeClassifier(ROOT / "models/cnn-border-fill-best.pt").model
    layers = folded_layers(model)
    crops = [np.full((64, 64), level, np.uint8) for level in (0, 127, 255)]
    crops += [np.random.default_rng(2026).integers(0, 256, (64, 64), dtype=np.uint8),
              np.pad(np.full((1, 1), 255, np.uint8), ((0, 63), (0, 63))),
              np.tile(np.array([0, 255], np.uint8), (64, 32))]
    torch_trace = {}
    value = torch.from_numpy(np.stack(crops).astype(np.float32)[:, None] / 255)
    with torch.inference_mode():
        for index, module in enumerate(model.features):
            value = module(value)
            if index in (2, 5, 8, 11, 13, 14):
                name = {2: "conv1", 5: "conv2", 8: "conv3", 11: "conv4", 13: "gap", 14: "logits"}[index]
                torch_trace[name] = value.numpy().copy()
    maximum, double_maximum, violations = 0.0, 0.0, []
    for number, crop in enumerate(crops):
        trace = reference_trace(crop, layers)
        double = folded_double_trace(crop, layers)
        for name, expected in torch_trace.items():
            original_error = float(np.max(np.abs(trace[name] - expected[number])))
            double_error = float(np.max(np.abs(trace[name] - double[name])))
            print(f"sample={number} stage={name} original_error={original_error:.9g} folded_fp64_error={double_error:.9g}")
            maximum, double_maximum = max(maximum, original_error), max(double_maximum, double_error)
            np.testing.assert_allclose(trace[name], double[name], rtol=RTOL, atol=ATOL)
            if not np.allclose(trace[name], expected[number], rtol=RTOL, atol=ATOL):
                violations.append((number, name))
        assert trace["logits"].argmax() == torch_trace["logits"][number].argmax()
    assert not violations, f"FP32 tolerance failures: {violations}; original={maximum}; double={double_maximum}"
    for invalid in ((image.astype(np.float64), weight, np.array([1], np.float32), [2, 2], [1, 1]),
                    (image, weight, np.array([1], np.float32), [0, 2], [1, 1])):
        try:
            conv2d(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid convolution accepted")
    print(f"PASS: convolution indexing and six inputs x six stages; max_abs_error={maximum:.9g}; rtol={RTOL} atol={ATOL}")


if __name__ == "__main__":
    main()
