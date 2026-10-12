"""Strict NumPy tensor wrappers for the C02 scalar quantization rules."""
import numpy as np
from int8_reference import (INT32_MAX, INT32_MIN, quantize_bias, quantize_i8_sym,
                            requantize_i8, round_shift, sat_i8_sym)


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


def requantize_channels(accumulators, multipliers, shifts, relu):
    """Apply optional INT32 ReLU and per-output-channel requantization."""
    if (not isinstance(accumulators, np.ndarray) or accumulators.dtype != np.int32
            or accumulators.ndim not in (1, 3) or accumulators.size == 0
            or not isinstance(multipliers, np.ndarray) or multipliers.dtype != np.int32
            or not isinstance(shifts, np.ndarray) or shifts.dtype != np.uint8
            or type(relu) is not bool):
        raise ValueError("invalid requant tensors")
    channels = accumulators.shape[0]
    if (multipliers.shape != (channels,) or shifts.shape != (channels,)
            or np.any(multipliers <= 0) or np.any(shifts > 62)):
        raise ValueError("requant channel parameters mismatch")
    result = np.empty(accumulators.shape, dtype=np.int8)
    for index in np.ndindex(accumulators.shape):
        value = int(accumulators[index])
        if relu and value < 0:
            value = 0
        result[index] = requantize_i8(value, int(multipliers[index[0]]),
                                      int(shifts[index[0]]))
    return result


def conv_relu_requant(image, weight, bias, stride, padding, multipliers, shifts):
    """Compose checked Conv+bias accumulation, INT32 ReLU and requantization."""
    accumulators = conv2d_accumulate(image, weight, bias, stride, padding)
    return requantize_channels(accumulators, multipliers, shifts, True)


def gap_16x16(activation):
    """Average each nonnegative Cx16x16 INT8 channel with contract rounding."""
    if (not isinstance(activation, np.ndarray) or activation.dtype != np.int8
            or activation.ndim != 3 or activation.shape[0] == 0
            or activation.shape[1:] != (16, 16) or np.any(activation < 0)):
        raise ValueError("GAP requires nonnegative Cx16x16 INT8")
    result = np.empty((activation.shape[0],), dtype=np.int8)
    for channel in range(activation.shape[0]):
        total = 0
        for value in activation[channel].flat:
            total += int(value)
            if not INT32_MIN <= total <= INT32_MAX:
                raise OverflowError("GAP accumulator overflow")
        result[channel] = sat_i8_sym(round_shift(total, 8))
    return result


def linear_accumulate(vector, weight, bias):
    """OI INT8 linear layer with checked INT32 bias and accumulation."""
    if (not isinstance(vector, np.ndarray) or vector.dtype != np.int8 or vector.ndim != 1
            or not isinstance(weight, np.ndarray) or weight.dtype != np.int8 or weight.ndim != 2
            or not isinstance(bias, np.ndarray) or bias.dtype != np.int32 or bias.ndim != 1
            or vector.size == 0 or weight.size == 0 or weight.shape[1] != vector.size
            or bias.shape != (weight.shape[0],)):
        raise ValueError("invalid linear tensors")
    result = np.empty((weight.shape[0],), dtype=np.int32)
    for output in range(weight.shape[0]):
        acc = int(bias[output])
        for index in range(vector.size):
            acc += int(vector[index]) * int(weight[output, index])
            if not INT32_MIN <= acc <= INT32_MAX:
                raise OverflowError("linear accumulator overflow")
        result[output] = acc
    return result


def linear_requant(vector, weight, bias, multipliers, shifts):
    """Complete FC+bias+requant path; logits deliberately have no ReLU."""
    return requantize_channels(linear_accumulate(vector, weight, bias),
                               multipliers, shifts, False)
