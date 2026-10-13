"""Hand-computed addressing, padding and overflow tests for integer Conv2d."""
import numpy as np
from int8_reference import INT32_MAX
from int8_tensor_reference import conv2d_accumulate


def expect_rejected(call, error=ValueError):
    try:
        call()
    except error:
        return
    raise AssertionError("invalid convolution accepted")


def main():
    image = np.array([[[-1, 2, 3], [4, -5, 6]],
                      [[1, 0, -1], [2, 3, 4]]], np.int8)
    weight = np.array([[[[1, -2], [3, 4]],
                        [[-1, 2], [0, -3]]]], np.int8)
    actual = conv2d_accumulate(image, weight, np.array([-3], np.int32), [1, 1], [0, 0])
    np.testing.assert_array_equal(actual, np.array([[[-26, -12]]], np.int32))

    unit_weight = np.array([[[[2]]]], np.int8)
    padded = conv2d_accumulate(image[:1], unit_weight, np.array([1], np.int32),
                               [2, 2], [1, 1])
    np.testing.assert_array_equal(padded, np.array([[[1, 1, 1], [1, -9, 1]]], np.int32))
    assert actual.flags.c_contiguous

    invalid = (lambda: conv2d_accumulate(image.astype(np.int16), weight,
                                          np.array([-3], np.int32), [1, 1], [0, 0]),
               lambda: conv2d_accumulate(image, weight[:, :1], np.array([-3], np.int32),
                                          [1, 1], [0, 0]),
               lambda: conv2d_accumulate(image, weight, np.array([-3, 0], np.int32),
                                          [1, 1], [0, 0]),
               lambda: conv2d_accumulate(image, weight, np.array([-3], np.int32),
                                          [0, 1], [0, 0]),
               lambda: conv2d_accumulate(image, np.ones((1, 2, 5, 5), np.int8),
                                          np.array([0], np.int32), [1, 1], [0, 0]))
    for call in invalid:
        expect_rejected(call)
    expect_rejected(lambda: conv2d_accumulate(np.array([[[127]]], np.int8),
                    np.array([[[[127]]]], np.int8), np.array([INT32_MAX], np.int32),
                    [1, 1], [0, 0]), OverflowError)
    print("PASS: INT8 Conv2d addressing, bias, padding, stride and INT32 overflow gate")


if __name__ == "__main__":
    main()
