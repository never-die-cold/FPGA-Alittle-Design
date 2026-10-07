#!/usr/bin/env python3
"""Audit stored PC-depth logs and the actual repository sources; no simulation."""
import hashlib
import json
from pathlib import Path
import re
import sys

folder = Path(__file__).resolve().parent
root = folder.parents[2]
manifest = json.loads((folder / "source_manifest.json").read_text())
for item in manifest["files"]:
    digest = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest()
    assert digest == item["sha256"], "source changed: " + item["path"]
log_name = sys.argv[1] if len(sys.argv) > 1 else "all-final.log"
lines = (folder / log_name).read_text().splitlines()
records = []
for i, line in enumerate(lines):
    if not line.startswith("== coremark "):
        continue
    def fields(text):
        return {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", text)}
    row = fields(line)
    classes = fields(lines[i + 1])
    bht = fields(lines[i + 2])
    assert lines[i + 1].startswith("CLASS:")
    assert lines[i + 2].startswith("BHT:")
    assert row["cycles"] == row["retired"] + row["bubbles"]
    assert classes["classified"] == row["bubbles"]
    assert sum(classes[k] for k in ("mul", "div", "load_use", "raw_nofwd",
                                   "control", "other")) == row["bubbles"]
    assert bht["lookup"] == bht["hit"] + bht["miss"]
    crc = re.search(r"crcfinal=0x([0-9a-f]+)", lines[i + 3]).group(1)
    assert crc == "8799" and row["retired"] == 10106386
    records.append((row, classes, bht))
anchors = [(0, 0, 19057438, 0, 0, 0),
           (1, 0, 17114141, 0, 0, 0),
           (1, 1, 16335562, 1854101, 1587055, 267046),
           (1, 2, 16232079, 1854101, 1690538, 163563)]
assert len(records) == len(anchors), "incomplete/extra CoreMark runs"
for (row, classes, bht), anchor in zip(records, anchors):
    actual = (row["mode"], bht["mode"], row["cycles"],
              bht["lookup"], bht["hit"], bht["miss"])
    assert actual == anchor, (actual, anchor)
    assert all(classes[k] == records[0][1][k]
               for k in ("mul", "div", "load_use", "other"))
assert records[0][0]["cycles"] - records[1][0]["cycles"] == 1943297
assert records[0][1]["raw_nofwd"] == 1943297
assert all(r[1]["raw_nofwd"] == 0 for r in records[1:])
print("PASS: source hashes, four anchors, CRC/retired, cycle classes and BHT counts")
