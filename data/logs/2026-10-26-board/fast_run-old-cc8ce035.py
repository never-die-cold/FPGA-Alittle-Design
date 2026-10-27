#!/usr/bin/env python3
"""Board-only fast path for the J08-lite coprocessor loader.

Why this exists:
- The packaged pynq_cop loader does preflight after the bitstream is loaded; the
  resident firmware's wait guard can expire while preflight reads 36 KB + HWH.
- The packaged loader writes dma_start high then low from Python; the high level
  can survive the CDC ack and retrigger, aborting the adapter's loading state.

This script is a board-only workaround, not a replacement for the RTL edge fix:
  1. run preflight (file/HWH/SHA) BEFORE resetting the PL;
  2. set FCLK1=40 then load the bitstream;
  3. emit the dma_start high/low pulse from a tiny C helper (two adjacent
     /dev/mem stores), then run the normal config/DMA/result path.

Run ON THE BOARD as root with the PYNQ venv:
  sudo -E /usr/local/share/pynq-venv/bin/python3 \
    sim/scripts/cop_board_fast_run.py \
    --package /home/xilinx/cop-pkg-imem-20261026 --case zero \
    --measurement /tmp/zero-fast.json
"""
import argparse
import os
import subprocess
import sys
import types

C_SOURCE = r"""#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    int kind = atoi(argv[1]) & 1;
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) return 3;
    volatile uint32_t *p = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE,
                                MAP_SHARED, fd, 0x40020000);
    if (p == MAP_FAILED) { close(fd); return 4; }
    uint32_t ctl = ((uint32_t)kind) << 1;
    p[0] = ctl | 1u;
    p[0] = ctl;
    __sync_synchronize();
    munmap((void *)p, 0x1000);
    close(fd);
    return 0;
}
"""


def build_helper(path="/tmp/cop_fast_start"):
    source = path + ".c"
    for candidate in (source, path):
        try:
            os.unlink(candidate)
        except FileNotFoundError:
            pass
    with open(source, "w", encoding="utf-8") as stream:
        stream.write(C_SOURCE)
    subprocess.run(["gcc", "-O2", "-Wall", "-o", path, source], check=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, help="board package root")
    parser.add_argument("--case", choices=("zero", "pattern"), required=True)
    parser.add_argument("--measurement", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--helper", default="/tmp/cop_fast_start")
    args = parser.parse_args()

    package = os.path.abspath(args.package)
    sys.path.insert(0, os.path.join(package, "payload", "tools"))
    import cop_payload_loader as loader
    from pynq import Clocks, Overlay

    # Slow file/HWH preflight BEFORE the PL reset starts the firmware guard.
    preflight = loader.preflight(package, args.case)
    helper = build_helper(args.helper)

    def fast_start(kind):
        result = subprocess.run([helper, str(kind)], check=False)
        if result.returncode != 0:
            raise loader.LoaderError("fast_start failed rc=%d" % result.returncode)

    def fast_send(dma, gpio, cop, buffer, length, kind, timeout):
        if length < 1 or length > loader.DMA_LENGTH_MAX:
            raise loader.LoaderError("DMA length does not fit 16-bit")
        if not gpio.read(loader.GPIO2_DATA) & 1:
            raise loader.LoaderError("start_ready is 0 before dma_start")
        gpio.write(loader.GPIO_TRI, 0)
        gpio.write(loader.GPIO2_TRI, 0xFFFFFFFF)
        fast_start(kind)
        loader.wait_for(
            lambda: loader.read_mask(cop, loader.REG["STATUS"], loader.STATUS["DMA_BUSY"]),
            timeout, "start request not accepted")
        buffer.flush()
        dma.write(loader.DMA_DMACR, 4)
        loader.wait_for(lambda: 1 if not dma.read(loader.DMA_DMACR) & 4 else None,
                        timeout, "AXI DMA reset timeout")
        dma.write(loader.DMA_DMACR, 1)
        dma.write(loader.DMA_SA, int(buffer.physical_address))
        dma.write(loader.DMA_LENGTH, length & loader.DMA_LENGTH_MAX)
        seen_payload_error = False

        def transfer_done():
            nonlocal seen_payload_error
            seen_payload_error |= bool(gpio.read(loader.GPIO2_DATA) & 2)
            status = dma.read(loader.DMA_DMASR)
            if status & 0x770:
                raise loader.LoaderError("AXI DMA MM2S error status=0x%08x" % status)
            return status if status & 2 else None

        transfer_status = loader.wait_for(transfer_done, timeout, "AXI DMA MM2S timeout")
        loader.wait_for(
            lambda: loader.read_mask(cop, loader.REG["STATUS"], loader.STATUS["DMA_BUSY"], False),
            timeout, "coprocessor DMA loader did not finish")
        gpio_status = gpio.read(loader.GPIO2_DATA)
        if seen_payload_error or gpio_status & 2:
            raise loader.LoaderError("payload_error observed")
        if not gpio_status & 1:
            raise loader.LoaderError("start_ready did not return")
        if cop.read(loader.REG["DMA_BYTES"]) != length:
            raise loader.LoaderError("DMA_BYTES differs from submitted byte count")
        return transfer_status

    loader.dma_send = fast_send
    Clocks.fclk1_mhz = 40.0
    overlay = Overlay(os.path.join(package, "payload", "pynq_cop_40mhz.bit"))
    loader.preflight = lambda pkg, case: preflight
    run_args = types.SimpleNamespace(package=package, case=args.case,
                                     measurement=args.measurement, timeout=args.timeout)
    loader.run_board(run_args)
    with open(args.measurement, "r", encoding="utf-8") as stream:
        print("MEASURED=" + stream.read().strip())
    return overlay


if __name__ == "__main__":
    main()
