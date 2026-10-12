"""Frozen FastenerCNN integer parameter schema for the J02 executor."""
import numpy as np
from int8_result_reference import summarize_logits
from int8_tensor_reference import conv_relu_requant, gap_16x16, linear_requant

CONV_SPECS = (("conv1", (16, 1, 3, 3), (2, 2)),
              ("conv2", (32, 16, 3, 3), (1, 1)),
              ("conv3", (32, 32, 3, 3), (2, 2)),
              ("conv4", (64, 32, 3, 3), (1, 1)))
CONV_KEYS = {"name", "weight", "bias", "stride", "padding", "multipliers", "shifts"}
LINEAR_KEYS = {"name", "weight", "bias", "multipliers", "shifts"}


def _vectors_valid(layer, outputs):
    return (isinstance(layer["bias"], np.ndarray) and layer["bias"].dtype == np.int32
            and layer["bias"].shape == (outputs,)
            and isinstance(layer["multipliers"], np.ndarray)
            and layer["multipliers"].dtype == np.int32
            and layer["multipliers"].shape == (outputs,)
            and np.all(layer["multipliers"] > 0)
            and isinstance(layer["shifts"], np.ndarray) and layer["shifts"].dtype == np.uint8
            and layer["shifts"].shape == (outputs,) and np.all(layer["shifts"] <= 62))


def validate_fastener_layers(layers):
    """Reject parameters that do not exactly match the frozen five-layer network."""
    if not isinstance(layers, (list, tuple)) or len(layers) != 5:
        raise ValueError("FastenerCNN requires five parameter layers")
    for layer, (name, shape, stride) in zip(layers[:4], CONV_SPECS):
        if not isinstance(layer, dict) or set(layer) != CONV_KEYS or layer["name"] != name:
            raise ValueError("invalid convolution layer schema")
        if (not isinstance(layer["weight"], np.ndarray) or layer["weight"].dtype != np.int8
                or layer["weight"].shape != shape or not _vectors_valid(layer, shape[0])):
            raise ValueError("invalid convolution parameters")
        if (not isinstance(layer["stride"], (list, tuple)) or tuple(layer["stride"]) != stride
                or not isinstance(layer["padding"], (list, tuple))
                or tuple(layer["padding"]) != (1, 1)):
            raise ValueError("invalid convolution geometry")
    linear = layers[4]
    if (not isinstance(linear, dict) or set(linear) != LINEAR_KEYS
            or linear["name"] != "logits" or not isinstance(linear["weight"], np.ndarray)
            or linear["weight"].dtype != np.int8 or linear["weight"].shape != (3, 64)
            or not _vectors_valid(linear, 3)):
        raise ValueError("invalid linear layer schema")


def run_fastener_cnn(image, layers, min_margin_q):
    """Execute the frozen integer network and return independent layer traces."""
    if (not isinstance(image, np.ndarray) or image.dtype != np.int8
            or image.shape != (64, 64)):
        raise ValueError("image must be INT8 shape [64, 64]")
    if type(min_margin_q) is not int or not 0 <= min_margin_q <= 254:
        raise ValueError("min_margin_q must be an integer in [0, 254]")
    validate_fastener_layers(layers)
    current = np.array(image, dtype=np.int8, order="C", copy=True).reshape(1, 64, 64)
    trace = {"input": current.copy(order="C")}
    expected_shapes = ((16, 32, 32), (32, 32, 32),
                       (32, 16, 16), (64, 16, 16))
    for layer, expected_shape in zip(layers[:4], expected_shapes):
        current = conv_relu_requant(current, layer["weight"], layer["bias"],
                                    layer["stride"], layer["padding"],
                                    layer["multipliers"], layer["shifts"])
        if current.shape != expected_shape:
            raise RuntimeError("unexpected convolution output shape")
        trace[layer["name"]] = current.copy(order="C")
    pooled = gap_16x16(current)
    logits_layer = layers[4]
    logits = linear_requant(pooled, logits_layer["weight"], logits_layer["bias"],
                            logits_layer["multipliers"], logits_layer["shifts"])
    trace["gap"] = pooled.copy(order="C")
    trace["logits"] = logits.copy(order="C")
    trace["result"] = dict(summarize_logits(logits, min_margin_q))
    return trace
