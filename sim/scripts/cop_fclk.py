"""Read Zynq-7000 FCLK registers; changes require the matching HWH clock plan.

The current MMCM design expects FCLK1 ~142.857 MHz, then generates 40 MHz.
Use cop_payload_loader for overlay initialization. This diagnostic never
assumes that the cop compute frequency equals its PS input frequency.
"""
import argparse
import json
import os
import sys
from pathlib import Path

SLCR_BASE = 0xF800_0000
SLCR_LENGTH = 0x1000
SLCR_DUMP_OFFSETS = {
    "io_pll_ctrl_0x108": 0x108, "fpga_clk_ctrl_0x170": 0x170,
    "fpga1_clk_ctrl_0x180": 0x180, "fpga2_clk_ctrl_0x190": 0x190,
    "fpga3_clk_ctrl_0x1A0": 0x1A0,
}
MHZ_TOLERANCE = 0.05


def _require_env():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        raise EnvironmentError("run as root (sudo); Clocks/MMIO write /dev/mem")
    try:
        from pynq import Clocks, MMIO
    except ImportError as error:
        raise EnvironmentError(
            "pynq is not installed; run with the board venv python "
            "/usr/local/share/pynq-venv/bin/python3") from error
    return Clocks, MMIO


def fclk_json(clocks, slcr):
    report = {f"fclk{i}_mhz": round(float(getattr(clocks, f"fclk{i}_mhz")), 6)
              for i in range(4)}
    report["slcr"] = {name: f"0x{slcr.read(offset):08x}"
                      for name, offset in SLCR_DUMP_OFFSETS.items()}
    return report


def cmd_status(_args):
    clocks, MMIO = _require_env()
    slcr = MMIO(SLCR_BASE, SLCR_LENGTH)
    print(json.dumps(fclk_json(clocks, slcr), indent=2, sort_keys=True))
    return 0


def cmd_set(args):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"tools"))
    from cop_payload_loader import hwh_clock_plan
    topology, expected = hwh_clock_plan(args.hwh)
    if args.clk != 1 or abs(args.mhz-expected) > MHZ_TOLERANCE:
        raise EnvironmentError(f"{topology} HWH requires FCLK1={expected:g} MHz; request rejected")
    clocks, MMIO = _require_env()
    slcr = MMIO(SLCR_BASE, SLCR_LENGTH)
    name = f"fclk{args.clk}_mhz"
    before = float(getattr(clocks, name))
    report = {"clk": args.clk, "target_mhz": args.mhz,
              "before_mhz": round(before, 6)}
    if abs(before - args.mhz) <= MHZ_TOLERANCE:
        report["action"] = "already_at_target"
    else:
        setattr(clocks, name, float(args.mhz))
        report["action"] = "set"
    after = float(getattr(clocks, name))
    report["after_mhz"] = round(after, 6)
    report["in_spec"] = abs(after - args.mhz) <= MHZ_TOLERANCE
    report.update(fclk_json(clocks, slcr))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["in_spec"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    status_cmd = sub.add_parser("status", help="read all FCLKs + raw SLCR words")
    status_cmd.set_defaults(func=cmd_status)
    set_cmd = sub.add_parser("set", help="set one FCLK and verify")
    set_cmd.add_argument("--clk", type=int, choices=(1,), default=1)
    set_cmd.add_argument("--hwh", type=Path, required=True, help="matching overlay HWH")
    set_cmd.add_argument("--mhz", type=float, required=True)
    set_cmd.set_defaults(func=cmd_set)
    args = parser.parse_args()
    try:
        return args.func(args)
    except EnvironmentError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
