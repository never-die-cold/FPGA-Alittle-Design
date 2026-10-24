"""Read-only PYNQ control-plane preflight for the C03 coprocessor.

Run this ON THE BOARD after the JL/NC bitstream is loaded.  It only reads
IP_ID/VERSION/CAPABILITY/STATUS/ERROR_CODE/RESULT_SEQ through a 4 KiB MMIO
window; it writes nothing and does not touch DMA.  It is intentionally not part
of the off-board gate (no pynq in CI).  A successful probe is NOT a board
acceptance; it only proves the PS can see the register window.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from cop_driver import CopError, PynqMmio, probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=lambda value: int(value, 0), required=True,
                        help="PS AXI base from Vivado Address Editor (not 0x8001_0000)")
    parser.add_argument("--length", type=lambda value: int(value, 0), default=0x1000,
                        help="MMIO window length (default 4 KiB)")
    args = parser.parse_args()
    try:
        from pynq import MMIO
    except ImportError:
        print("ERROR: pynq is not installed; run this on the PYNQ board", file=sys.stderr)
        return 2
    try:
        info = probe(PynqMmio(MMIO(args.base, args.length), args.base))
    except (CopError, OSError, ValueError) as error:
        print(f"ERROR: control-plane probe failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
