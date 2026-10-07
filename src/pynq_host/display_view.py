#!/usr/bin/env python3
"""Switch FPGA HDMI diagnostics without reloading the overlay.

Requires the diagnostic bit/hwh, active 720p60 input and root MMIO access.
Example: python3 display_view.py --view edge
"""
import argparse
import json
import math
from vision_regs import VisionRegs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--view", choices=("color", "gray", "gauss", "edge"))
    group.add_argument("--status", action="store_true")
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be finite and positive")
    try:
        regs = VisionRegs(base=0x40000000)
        if args.view:
            regs.set_display_view(args.view)
            config_id = regs.commit(timeout=args.timeout)
            print(f"PASS: display={args.view.upper()} applied_config_id={config_id}")
        print(json.dumps({"staged_view": regs.get_display_view(),
                          "staged_R0": regs.read_reg(0), **regs.status()}))
    except (RuntimeError, TimeoutError, OSError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
