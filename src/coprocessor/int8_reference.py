"""Bit-exact scalar primitives frozen by the C02 integer contract."""
import math

INT32_MIN, INT32_MAX = -(1 << 31), (1 << 31) - 1
INT64_MIN, INT64_MAX = -(1 << 63), (1 << 63) - 1

def _exact_int(value, name):
    if type(value) is not int:
        raise TypeError(f"{name} must be an int")
    return value


def _finite_float(value, name):
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be an int or float")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def round_float_away(value):
    """Round a finite scalar to nearest integer, with ties away from zero."""
    value = _finite_float(value, "value")
    magnitude = math.floor(abs(value) + 0.5)
    return -magnitude if value < 0 else magnitude


def round_shift(value, shift):
    """Divide by 2**shift, rounding nearest with ties away from zero."""
    value = _exact_int(value, "value")
    shift = _exact_int(shift, "shift")
    if not 0 <= shift <= 62:
        raise ValueError("shift must be in [0, 62]")
    if shift == 0:
        return value
    magnitude = -value if value < 0 else value
    rounded = (magnitude + (1 << (shift - 1))) >> shift
    return -rounded if value < 0 else rounded


def sat_i8_sym(value):
    """Saturate to the symmetric INT8 contract range [-127, 127]."""
    value = _exact_int(value, "value")
    return max(-127, min(127, value))


def quantize_i8_sym(value, scale):
    """Quantize a scalar with symmetric zero-point zero semantics."""
    value = _finite_float(value, "value")
    scale = _finite_float(scale, "scale")
    if scale <= 0:
        raise ValueError("scale must be positive")
    if value >= 127.5 * scale:
        return 127
    if value <= -127.5 * scale:
        return -127
    return sat_i8_sym(round_float_away(value / scale))


def quantize_bias(bias, input_scale, weight_scale):
    """Quantize one bias using S_bias = S_input * S_weight[channel]."""
    bias = _finite_float(bias, "bias")
    input_scale = _finite_float(input_scale, "input_scale")
    weight_scale = _finite_float(weight_scale, "weight_scale")
    divisor = input_scale * weight_scale
    if not math.isfinite(divisor) or divisor <= 0:
        raise ValueError("bias scale product must be finite and positive")
    quantized = round_float_away(bias / divisor)
    if not INT32_MIN <= quantized <= INT32_MAX:
        raise OverflowError("quantized bias does not fit signed INT32")
    return quantized


def encode_requant_scale(scale_ratio):
    """Choose the closest positive INT32 multiplier and shift in [0, 62]."""
    scale_ratio = _finite_float(scale_ratio, "scale_ratio")
    if scale_ratio <= 0:
        raise ValueError("scale_ratio must be positive")
    best = None
    for shift in range(63):
        scaled = math.ldexp(scale_ratio, shift)
        if scaled >= INT32_MAX + 0.5:
            break
        multiplier = round_float_away(scaled)
        if multiplier == 0:
            continue
        approximation = math.ldexp(float(multiplier), -shift)
        key = (abs(approximation - scale_ratio), -shift)
        if best is None or key < best[0]:
            best = (key, multiplier, shift)
    if best is None:
        raise ValueError("scale_ratio cannot be represented")
    return best[1], best[2]


def requantize_i8(acc, multiplier, shift):
    """Apply signed INT64 multiply, contract rounding, then INT8 saturation."""
    acc = _exact_int(acc, "acc")
    multiplier = _exact_int(multiplier, "multiplier")
    if not INT32_MIN <= acc <= INT32_MAX:
        raise ValueError("acc must fit signed INT32")
    if not 1 <= multiplier <= INT32_MAX:
        raise ValueError("multiplier must be positive signed INT32")
    product = acc * multiplier
    if not INT64_MIN <= product <= INT64_MAX:
        raise OverflowError("requant product does not fit signed INT64")
    return sat_i8_sym(round_shift(product, shift))
