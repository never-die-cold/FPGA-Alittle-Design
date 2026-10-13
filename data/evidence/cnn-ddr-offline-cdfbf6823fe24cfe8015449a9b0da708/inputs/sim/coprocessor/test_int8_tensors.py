"""Tensor shape, channel-scale and rejection tests for C02 quantization."""
import numpy as np
from int8_tensor_reference import quantize_biases, quantize_tensor, quantize_weights


def expect_rejected(call):
    try:
        call()
    except (TypeError, ValueError, OverflowError):
        return
    raise AssertionError("invalid tensor input accepted")


def main():
    values = np.array([[-1000.0, -1.25, 0.0, 1.25, 1000.0]], np.float32)
    original = values.copy()
    actual = quantize_tensor(values, 0.5)
    expected = np.array([[-127, -3, 0, 3, 127]], np.int8)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(values, original)
    assert actual.flags.c_contiguous

    weights = np.array([[[[-1.0, 0.5]]], [[[1.0, 0.5]]]], np.float32)
    scales = np.array([0.5, 0.25], np.float32)
    expected_weights = np.array([[[[-2, 1]]], [[[4, 2]]]], np.int8)
    np.testing.assert_array_equal(quantize_weights(weights, scales), expected_weights)
    biases = np.array([1.25, -1.25], np.float32)
    np.testing.assert_array_equal(quantize_biases(biases, 0.5, scales),
                                  np.array([5, -10], np.int32))

    invalid = (lambda: quantize_tensor(values.astype(np.float64), 0.5),
               lambda: quantize_tensor(np.array([np.nan], np.float32), 0.5),
               lambda: quantize_weights(weights, np.array([0.5], np.float32)),
               lambda: quantize_weights(weights, np.array([0.5, 0.0], np.float32)),
               lambda: quantize_weights(weights.reshape(2, 1, 2), scales),
               lambda: quantize_biases(biases, 0.5, np.array([0.5], np.float32)))
    for call in invalid:
        expect_rejected(call)
    print("PASS: C02 tensor/per-channel quantization values, layouts and rejection gates")


if __name__ == "__main__":
    main()
