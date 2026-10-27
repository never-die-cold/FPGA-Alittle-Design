#!/usr/bin/env python3
"""Read cop/DMA diagnostics only when the requested overlay is still loaded."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    sys.path.insert(0, str(package / "payload/tools"))
    import cop_payload_loader as loader
    import pynq.pl_server.embedded_device
    from pynq import Clocks, MMIO, PL

    bit = package / "payload/pynq_cop_40mhz.bit"
    if not PL.bitfile_name or Path(PL.bitfile_name).resolve() != bit:
        raise SystemExit("requested cop overlay is not loaded; no PL MMIO read")
    _, expected = loader.hwh_clock_plan(bit.with_suffix(".hwh"))
    if abs(float(Clocks.fclk1_mhz) - expected) > 0.001:
        raise SystemExit("FCLK1 differs from HWH; no PL MMIO read")
    cop = MMIO(loader.COP_BASE, 0x1000)
    dma = MMIO(loader.DMA_BASE, 0x10000)
    gpio = MMIO(loader.GPIO_BASE, 0x10000)
    snapshot = {"cop": loader.firmware_snapshot(cop),
                "dma": {name: f"0x{dma.read(offset):08x}" for name, offset in
                        (("DMACR", 0), ("DMASR", 4), ("SA", 0x18), ("LENGTH", 0x28))},
                "gpio": {name: f"0x{gpio.read(offset):08x}" for name, offset in
                         (("DATA", 0), ("TRI", 4), ("DATA2", 8), ("TRI2", 12))}}
    print(json.dumps(snapshot, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
