#!/usr/bin/env python3
"""Repository-local negative and positive tests for the IMEM build gate."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import cop_imem_gate as gate


def rejected(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), error
        return
    raise AssertionError("negative case was accepted: " + text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    image = ROOT / "src/riscv_fw/cop_job.hex"
    assert gate.precheck(image, args.output / "precheck.txt") == "00008117"
    imem, dmem = args.output / "cop_job.imem.hex", args.output / "cop_job.dmem.hex"
    source_words = gate.materialize(image, imem, dmem, 8192)
    assert source_words == 4094
    assert len(gate.hex_words(imem)) == len(gate.hex_words(dmem)) == 8192
    assert gate.hex_words(imem)[-1] == "00000013" and gate.hex_words(dmem)[-1] == "00000000"

    empty = args.output / "empty.hex"; empty.write_bytes(b"")
    rejected(lambda: gate.precheck(empty, args.output / "bad.txt"), "missing or empty")
    wrong = args.output / "wrong.hex"; wrong.write_bytes(b"00000000\n00010113\n00000297\n")
    rejected(lambda: gate.precheck(wrong, args.output / "bad.txt"), "prefix mismatch")

    clean = args.output / "clean.log"; clean.write_text("INFO: synthesis complete\n", encoding="ascii")
    assert gate.scan_log(clean, args.output / "clean-report.txt") == 0
    warning = args.output / "warning.log"
    warning.write_text("WARNING: $readmemh cannot open src/riscv_fw/cop_job.hex\n", encoding="ascii")
    rejected(lambda: gate.scan_log(warning, args.output / "warning-report.txt"), "fail-closed")
    print("PASS: imem_gate validates cop_job prefix, materializes 8192-word NOP/zero images, and "
          "rejects missing, empty, wrong-prefix, and readmem-warning inputs")


if __name__ == "__main__":
    main()
