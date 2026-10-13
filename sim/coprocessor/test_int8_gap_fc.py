"""GAP half-rounding and signed fully-connected output tests."""
import numpy as np
from int8_reference import INT32_MAX, encode_requant_scale
from int8_tensor_reference import gap_16x16, linear_accumulate, linear_requant


def expect_rejected(call, error=ValueError):
    try:
        call()
    except error:
        return
    raise AssertionError("invalid GAP/FC input accepted")


def main():
    activation = np.zeros((3, 16, 16), np.int8)
    activation[0].flat[:2] = (127, 1)
    activation[1].flat[:4] = (127, 127, 127, 3)
    activation[2].fill(127)
    np.testing.assert_array_equal(gap_16x16(activation), np.array([1, 2, 127], np.int8))

    vector = np.array([-2, 3], np.int8)
    weight = np.array([[4, -5], [-1, 2], [127, 127]], np.int8)
    bias = np.array([3, -3, 0], np.int32)
    np.testing.assert_array_equal(linear_accumulate(vector, weight, bias),
                                  np.array([-20, 5, 127], np.int32))
    multiplier, shift = encode_requant_scale(0.5)
    multipliers = np.full((3,), multiplier, np.int32)
    shifts = np.full((3,), shift, np.uint8)
    np.testing.assert_array_equal(linear_requant(vector, weight, bias, multipliers, shifts),
                                  np.array([-10, 3, 64], np.int8))

    negative = np.zeros((1, 16, 16), np.int8)
    negative[0, 0, 0] = -1
    invalid = (lambda: gap_16x16(np.zeros((1, 15, 16), np.int8)),
               lambda: gap_16x16(negative),
               lambda: gap_16x16(activation.astype(np.int16)),
               lambda: linear_accumulate(vector.reshape(1, 2), weight, bias),
               lambda: linear_accumulate(vector, np.empty((0, 2), np.int8), np.empty((0,), np.int32)),
               lambda: linear_accumulate(vector, weight[:, :1], bias),
               lambda: linear_accumulate(vector, weight, bias[:2]))
    for call in invalid:
        expect_rejected(call)
    expect_rejected(lambda: linear_accumulate(np.array([127], np.int8),
                    np.array([[127]], np.int8), np.array([INT32_MAX], np.int32)), OverflowError)
    print("PASS: GAP rounding and signed FC accumulation/requantization")


if __name__ == "__main__":
    main()
