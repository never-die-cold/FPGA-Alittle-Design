"""Lossless file replay evidence and checked, persistent request reuse."""
import hashlib
import json
from pathlib import Path
import cv2


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save_bytes(folder, name, raw):
    (folder / name).write_bytes(raw)
    return {"path": name, "sha256": digest(raw)}


def save_png(folder, name, pixels):
    ok, encoded = cv2.imencode(".png", pixels)
    if not ok:
        raise OSError("PNG encoding failed")
    return save_bytes(folder, name, encoded.tobytes())


def load_existing(folder, fingerprint):
    raw = (folder / "result.json").read_bytes()
    if digest(raw) != (folder / "result.sha256").read_text(encoding="ascii").strip():
        raise ValueError("replay manifest hash mismatch")
    result = json.loads(raw)
    if result.get("mode") != "FILE_REPLAY" or result.get("request_fingerprint") != fingerprint:
        raise ValueError("request ID already used with different inputs")
    root = folder.resolve()
    for item in result["artifacts"]:
        path = (folder / item["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file() or digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("missing, modified or out-of-folder replay artifact")
    return result
