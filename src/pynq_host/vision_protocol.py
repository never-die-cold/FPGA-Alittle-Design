"""M2 interface prototype: mock location packets, never classification/check verdicts.

schema v1.1（docs/vision-sync-protocol-decisions.md D2/D3/D6）：
- 新增必填 check_id：检查轮次标识，服务端生成、uint32 单调回绕（D2）。
- trigger_ref 可选回显字段：EXE 触发时携带，服务端原样返回（D2）。
- 有效性判据（D3）= session_id + config_id + created_at 年龄；frame_id 仅透传展示，
  不参与匹配——EXE 无法把结果帧号对应到采集卡画面（决策单 §1）。
- bbox 为半开区间 [x0,x1)×[y0,y1)，宽=x1-x0；端点语义对齐定位外包需求 L2
  （docs/outsource/localization-requirements.md）。
"""
import math
import time

VERSION = 1
MAX_TARGETS = 16
MAX_TRIGGER_REF_LEN = 64
PACKET_FIELDS = frozenset(("version", "mode", "session_id", "frame_id", "config_id",
                          "check_id", "trigger_ref", "width", "height", "created_at",
                          "status", "targets"))
TARGET_FIELDS = frozenset(("target_id", "bbox"))


def uint(value, name):
    """uint32 校验。type() is 严格判型：bool 是 int 的子类，用 type() 挡住 True/False 冒充 0/1。"""
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"invalid {name}")
    return value


def validate_packet(packet):
    if not isinstance(packet, dict) or set(packet) - PACKET_FIELDS:
        raise ValueError("invalid packet fields")
    if packet.get("version") != VERSION or packet.get("mode") != "MOCK":
        raise ValueError("only explicitly marked M2 mock packets are supported")
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
    if packet.get("status") != "LOCATION_ONLY" or not isinstance(packet.get("targets"), list):
        raise ValueError("not a location-only packet")
    if len(packet["targets"]) > MAX_TARGETS:
        raise ValueError("target limit")
    ids = set()
    for target in packet["targets"]:
        if not isinstance(target, dict) or set(target) - TARGET_FIELDS:
            raise ValueError("invalid target fields")
        identity = uint(target.get("target_id"), "target_id")
        if identity in ids:
            raise ValueError("duplicate target_id")
        ids.add(identity)
        box = target.get("bbox")
        if not isinstance(box, list) or len(box) != 4 or any(type(x) is not int for x in box):
            raise ValueError("invalid box")
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError("invalid box bounds")
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
