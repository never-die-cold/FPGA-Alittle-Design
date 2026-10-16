"""M2/M3 result packet contract (schema v1.2) — docs/vision-sync-protocol-decisions.md D6.

v1.1：check_id / trigger_ref / bbox 半开区间（D1–D3）。
v1.2（2026-10-10 WC+NC 确认，LIVE 轮廓冻结）：
- mode 两类：MOCK（严格——仅定位，不允 class/score/decision）与 LIVE（板端真实/原型服务）；
- LIVE 目标可带 class（bolt/nut/washer 或 null）与 score（0–1）；
- LIVE status ∈ LOCATION_ONLY / CHECK_PASS / CHECK_FAIL / RECHECK；判定类 status 必带
  decision（工单判定：expected/actual/delta/missing/extra/reasons，verdict 可选但出现时
  须与 status 一致），LOCATION_ONLY 不得带 decision；
- prototype 可选布尔（仅 LIVE）：板端服务以离线产物代实时结果时必须置 true
  （EXE 恒加 PROTOTYPE 标识，对齐 MOCK 的诚实约束）；
- 有效性判据（D3）= session_id + config_id + created_at 年龄；frame_id 仅透传展示。
"""
import math
import time

VERSION = 1
MAX_TARGETS = 16
MAX_TRIGGER_REF_LEN = 64
CLASSES = ("bolt", "nut", "washer")
VERDICTS = ("CHECK_PASS", "CHECK_FAIL", "RECHECK")
LOCATION_STATUS = "LOCATION_ONLY"
MOCK_PACKET_FIELDS = frozenset(("version", "mode", "session_id", "frame_id", "config_id",
                                "check_id", "trigger_ref", "width", "height", "created_at",
                                "status", "targets"))
LIVE_PACKET_FIELDS = MOCK_PACKET_FIELDS | frozenset(("decision", "prototype"))
MOCK_TARGET_FIELDS = frozenset(("target_id", "bbox"))
LIVE_TARGET_FIELDS = frozenset(("target_id", "bbox", "class", "score"))
DECISION_FIELDS = frozenset(("verdict", "expected", "actual", "delta", "missing", "extra",
                             "reasons"))


def uint(value, name):
    """uint32 校验。type() is 严格判型：bool 是 int 的子类，用 type() 挡住 True/False 冒充 0/1。"""
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"invalid {name}")
    return value


def _validate_target(target, target_fields, width, height):
    if not isinstance(target, dict) or set(target) - target_fields:
        raise ValueError("invalid target fields")
    identity = uint(target.get("target_id"), "target_id")
    box = target.get("bbox")
    if not isinstance(box, list) or len(box) != 4 or any(type(x) is not int for x in box):
        raise ValueError("invalid box")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("invalid box bounds")
    return identity


def _validate_class_score(target):
    label = target.get("class")
    if label is not None and label not in CLASSES:
        raise ValueError("invalid target class")
    if "score" in target:
        score = target["score"]
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("invalid target score")


def _validate_decision(decision, status):
    if not isinstance(decision, dict) or set(decision) - DECISION_FIELDS:
        raise ValueError("invalid decision fields")
    if decision.get("verdict") is not None and decision["verdict"] != status:
        raise ValueError("decision verdict mismatch")
    for name in ("expected", "actual", "delta", "missing", "extra"):
        counts = decision.get(name)
        if not isinstance(counts, dict) or set(counts) != set(CLASSES):
            raise ValueError("invalid decision counts")
        for value in counts.values():
            if type(value) is not int or (name != "delta" and value < 0):
                raise ValueError("invalid decision counts")
    reasons = decision.get("reasons")
    if not isinstance(reasons, list) or any(not isinstance(item, str) or not item
                                            for item in reasons):
        raise ValueError("invalid decision reasons")


def validate_packet(packet):
    """校验 MOCK/LIVE 报文（严格白名单）；通过返回原报文，失败抛 ValueError。"""
    if not isinstance(packet, dict) or packet.get("mode") not in ("MOCK", "LIVE"):
        raise ValueError("invalid packet fields")
    live = packet["mode"] == "LIVE"
    if set(packet) - (LIVE_PACKET_FIELDS if live else MOCK_PACKET_FIELDS) \
            or packet.get("version") != VERSION:
        raise ValueError("invalid packet fields")
    if not isinstance(packet.get("session_id"), str) or not packet["session_id"]:
        raise ValueError("missing session_id")
    for name in ("frame_id", "config_id", "check_id"):
        uint(packet.get(name), name)
    ref = packet.get("trigger_ref")
    if ref is not None and (not isinstance(ref, str) or not 0 < len(ref) <= MAX_TRIGGER_REF_LEN):
        raise ValueError("invalid trigger_ref")
    w, h = packet.get("width"), packet.get("height")
    if type(w) is not int or type(h) is not int or not (1 <= w <= 4096 and 1 <= h <= 2160):
        raise ValueError("invalid dimensions")
    stamp = packet.get("created_at")
    if type(stamp) not in (int, float) or not math.isfinite(stamp):
        raise ValueError("invalid timestamp")
    status = packet.get("status")
    if live:
        if status not in (LOCATION_STATUS,) + VERDICTS:
            raise ValueError("invalid status")
    elif status != LOCATION_STATUS:
        raise ValueError("not a location-only packet")
    targets = packet.get("targets")
    if not isinstance(targets, list):
        raise ValueError("invalid targets")
    if len(targets) > MAX_TARGETS:
        raise ValueError("target limit")
    ids = set()
    target_fields = LIVE_TARGET_FIELDS if live else MOCK_TARGET_FIELDS
    for target in targets:
        identity = _validate_target(target, target_fields, w, h)
        if identity in ids:
            raise ValueError("duplicate target_id")
        ids.add(identity)
        if live:
            _validate_class_score(target)
    if live:
        decision = packet.get("decision")
        if status == LOCATION_STATUS:
            if decision is not None:
                raise ValueError("decision requires a verdict status")
        else:
            _validate_decision(decision, status)
        if type(packet.get("prototype", False)) is not bool:
            raise ValueError("invalid prototype flag")
    return packet


def mock_packet(session_id, frame_id, config_id, check_id, trigger_ref=None):
    payload = {"version": VERSION, "mode": "MOCK", "session_id": session_id,
        "frame_id": frame_id, "config_id": config_id, "check_id": check_id,
        "width": 1280, "height": 720,
        "created_at": time.time(), "status": "LOCATION_ONLY",
        "targets": [{"target_id": 0, "bbox": [180, 170, 339, 289]},
                    {"target_id": 1, "bbox": [730, 400, 929, 559]}]}
    if trigger_ref is not None:
        payload["trigger_ref"] = trigger_ref
    return validate_packet(payload)


def is_current(packet, session_id, config_id, max_age=1.0):
    """D3 判据：会话一致 + 配置一致 + 年龄窗内。frame_id 不参与匹配。"""
    validate_packet(packet)
    age = time.time() - packet["created_at"]
    return (packet["session_id"] == session_id and packet["config_id"] == config_id
            and 0 <= age <= max_age)
