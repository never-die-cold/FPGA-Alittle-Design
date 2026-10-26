#!/usr/bin/env python3
"""Fail-closed checks for the cop_job memory image and Vivado synthesis log."""
import argparse
import re
from pathlib import Path

EXPECTED_PREFIX = ("00008117", "00010113", "00000297")
DIAGNOSTIC = re.compile(r"readmem[hb]|cop_job\.hex", re.IGNORECASE)
BAD = re.compile(r"warning|error|critical|cannot|failed|missing|not found|no such", re.IGNORECASE)


def hex_words(path):
    words = []
    for number, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw.split("//", 1)[0].split("#", 1)[0].strip()
        if not line:
            continue
        if not re.fullmatch(r"[0-9a-fA-F]{8}", line):
            raise ValueError(f"{path}:{number}: expected one 32-bit hexadecimal word")
        words.append(line.lower())
    return words


def precheck(path, report):
    path = path.resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"firmware image is missing or empty: {path}")
    words = hex_words(path)
    if tuple(words[:len(EXPECTED_PREFIX)]) != EXPECTED_PREFIX:
        raise ValueError(f"cop_job prefix mismatch: got={words[:3]} expected={list(EXPECTED_PREFIX)}")
    if words[0] in ("00000000", "00000013"):
        raise ValueError(f"cop_job first word is an empty/idle instruction: {words[0]}")
    report.write_bytes((f"IMEM_HEX={path}\nBYTES={path.stat().st_size}\nWORDS={len(words)}\n"
                        f"PREFIX={','.join(words[:3])}\n").encode("ascii"))
    return words[0]


def materialize(path, imem, dmem, depth):
    words = hex_words(path.resolve())
    if depth < 1 or len(words) > depth:
        raise ValueError(f"firmware words={len(words)} do not fit memory depth={depth}")
    imem_words = words + ["00000013"] * (depth - len(words))
    dmem_words = words + ["00000000"] * (depth - len(words))
    imem.write_bytes(("\n".join(imem_words) + "\n").encode("ascii"))
    dmem.write_bytes(("\n".join(dmem_words) + "\n").encode("ascii"))
    return len(words)


def scan_log(path, report):
    if not path.is_file():
        raise ValueError(f"synthesis log is missing: {path}")
    lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
             if DIAGNOSTIC.search(line)]
    report.write_bytes((("\n".join(lines) + "\n") if lines else
                        "NO_READMEM_OR_COP_JOB_DIAGNOSTICS\n").encode("utf-8"))
    bad = [line for line in lines if BAD.search(line)]
    if bad:
        raise ValueError("readmem/cop_job synthesis diagnostic is fail-closed: " + bad[0])
    return len(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("precheck"); pre.add_argument("image", type=Path); pre.add_argument("report", type=Path)
    mat = sub.add_parser("materialize"); mat.add_argument("image", type=Path)
    mat.add_argument("imem", type=Path); mat.add_argument("dmem", type=Path)
    mat.add_argument("--depth", type=int, default=8192)
    log = sub.add_parser("scan-log"); log.add_argument("log", type=Path); log.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "precheck":
            print("IMEM PRECHECK PASSED: first_word=" + precheck(args.image, args.report))
        elif args.command == "materialize":
            count = materialize(args.image, args.imem, args.dmem, args.depth)
            print(f"IMEM MATERIALIZE PASSED: source_words={count} depth={args.depth}")
        else:
            print(f"READMEM LOG GATE PASSED: relevant_lines={scan_log(args.log, args.report)} blocking=0")
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, "IMEM GATE FAILED: " + str(error) + "\n")


if __name__ == "__main__":
    main()
