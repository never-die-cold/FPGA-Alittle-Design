#!/usr/bin/env python3
"""Build synthetic ROI data and exercise compliant/rejected audit paths."""
import argparse, csv, struct, subprocess, sys, zlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/check_roi_dataset.py"
HEADER = ("file", "class", "source_file", "source_width", "source_height", "x0", "y0", "x1", "y1")


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def gray_png(width=64, height=64, value=17):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    pixels = b"".join(b"\0" + bytes([value]) * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


def run(dataset):
    return subprocess.run([sys.executable, str(TOOL), str(dataset)], text=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True)
    root = parser.parse_args().output
    if root.exists(): shutil.rmtree(root)
    (root / "splits").mkdir(parents=True)
    rows, split_names = [], {name: [] for name in ("train", "val", "test")}
    for split_index, split in enumerate(split_names):
        for class_index, label in enumerate(("bolt", "nut", "washer")):
            name = f"images/{label}/{split}-01.png"; path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gray_png(value=20 + split_index * 3 + class_index))
            rows.append(dict(zip(HEADER, (name, label, f"raw/{split}.png", 1280, 720,
                                           10, 20, 110, 120))))
            split_names[split].append(name)
    with (root / "annotations.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    for split, names in split_names.items():
        (root / "splits" / f"{split}.txt").write_bytes(("\n".join(names) + "\n").encode())
    passed = run(root)
    assert passed.returncode == 0 and '"verdict": "PASS_STRUCTURE_ONLY"' in passed.stdout
    assert '"file_count": 9' in passed.stdout and '"bolt": 3' in passed.stdout

    manifest = root / "annotations.csv"; original = manifest.read_text(encoding="utf-8")
    manifest.write_text(original.replace(",10,20,110,120", ",10,20,10,120", 1), encoding="utf-8")
    failed = run(root)
    assert failed.returncode == 1 and "zero-area bbox" in failed.stderr
    manifest.write_text(original, encoding="utf-8")
    (root / "splits/test.txt").unlink()
    failed = run(root)
    assert failed.returncode == 1 and "missing split manifest" in failed.stderr
    print("PASS: roi_dataset synthetic 3-class/3-split fixture; dimensions, channels, bbox, "
          "split coverage, distribution, and per-file SHA256 audited; invalid samples rejected")


if __name__ == "__main__": main()
