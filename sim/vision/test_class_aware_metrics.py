"""Regression cases for fixed-IoU class matching and shared preprocessing."""
import unittest
import numpy as np
from evaluate_class_aware import count_matches
from evaluate_fastener_classifier import crop_tensor
from train_scene_classifier import preprocess


class MetricsTests(unittest.TestCase):
    def test_wrong_class_cannot_consume_correct_match(self):
        truth = [(0, (0, 0, 10, 10))]
        predictions = [(1, (0, 0, 10, 10)), (0, (1, 0, 10, 10))]
        self.assertEqual(count_matches(predictions, truth, 3)[:3], (1, 1, 0))

    def test_duplicate_and_rejection(self):
        truth = [(0, (0, 0, 10, 10))]
        self.assertEqual(count_matches(truth * 2, truth, 3)[:3], (1, 1, 0))
        self.assertEqual(count_matches([(3, truth[0][1])], truth, 3)[:3], (0, 1, 1))
        self.assertEqual(count_matches([], [], 3)[:3], (0, 0, 0))

    def test_training_and_inference_preprocess_identical(self):
        image = np.random.default_rng(42).integers(0, 256, (80, 90, 3), dtype=np.uint8)
        for size in [64, 96]:
            for mode in ['opposite', 'border']:
                canvas, _ = preprocess(image, (3, 8, 65, 72), size, mode)
                np.testing.assert_array_equal(crop_tensor(image, (3, 8, 65, 72), size, mode).numpy()[0],
                                              canvas.astype(np.float32) / 255)


if __name__ == '__main__':
    unittest.main()
