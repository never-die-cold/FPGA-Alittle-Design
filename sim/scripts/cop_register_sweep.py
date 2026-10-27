#!/usr/bin/env python3
"""Check first-read correctness across distinct cop registers after one case."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--rounds", type=int, default=1000)
    parser.add_argument("--result-seq", type=int, default=1)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    package = args.package.resolve()
    sys.path.insert(0, str(package / "payload/tools"))
    import cop_payload_loader as loader
    import pynq.pl_server.embedded_device
    from pynq import Clocks, MMIO, PL

    bit = package / "payload/pynq_cop_40mhz.bit"
    if not PL.bitfile_name or Path(PL.bitfile_name).resolve() != bit:
        raise SystemExit("requested cop overlay is not loaded")
    _, input_mhz = loader.hwh_clock_plan(bit.with_suffix(".hwh"))
    if abs(float(Clocks.fclk1_mhz) - input_mhz) > 0.001:
        raise SystemExit("FCLK1 differs from HWH")
    manifest, _, _, expected, _ = loader.package_inputs(package, args.case)
    logits = [int(v) & 255 for v in expected["logits"].split(",")]
    words = {0: 0x434f5030, 4: 0, 8: 0, 0x24: manifest["model_id"], 0x2c: 1,
             0x70: (int(expected["class_id"]) << 16) | (1 << 24) |
                   (int(expected["low_conf"]) << 25),
             0x74: sum(v << (8*i) for i, v in enumerate(logits)),
             0x78: (int(expected["margin_q"]) << 16) | int(expected["score_q15"]),
             0x7c: args.result_seq, 0x84: 4096}
    cop = MMIO(loader.COP_BASE, 0x1000)
    errors = []
    for round_index in range(args.rounds):
        for offset, wanted in words.items():
            actual = cop.read(offset)
            if actual != wanted and len(errors) < 20:
                errors.append({"round": round_index, "offset": hex(offset),
                               "expected": hex(wanted), "actual": hex(actual)})
    print(json.dumps({"reads": args.rounds * len(words), "first_errors": errors}, sort_keys=True))
    if errors:
        raise SystemExit(1)
    print("PASS: all distinct-address first reads match hardware case")


if __name__ == "__main__":
    main()
