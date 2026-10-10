"""Independent NumPy FP32 cross-correlation/ReLU/GAP/linear reference."""
import numpy as np

RTOL, ATOL = 2e-5, 1e-4


def conv2d(image, weight, bias, stride, padding):
    if (image.ndim != 3 or weight.ndim != 4 or image.shape[0] != weight.shape[1]
            or bias.shape != (weight.shape[0],) or len(stride) != 2 or len(padding) != 2
            or any(type(value) is not int or value < 1 for value in stride)
            or any(type(value) is not int or value < 0 for value in padding)
            or any(value.dtype != np.float32 or not np.isfinite(value).all() for value in (image, weight, bias))):
        raise ValueError("invalid FP32 convolution inputs")
    kh, kw = weight.shape[2:]
    padded = np.pad(image, ((0, 0), (padding[0], padding[0]), (padding[1], padding[1])))
    if kh < 1 or kw < 1 or kh > padded.shape[1] or kw > padded.shape[2]:
        raise ValueError("invalid kernel extent")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (kh, kw), axis=(1, 2))
    windows = windows[:, ::stride[0], ::stride[1]]
    output = np.einsum("cyxij,ocij->oyx", windows, weight, optimize=True)
    return output + bias[:, None, None]


def reference_trace(crop, layers):
    if not isinstance(crop, np.ndarray) or crop.dtype != np.uint8 or crop.shape != (64, 64):
        raise ValueError("reference requires uint8 64x64 input")
    if [layer["kind"] for layer in layers] != ["conv_relu"] * 4 + ["global_average", "linear"]:
        raise ValueError("unsupported reference operator sequence")
    value = crop.astype(np.float32)[None] / np.float32(255)
    trace = {"input": value.copy()}
    for layer in layers:
        if layer["kind"] == "conv_relu":
            value = np.maximum(conv2d(value, layer["weight"], layer["bias"],
                                     layer["stride"], layer["padding"]), np.float32(0))
        elif layer["kind"] == "global_average":
            value = value.mean(axis=(1, 2), dtype=np.float32)
        else:
            value = layer["weight"] @ value + layer["bias"]
        if not np.isfinite(value).all():
            raise ValueError("nonfinite reference activation")
        trace[layer["name"]] = value.copy()
    return trace
