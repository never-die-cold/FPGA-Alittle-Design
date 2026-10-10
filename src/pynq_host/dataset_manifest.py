"""Validate the proposed 720p collection manifest; labels remain human claims."""
import csv
import hashlib
import io
import re
from pathlib import Path
import cv2
import numpy as np

CLASSES = ("bolt", "nut", "washer")
REQUIRED = frozenset("frame_id session split light bg spacing obj_id class x0 y0 x1 y1".split())
OPTIONAL = frozenset(("notes", "specimen_id"))
BOX = ("x0", "y0", "x1", "y1")
IDENTITY = r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}"


def validate_row(row):
    if (not isinstance(row, dict) or not REQUIRED <= set(row)
            or set(row) - REQUIRED - OPTIONAL or any(not isinstance(value, str) for value in row.values())):
        raise ValueError("invalid manifest fields")
    if (not re.fullmatch(r"sess-[a-z0-9]+(?:-[a-z0-9]+)*", row["session"])
            or not re.fullmatch(r"frame_[0-9]{5}", row["frame_id"])
            or row["split"] not in ("train", "val", "test")
            or row["light"] not in ("L0", "L1", "L2", "L3")
            or row["bg"] not in ("dark", "gray", "wood") or not row["spacing"]):
        raise ValueError("invalid manifest identity or conditions")
    if not row["class"]:
        if any(row[name] for name in ("obj_id", *BOX)) or row.get("specimen_id", ""):
            raise ValueError("empty frame must not contain a target")
        if row["split"] != "test":
            raise ValueError("empty collection frames belong to test")
        return None
    specimen = row.get("specimen_id", "")
    if (row["class"] not in CLASSES or not re.fullmatch(IDENTITY, row["obj_id"])
            or (specimen and not re.fullmatch(IDENTITY, specimen))
            or any(not re.fullmatch(r"[0-9]+", row[name]) for name in BOX)):
        raise ValueError("invalid target identity, class or coordinates")
    x0, y0, x1, y1 = (int(row[name]) for name in BOX)
    if not (0 <= x0 < x1 <= 1280 and 0 <= y0 < y1 <= 720):
        raise ValueError("target outside half-open 720p bounds")
    return {"obj_id": row["obj_id"], "class": row["class"], "bbox": [x0, y0, x1, y1],
            "specimen_id": specimen}


def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("collection file escapes dataset root")
    return path


def load_manifest(root, max_targets=10):
    root = Path(root).resolve()
    if type(max_targets) is not int or not 1 <= max_targets <= 16:
        raise ValueError("invalid collection target limit")
    raw = contained(root, "manifest.csv").read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if (not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames))
            or not REQUIRED <= set(reader.fieldnames) or set(reader.fieldnames) - REQUIRED - OPTIONAL):
        raise ValueError("invalid manifest header")
    frames = {}
    for row in reader:
        target = validate_row(row)
        key = (row["session"], row["frame_id"])
        metadata = {name: row[name] for name in ("session", "frame_id", "split", "light", "bg", "spacing")}
        if key not in frames:
            name = f"raw/{key[0]}/{key[1]}.png"
            pixels_raw = contained(root, name).read_bytes()
            if not pixels_raw.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("collection frame is not a PNG file")
            image = cv2.imdecode(np.frombuffer(pixels_raw, np.uint8), cv2.IMREAD_UNCHANGED)
            if image is None or image.shape != (720, 1280, 3) or image.dtype != np.uint8:
                raise ValueError("collection frame must be lossless 720p uint8 BGR PNG")
            frames[key] = {**metadata, "image": name, "targets": [], "empty_scene": target is None,
                           "source_sha256": hashlib.sha256(pixels_raw).hexdigest(),
                           "pixels_sha256": hashlib.sha256(image.tobytes()).hexdigest()}
        else:
            frame = frames[key]
            if (any(frame[name] != value for name, value in metadata.items())
                    or target is None or frame["empty_scene"]):
                raise ValueError("conflicting frame metadata or empty marker")
        if target is None:
            continue
        frame = frames[key]
        x0, y0, x1, y1 = target["bbox"]
        for other in frame["targets"]:
            a, b, c, d = other["bbox"]
            same_specimen = target["specimen_id"] and other["specimen_id"] == target["specimen_id"]
            if (other["obj_id"] == target["obj_id"] or same_specimen
                    or (max(x0, a) < min(x1, c) and max(y0, b) < min(y1, d))):
                raise ValueError("duplicate target/specimen ID or overlapping collection boxes")
        frame["targets"].append(target)
        if len(frame["targets"]) > max_targets:
            raise ValueError("collection target limit exceeded")
    if not frames:
        raise ValueError("collection manifest has no frames")
    listed = {contained(root, frame["image"]) for frame in frames.values()}
    actual = {path.resolve() for path in (root / "raw").rglob("*")
              if path.is_file() and path.suffix.lower() == ".png"}
    if actual != listed:
        raise ValueError("unlisted raw PNG frames")
    return {"manifest_sha256": hashlib.sha256(raw).hexdigest(), "max_targets": max_targets,
            "frames": [frames[key] for key in sorted(frames)]}
