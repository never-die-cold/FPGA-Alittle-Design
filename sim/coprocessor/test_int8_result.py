"""Tie, extreme score and low-confidence tests for final INT8 logits."""
import numpy as np
from int8_result_reference import summarize_logits


def expect_rejected(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("invalid result input accepted")


def main():
    for logits, expected_class in (([9, 3, 1], 0), ([0, 9, 1], 1), ([0, 1, 9], 2),
                                   ([-3, -1, -2], 1)):
        assert summarize_logits(np.array(logits, np.int8), 0)["class_id"] == expected_class

    tie01 = summarize_logits(np.array([7, 7, 1], np.int8), 1)
    assert tie01 == {"class_id": 0, "margin_q": 0, "score_q15": 0, "low_conf": True}
    tie12 = summarize_logits(np.array([0, 5, 5], np.int8), 0)
    assert tie12["class_id"] == 1 and tie12["margin_q"] == 0
    assert summarize_logits(np.array([4, 4, 4], np.int8), 0)["class_id"] == 0

    middle = summarize_logits(np.array([127, 0, -127], np.int8), 0)
    assert middle["margin_q"] == 127 and middle["score_q15"] == 16384
    maximum = summarize_logits(np.array([127, -127, -127], np.int8), 254)
    assert maximum["margin_q"] == 254 and maximum["score_q15"] == 32767
    assert maximum["low_conf"] is False
    assert summarize_logits(np.array([10, 5, 0], np.int8), 5)["low_conf"] is False
    assert summarize_logits(np.array([10, 5, 0], np.int8), 6)["low_conf"] is True

    invalid = (lambda: summarize_logits(np.array([1, 2], np.int8), 0),
               lambda: summarize_logits(np.array([1, 2, 3], np.int16), 0),
               lambda: summarize_logits(np.array([1, 2, 3], np.int8), True),
               lambda: summarize_logits(np.array([1, 2, 3], np.int8), -1),
               lambda: summarize_logits(np.array([1, 2, 3], np.int8), 255))
    for call in invalid:
        expect_rejected(call)
    print("PASS: class tie-break, integer score and low-confidence semantics")


if __name__ == "__main__":
    main()
