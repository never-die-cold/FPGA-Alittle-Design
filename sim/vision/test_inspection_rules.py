"""Work-order normal/missing/extra/wrong/empty and uncertainty precedence."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from inspection_rules import judge


def main():
    order = {"bolt": 1, "nut": 1, "washer": 1}
    targets = [{"class": name, "score": 0.9} for name in order]
    assert judge(targets, order, 0.8)["verdict"] == "CHECK_PASS"
    missing = judge(targets[:2], order, 0.8)
    assert missing["verdict"] == "CHECK_FAIL" and missing["missing"]["washer"] == 1
    extra = judge(targets + [targets[0]], order, 0.8)
    assert extra["extra"]["bolt"] == 1 and extra["verdict"] == "CHECK_FAIL"
    wrong = judge([targets[0], targets[0], targets[2]], order, 0.8)
    assert wrong["missing"]["nut"] == wrong["extra"]["bolt"] == 1
    assert judge([], order, 0.8)["verdict"] == "CHECK_FAIL"
    for field, value, reason in (("score", 0.7, "low_score"),
                                  ("touches_border", True, "touches_border"),
                                  ("class", "unknown", "unknown_class")):
        result = judge([{**targets[0], field: value}], order, 0.8)
        assert result["verdict"] == "RECHECK" and reason in result["reasons"]
    assert judge(targets * 6, order, 0.8)["reasons"] == ["target_limit"]
    invalid = [(targets, {**order, "bolt": True}, 0.8), (targets, dict.fromkeys(order, 0), 0.8),
               (targets, {**order, "nut": -1}, 0.8), (targets, order, float("nan")),
               ([{**targets[0], "score": float("nan")}], order, 0.8)]
    for args in invalid:
        try:
            judge(*args)
        except ValueError:
            continue
        raise AssertionError("invalid work order/score accepted")
    print("PASS: work-order pass/fail/recheck counts and invalid inputs")


if __name__ == "__main__":
    main()
