#!/usr/bin/env python3
"""Parse the generic firmware tb PASS line and report reproducible CPI data."""
import re
import sys

PATTERN = re.compile(
    r"PASS: coremark cycles=(\d+) instrs=(\d+) bubbles=(\d+) cpi=(\d+)\.(\d+)"
)


def main(argv):
    if len(argv) not in (2, 3):
        print("usage: python data/scripts/cpi_harness.py <log> [benchmark-name]")
        return 2

    log_path = argv[1]
    name = argv[2] if len(argv) == 3 else "benchmark-v0.1"
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        match = PATTERN.search(handle.read())
    if match is None:
        print("FAIL: log has no firmware PASS/CPI line")
        return 1

    cycles, instrs, bubbles, _, _ = (int(value) for value in match.groups())
    if instrs == 0:
        print("FAIL: retired instruction count is zero")
        return 1
    cpi = cycles / instrs

    print(f"PASS: {name} cycles={cycles} instrs={instrs} bubbles={bubbles} cpi={cpi:.3f}")
    print("metrics.csv suggested row:")
    print(
        f"RISC-V {name} CPI,core benchmark,{cpi:.3f},CPI,"
        f"iverilog; cycles/instrs,{cycles} cycles / {instrs} instrs,{log_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
