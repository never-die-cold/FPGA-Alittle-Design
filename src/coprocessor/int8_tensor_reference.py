"""Strict NumPy tensor wrappers for the C02 scalar quantization rules."""
import numpy as np
from int8_reference import INT32_MAX, INT32_MIN, quantize_bias, quantize_i8_sym


def _float32_array(value, name):
    if (not isinstance(value, np.ndarray) or value.dtype != np.float32
            or value.size == 0 or not np.isfinite(value).all()):
        raise ValueError(f"{name} must be a nonempty finite float32 array")
    return value


def quantize_tensor(value, scale):
    """Per-tensor symmetric INT8 quantization in C element order."""
    value = _float32_array(value, "value")
    result = np.fromiter((quantize_i8_sym(float(item), scale) for item in value.flat),
                         dtype=np.int8, count=value.size)
    return result.reshape(value.shape)


def quantize_weights(weight, scales):
    """Quantize OIHW or OI weights with one scale per output channel."""
    weight = _float32_array(weight, "weight")
    scales = _float32_array(scales, "scales")
    if weight.ndim not in (2, 4) or scales.shape != (weight.shape[0],):
        raise ValueError("weight/scales shape mismatch")
    if np.any(scales <= 0):
        raise ValueError("weight scales must be positive")
    result = np.empty(weight.shape, dtype=np.int8)
    for channel in range(weight.shape[0]):
        result[channel] = quantize_tensor(weight[channel], float(scales[channel]))
    return result


def quantize_biases(bias, input_scale, weight_scales):
    """Quantize O biases with their per-output-channel weight scales."""
    bias = _float32_array(bias, "bias")
    weight_scales = _float32_array(weight_scales, "weight_scales")
    if bias.ndim != 1 or weight_scales.shape != bias.shape or np.any(weight_scales <= 0):
        raise ValueError("bias/weight_scales mismatch")
    return np.fromiter((quantize_bias(float(value), input_scale, float(weight_scales[index]))
                       for index, value in enumerate(bias)), dtype=np.int32, count=bias.size)


def _pair(value, name, minimum):
    if (not isinstance(value, (tuple, list)) or len(value) != 2
            or any(type(item) is not int or item < minimum for item in value)):
        raise ValueError(f"invalid {name}")
    return tuple(value)


def conv2d_accumulate(image, weight, bias, stride, padding):
    """CHW/OIHW cross-correlation with exact, checked INT32 accumulation."""
    if (not isinstance(image, np.ndarray) or image.dtype != np.int8 or image.ndim != 3
            or not isinstance(weight, np.ndarray) or weight.dtype != np.int8 or weight.ndim != 4
            or not isinstance(bias, np.ndarray) or bias.dtype != np.int32 or bias.ndim != 1):
        raise ValueError("invalid convolution tensors")
    if (image.size == 0 or weight.size == 0 or bias.shape != (weight.shape[0],)
            or image.shape[0] != weight.shape[1]):
        raise ValueError("convolution shape mismatch")
    stride, padding = _pair(stride, "stride", 1), _pair(padding, "padding", 0)
    _, height, width = image.shape
    outputs, _, kernel_h, kernel_w = weight.shape
    padded_h, padded_w = height + 2 * padding[0], width + 2 * padding[1]
    if kernel_h > padded_h or kernel_w > padded_w:
        raise ValueError("kernel exceeds padded input")
    output_h = (padded_h - kernel_h) // stride[0] + 1
    output_w = (padded_w - kernel_w) // stride[1] + 1
    result = np.empty((outputs, output_h, output_w), dtype=np.int32)
    for oc in range(outputs):
        for oy in range(output_h):
            for ox in range(output_w):
                acc = int(bias[oc])
                for ic in range(image.shape[0]):
                    for ky in range(kernel_h):
                        iy = oy * stride[0] + ky - padding[0]
                        for kx in range(kernel_w):
                            ix = ox * stride[1] + kx - padding[1]
                            if 0 <= iy < height and 0 <= ix < width:
                                acc += int(image[ic, iy, ix]) * int(weight[oc, ic, ky, kx])
                                if not INT32_MIN <= acc <= INT32_MAX:
                                    raise OverflowError("convolution accumulator overflow")
                result[oc, oy, ox] = acc
    return result
