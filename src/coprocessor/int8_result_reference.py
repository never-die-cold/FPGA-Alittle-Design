"""Final class, margin, score and confidence semantics from C02."""
import numpy as np


def summarize_logits(logits, min_margin_q):
    """Summarize three signed INT8 logits without floating-point math."""
    if (not isinstance(logits, np.ndarray) or logits.dtype != np.int8
            or logits.shape != (3,)):
        raise ValueError("logits must be INT8 shape [3]")
    if type(min_margin_q) is not int or not 0 <= min_margin_q <= 254:
        raise ValueError("min_margin_q must be an integer in [0, 254]")
    order = sorted(range(3), key=lambda class_id: (-int(logits[class_id]), class_id))
    class_id = order[0]
    margin_q = int(logits[class_id]) - int(logits[order[1]])
    score_q15 = (margin_q * 32767 + 127) // 254
    return {"class_id": class_id, "margin_q": margin_q, "score_q15": score_q15,
            "low_conf": margin_q < min_margin_q}
