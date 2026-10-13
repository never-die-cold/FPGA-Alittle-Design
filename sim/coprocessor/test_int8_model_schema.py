"""Positive and mutation tests for the frozen FastenerCNN integer schema."""
import numpy as np
from int8_model_reference import validate_fastener_layers

SPECS = (("conv1", (16, 1, 3, 3), [2, 2]),
         ("conv2", (32, 16, 3, 3), [1, 1]),
         ("conv3", (32, 32, 3, 3), [2, 2]),
         ("conv4", (64, 32, 3, 3), [1, 1]))


def make_layers():
    layers = []
    for name, shape, stride in SPECS:
        outputs = shape[0]
        layers.append({"name": name, "weight": np.zeros(shape, np.int8),
                       "bias": np.zeros(outputs, np.int32), "stride": stride,
                       "padding": [1, 1], "multipliers": np.ones(outputs, np.int32),
                       "shifts": np.zeros(outputs, np.uint8)})
    layers.append({"name": "logits", "weight": np.zeros((3, 64), np.int8),
                   "bias": np.zeros(3, np.int32), "multipliers": np.ones(3, np.int32),
                   "shifts": np.zeros(3, np.uint8)})
    return layers


def reject(layers):
    try:
        validate_fastener_layers(layers)
    except ValueError:
        return
    raise AssertionError("invalid FastenerCNN schema accepted")


def main():
    validate_fastener_layers(make_layers())
    bad = make_layers(); bad[0], bad[1] = bad[1], bad[0]; reject(bad)
    bad = make_layers(); bad[0]["weight"] = np.zeros((16, 1, 1, 1), np.int8); reject(bad)
    bad = make_layers(); bad[1]["weight"] = bad[1]["weight"].astype(np.int16); reject(bad)
    bad = make_layers(); bad[2]["stride"] = [1, 1]; reject(bad)
    bad = make_layers(); bad[3]["bias"] = np.zeros(63, np.int32); reject(bad)
    bad = make_layers(); bad[4]["multipliers"][0] = 0; reject(bad)
    bad = make_layers(); bad[0]["shifts"][0] = 63; reject(bad)
    bad = make_layers(); bad[4]["unknown"] = 1; reject(bad)
    print("PASS: frozen FastenerCNN layer order, shapes, dtypes and channel parameters")


if __name__ == "__main__":
    main()
