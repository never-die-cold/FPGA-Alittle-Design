"""M2 interface prototype: mock location packets, never classification/check verdicts."""
import math
import time

VERSION = 1


def uint(value, name):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"invalid {name}")
    return value


def validate_packet(packet):
    if packet.get("version") != VERSION or packet.get("mode") != "MOCK":
        raise ValueError("only explicitly marked M2 mock packets are supported")
    if not isinstance(packet.get("session_id"), str) or not packet["session_id"]:
        raise ValueError("missing session_id")
    for name in ("frame_id", "config_id"):
        uint(packet.get(name), name)
    w, h = packet.get("width"), packet.get("height")
    if type(w) is not int or type(h) is not int or not (1 <= w <= 4096 and 1 <= h <= 2160):
        raise ValueError("invalid dimensions")
    stamp = packet.get("created_at")
    if type(stamp) not in (int, float) or not math.isfinite(stamp):
        raise ValueError("invalid timestamp")
    if packet.get("status") != "LOCATION_ONLY" or not isinstance(packet.get("targets"), list):
        raise ValueError("not a location-only packet")
    if len(packet["targets"]) > 16:
        raise ValueError("target limit")
    ids = set()
    for target in packet["targets"]:
        identity = uint(target.get("target_id"), "target_id")
        if identity in ids:
            raise ValueError("duplicate target_id")
        ids.add(identity)
        box = target.get("bbox")
        if not isinstance(box, list) or len(box) != 4 or any(type(x) is not int for x in box):
            raise ValueError("invalid box")
        x0, y0, x1, y1 = box
        if not (0 <= x0 <= x1 < w and 0 <= y0 <= y1 < h):
            raise ValueError("box outside frame")
        if "class" in target or "verdict" in target:
            raise ValueError("classification is outside this mock contract")
    return packet


def mock_packet(session_id, frame_id, config_id):
    return validate_packet({"version": VERSION, "mode": "MOCK", "session_id": session_id,
        "frame_id": frame_id, "config_id": config_id, "width": 1280, "height": 720,
        "created_at": time.time(), "status": "LOCATION_ONLY",
        "targets": [{"target_id": 0, "bbox": [180, 170, 339, 289]},
                    {"target_id": 1, "bbox": [730, 400, 929, 559]}]})


def is_current(packet, session_id, frame_id, config_id, max_age=1.0):
    validate_packet(packet)
    age = time.time() - packet["created_at"]
    return (packet["session_id"] == session_id and packet["frame_id"] == frame_id
            and packet["config_id"] == config_id and 0 <= age <= max_age)
