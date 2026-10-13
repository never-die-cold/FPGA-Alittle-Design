"""Per-channel post-processing and complete integer Conv layer tests."""
import numpy as np
from int8_reference import encode_requant_scale
from int8_tensor_reference import conv_relu_requant, requantize_channels


def expect_rejected(call):
    try:
        call()
    except (TypeError, ValueError):
        return
    raise AssertionError("invalid requant input accepted")


def main():
    half, half_shift = encode_requant_scale(0.5)
    quarter, quarter_shift = encode_requant_scale(0.25)
    accumulators = np.array([[[-5, 5, 255]], [[-5, 5, 255]]], np.int32)
    multipliers = np.array([half, quarter], np.int32)
    shifts = np.array([half_shift, quarter_shift], np.uint8)
    expected = np.array([[[0, 3, 127]], [[0, 1, 64]]], np.int8)
    np.testing.assert_array_equal(requantize_channels(accumulators, multipliers, shifts, True),
                                  expected)
    no_relu = requantize_channels(accumulators[:, :, :2], multipliers, shifts, False)
    np.testing.assert_array_equal(no_relu, np.array([[[-3, 3]], [[-1, 1]]], np.int8))

    image = np.array([[[-1, 2], [3, 4]]], np.int8)
    weight = np.array([[[[1, -1], [2, 1]]]], np.int8)
    actual = conv_relu_requant(image, weight, np.array([-2], np.int32), [1, 1], [0, 0],
                               np.array([half], np.int32), np.array([half_shift], np.uint8))
    np.testing.assert_array_equal(actual, np.array([[[3]]], np.int8))

    invalid = (lambda: requantize_channels(accumulators.astype(np.int64), multipliers, shifts, True),
               lambda: requantize_channels(accumulators, multipliers[:1], shifts, True),
               lambda: requantize_channels(accumulators, np.array([half, 0], np.int32), shifts, True),
               lambda: requantize_channels(accumulators, multipliers,
                                            np.array([half_shift, 63], np.uint8), True),
               lambda: requantize_channels(accumulators, multipliers, shifts, 1))
    for call in invalid:
        expect_rejected(call)
    print("PASS: per-channel ReLU/requant and complete Conv layer integer output")


if __name__ == "__main__":
    main()
