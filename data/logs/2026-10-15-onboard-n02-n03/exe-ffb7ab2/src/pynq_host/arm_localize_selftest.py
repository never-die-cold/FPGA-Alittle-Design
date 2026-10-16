#!/usr/bin/env python3
"""便携包自检：文件哈希、固定框/像素和导出格式；只使用标准库。"""
import hashlib
import json
import sys
from pathlib import Path


def verify_package(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    required = {"arm_localize.py", "reference.py", "arm_localize_selftest.py",
                "arm_localize_bench.py", "two_targets.json", "README.md"}
    if set(manifest["files"]) != required:
        raise ValueError("unexpected package file list")
    for name, digest in manifest["files"].items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"package missing or changed: {name}")
    return manifest


def main():
    root = Path(__file__).resolve().parent
    try:
        verify_package(root)
        sys.path.insert(0, str(root))
        from arm_localize import run
        output = root / "selftest-evidence/result.json"
        result = run(root / "two_targets.json", output, (4, 3), 7, 3)
        assert [t["bbox"] for t in result["targets"]] == [[1, 1, 2, 4], [7, 2, 9, 5]]
        assert [t["pixels"] for t in result["crops"]] == [[[20]*4]*3, [[30]*4]*3]
        for artifact, crop in zip(result["artifacts"], result["crops"]):
            pixels = bytes(p for row in crop["pixels"] for p in row)
            assert (output.parent / artifact["pgm"]["path"]).read_bytes() == b"P5\n4 3\n255\n" + pixels
            assert bytes.fromhex((output.parent / artifact["hex"]["path"]).read_text()) == pixels
        print("PASS: portable package hashes, exact localization/crops and PGM/hex")
        return 0
    except (OSError, ValueError, KeyError, AssertionError, ImportError) as exc:
        print(f"FAIL: portable package {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
