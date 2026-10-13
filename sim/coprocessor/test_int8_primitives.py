"""Boundary tests for the C02 scalar integer semantics."""
import math

from int8_reference import (INT32_MAX, INT32_MIN, encode_requant_scale, quantize_bias,
                            quantize_i8_sym, requantize_i8, round_float_away,
                            round_shift, sat_i8_sym, gap_average256, classify_logits)


def expect_rejected(call, error):
    try:
        call()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def main():
    shifts = ((0, 0, 0), (4, 1, 2), (-4, 1, -2),
              (5, 1, 3), (-5, 1, -3),
              (1 << 61, 62, 1), (-(1 << 61), 62, -1))
    for value, shift, expected in shifts:
        assert round_shift(value, shift) == expected

    values = (-1000, -128, -127, 0, 127, 128, 1000)
    expected = (-127, -127, -127, 0, 127, 127, 127)
    assert tuple(sat_i8_sym(value) for value in values) == expected

    floats = (-2.5, -2.49, -0.5, 0.5, 2.49, 2.5)
    assert tuple(round_float_away(value) for value in floats) == (-3, -2, -1, 1, 2, 3)
    assert quantize_i8_sym(1.25, 0.5) == 3
    assert quantize_i8_sym(-1.25, 0.5) == -3
    assert quantize_i8_sym(1000.0, 0.5) == 127
    assert quantize_i8_sym(-1000.0, 0.5) == -127
    assert quantize_i8_sym(1.0, 1e-320) == 127
    assert quantize_i8_sym(-1.0, 1e-320) == -127
    assert quantize_bias(1.25, 0.5, 1.0) == 3
    assert quantize_bias(-1.25, 0.5, 1.0) == -3

    assert encode_requant_scale(1.0) == (1 << 30, 30)
    assert encode_requant_scale(0.5) == (1 << 30, 31)
    assert encode_requant_scale(2.0) == (1 << 30, 29)
    assert encode_requant_scale(math.ldexp(1.0, -63)) == (1, 62)
    third_multiplier, third_shift = encode_requant_scale(1.0 / 3.0)
    assert abs(math.ldexp(float(third_multiplier), -third_shift) - 1.0 / 3.0) \
        <= math.ldexp(0.5, -third_shift)
    multiplier, shift = encode_requant_scale(0.5)
    assert requantize_i8(5, multiplier, shift) == 3
    assert requantize_i8(-5, multiplier, shift) == -3

    assert requantize_i8(5, 1, 1) == 3
    assert requantize_i8(-5, 1, 1) == -3
    assert requantize_i8(INT32_MAX, INT32_MAX, 62) == 1
    assert requantize_i8(INT32_MIN, INT32_MAX, 62) == -1
    assert requantize_i8(INT32_MAX, INT32_MAX, 0) == 127
    assert requantize_i8(INT32_MIN, INT32_MAX, 0) == -127
    assert gap_average256(127) == 0 and gap_average256(128) == 1
    assert gap_average256(32512) == 127
    assert classify_logits([7, 7, 7], 1) == {"class_id": 0, "margin_q": 0,
        "score_q15": 0, "low_conf": True}
    assert classify_logits([-127, 127, -127], 254) == {"class_id": 1, "margin_q": 254,
        "score_q15": 32767, "low_conf": False}
    for call, error in ((lambda: gap_average256(32513), ValueError),
                        (lambda: gap_average256(True), TypeError),
                        (lambda: classify_logits([0, 0], 0), ValueError),
                        (lambda: classify_logits([-128, 0, 0], 0), ValueError),
                        (lambda: classify_logits([0, 0, True], 0), TypeError),
                        (lambda: classify_logits([0, 0, 0], 256), ValueError)):
        expect_rejected(call, error)

    invalid = ((lambda: round_shift(1, -1), ValueError),
               (lambda: round_shift(1, 63), ValueError),
               (lambda: round_shift(True, 1), TypeError),
               (lambda: round_float_away(float("nan")), ValueError),
               (lambda: quantize_i8_sym(1.0, 0.0), ValueError),
               (lambda: quantize_i8_sym(1.0, float("inf")), ValueError),
               (lambda: quantize_bias(True, 1.0, 1.0), TypeError),
               (lambda: quantize_bias(INT32_MAX + 1, 1.0, 1.0), OverflowError),
               (lambda: quantize_bias(1.0, 1e-300, 1e-300), ValueError),
               (lambda: encode_requant_scale(0.0), ValueError),
               (lambda: encode_requant_scale(-1.0), ValueError),
               (lambda: encode_requant_scale(float("nan")), ValueError),
               (lambda: encode_requant_scale(math.ldexp(1.0, -64)), ValueError),
               (lambda: encode_requant_scale(INT32_MAX + 1.0), ValueError),
               (lambda: requantize_i8(INT32_MAX + 1, 1, 0), ValueError),
               (lambda: requantize_i8(0, 0, 0), ValueError),
               (lambda: requantize_i8(0, INT32_MAX + 1, 0), ValueError))
    for call, error in invalid:
        expect_rejected(call, error)
    print("PASS: C02 scalar quantize/bias/scale-encode/requant/GAP/logit boundaries and invalid inputs")


if __name__ == "__main__":
    main()
