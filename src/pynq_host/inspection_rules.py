"""Offline work-order candidate; no LIVE protocol or RISC-V implementation."""
import math

CLASSES = ("bolt", "nut", "washer")
POLICY_MAX = 10  # C03 §8 冻结：检查 V0 业务策略上限（协议/硬件能力仍为 16）


def effective_policy(max_targets, policy_max=None):
    """业务策略上限：默认 10 且不得超过能力上限（调用方传更小能力时按能力收窄）。"""
    if policy_max is None:
        return min(POLICY_MAX, max_targets)
    return policy_max


def judge(targets, order, min_score, max_targets=16, policy_max=None):
    """Class counts and signed deltas; uncertainty always requests reinspection.

    边界（C03 §8）：目标数或工单总数超过**业务策略**（默认 10）即 target_limit/RECHECK，
    不截断放行；max_targets 只是协议/硬件能力上限（16），不自动成为业务放行条件。
    """
    policy = effective_policy(max_targets, policy_max)
    if (type(max_targets) is not int or not 1 <= max_targets <= 16
            or type(policy) is not int or not 1 <= policy <= max_targets
            or not isinstance(order, dict) or set(order) != set(CLASSES)
            or any(type(value) is not int or value < 0 for value in order.values())
            or not 1 <= sum(order.values()) <= policy):
        raise ValueError("invalid work order or target limit")
    if type(min_score) not in (int, float) or not math.isfinite(min_score) or not 0 <= min_score <= 1:
        raise ValueError("min_score must be an explicit finite probability")
    if not isinstance(targets, list):
        raise ValueError("targets must be a list")
    actual = dict.fromkeys(CLASSES, 0)
    reasons = set()
    if len(targets) > policy:
        reasons.add("target_limit")
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError("invalid target")
        label, score = target.get("class"), target.get("score")
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("invalid classification score")
        if label not in CLASSES:
            reasons.add("unknown_class")
        else:
            actual[label] += 1
        if score < min_score:
            reasons.add("low_score")
        border = target.get("touches_border", False)
        if type(border) is not bool:
            raise ValueError("invalid border flag")
        if border:
            reasons.add("touches_border")
    delta = {label: actual[label] - order[label] for label in CLASSES}
    verdict = "RECHECK" if reasons else ("CHECK_FAIL" if any(delta.values()) else "CHECK_PASS")
    return {"verdict": verdict, "expected": dict(order), "actual": actual, "delta": delta,
            "missing": {label: max(-value, 0) for label, value in delta.items()},
            "extra": {label: max(value, 0) for label, value in delta.items()},
            "reasons": sorted(reasons)}
