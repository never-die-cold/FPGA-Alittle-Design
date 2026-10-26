#!/usr/bin/env python3
"""Synthetic compliant/noncompliant cases for the board-run summarizer."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/summarize_board_run.py"


def result(case, sequence, error=0, score=None):
    zero = case == "zero"
    return {"case": case, "error_code": error, "result_seq": sequence,
            "class_id": 2 if zero else 0, "margin_q": 2 if zero else 0,
            "score_q15": (258 if zero else 0) if score is None else score,
            "low_conf": 1, "logits": [2, -3, 4] if zero else [1, -3, 1]}


def invoke(directory, expected):
    return subprocess.run([sys.executable, str(TOOL), str(directory), "--expected", str(expected)],
                          text=True, capture_output=True, check=False)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True)
    root = parser.parse_args().output
    if root.exists(): shutil.rmtree(root)
    good, bad = root / "good", root / "bad"
    good.mkdir(parents=True); bad.mkdir()
    expected = root / "EXPECTED_OUTPUTS.tsv"
    expected.write_bytes(b"case\tclass_id\tmargin_q\tscore_q15\tlow_conf\tlogits\n"
                         b"pattern\t0\t0\t0\t1\t1,-3,1\nzero\t2\t2\t258\t1\t2,-3,4\n")
    (good / "clock.log").write_bytes(
        b"measured_fclk1_mhz=40.000000\nstatus_first_reads=0x00000001,0x00000001\n")
    for index, case in enumerate(("pattern", "zero"), 1):
        (good / f"{case}.json").write_bytes((json.dumps(result(case, index)) + "\n").encode())
    passed = invoke(good, expected)
    assert passed.returncode == 0 and "DATA_CHECK=PASS" in passed.stdout
    assert "data-layer verdict only" in passed.stdout and passed.stdout.count("\tMATCH") >= 16

    (bad / "clock.log").write_bytes(
        b"measured_fclk1_mhz=39.999999\nstatus_first_reads=0x00000000,0x00000001\n")
    (bad / "zero.json").write_bytes((json.dumps(result("zero", 0, error=5, score=257)) + "\n").encode())
    failed = invoke(bad, expected)
    assert failed.returncode == 1 and "DATA_CHECK=FAIL" in failed.stdout
    for field in ("fclk1_mhz", "first_STATUS", "ERROR_CODE", "RESULT_SEQ", "score_q15"):
        assert field in failed.stdout
    print("PASS: board_run_summary accepts exact clock/status/golden data and rejects clock, "
          "first-status, error, sequence, and result mismatches; verdict remains data-only")


if __name__ == "__main__": main()
