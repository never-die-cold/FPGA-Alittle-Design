#!/usr/bin/env python3
"""Fail-closed structural audit for a 64x64 grayscale fastener ROI dataset."""
import argparse, csv, hashlib, json, struct
from collections import Counter
from pathlib import Path

CLASSES = ("bolt", "nut", "washer")
HEADER = ("file", "class", "source_file", "source_width", "source_height", "x0", "y0", "x1", "y1")


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def png_info(path):
    raw = path.read_bytes()[:33]
    if len(raw) != 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    width, height, depth, color, _, _, _ = struct.unpack(">IIBBBBB", raw[16:29])
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color, 0)
    return width, height, depth, channels


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path.is_symlink():
        raise ValueError(f"path escapes dataset or is symlink: {name}")
    return path


def audit(root):
    root = root.resolve(); annotations = root / "annotations.csv"
    with annotations.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != HEADER: raise ValueError("invalid annotations.csv header")
        rows = list(reader)
    if not rows: raise ValueError("annotations.csv has no ROI rows")
    records, seen, distribution = {}, set(), Counter()
    for line, row in enumerate(rows, 2):
        name, label = row["file"], row["class"]
        if name in seen or label not in CLASSES: raise ValueError(f"duplicate file or class at row {line}")
        path = inside(root, name)
        if path.parent.name != label or path.parent.parent.name != "images" or not path.is_file():
            raise ValueError(f"ROI path/class mismatch at row {line}")
        try:
            sw, sh, x0, y0, x1, y1 = (int(row[key]) for key in
                                       ("source_width", "source_height", "x0", "y0", "x1", "y1"))
        except ValueError as error:
            raise ValueError(f"non-integer bbox at row {line}") from error
        if not (sw > 0 and sh > 0 and 0 <= x0 < x1 <= sw and 0 <= y0 < y1 <= sh):
            raise ValueError(f"out-of-bounds or zero-area bbox at row {line}")
        if png_info(path) != (64, 64, 8, 1): raise ValueError(f"ROI must be 64x64 uint8 grayscale: {name}")
        seen.add(name); distribution[label] += 1; records[name] = label
    actual = {path.relative_to(root).as_posix() for path in (root / "images").rglob("*") if path.is_file()}
    if actual != seen: raise ValueError("images and annotations.csv differ")
    splits, assigned = {}, set()
    for split in ("train", "val", "test"):
        path = root / "splits" / f"{split}.txt"
        if not path.is_file(): raise ValueError(f"missing split manifest: {split}.txt")
        names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(names) != len(set(names)) or any(name not in records for name in names):
            raise ValueError(f"duplicate or unknown ROI in {split}.txt")
        overlap = assigned.intersection(names)
        if overlap: raise ValueError(f"ROI appears in multiple splits: {sorted(overlap)[0]}")
        assigned.update(names); counts = Counter(records[name] for name in names)
        if any(counts[name] == 0 for name in CLASSES): raise ValueError(f"{split} lacks a class")
        splits[split] = dict(sorted(counts.items()))
    if assigned != seen: raise ValueError("split manifests do not cover every ROI")
    files = {path.relative_to(root).as_posix(): digest(path) for path in sorted(root.rglob("*"))
             if path.is_file() and not path.is_symlink()}
    return {"verdict": "PASS_STRUCTURE_ONLY", "file_count": len(seen),
            "image_spec": "64x64 uint8 grayscale PNG", "class_distribution": dict(sorted(distribution.items())),
            "split_distribution": splits, "file_sha256": files,
            "limits": "structure/hashes only; source and label truth remain human-reviewed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path); args = parser.parse_args()
    try: report = json.dumps(audit(args.dataset), indent=2, sort_keys=True) + "\n"
    except (OSError, UnicodeError, ValueError, csv.Error, struct.error) as error:
        parser.exit(1, f"ROI_DATASET_FAIL: {error}\n")
    if args.output: args.output.write_bytes(report.encode("utf-8"))
    print(report, end=""); return 0


if __name__ == "__main__": raise SystemExit(main())
