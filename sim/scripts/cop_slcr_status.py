#!/usr/bin/env python3
"""Read Zynq-7000 PS clock/reset registers without writing or touching PL MMIO."""
import json
import mmap
import os
import struct


def main():
    fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
    try:
        with mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ,
                       offset=0xF8000000) as page:
            registers = {name: struct.unpack_from("<I", page, offset)[0]
                         for name, offset in (("FPGA0_CLK_CTRL", 0x170),
                                              ("FPGA1_CLK_CTRL", 0x180),
                                              ("FPGA2_CLK_CTRL", 0x190),
                                              ("FPGA3_CLK_CTRL", 0x1A0),
                                              ("FPGA_RST_CTRL", 0x240),
                                              ("LVL_SHFTR_EN", 0x900))}
        print(json.dumps({name: f"0x{value:08x}" for name, value in registers.items()},
                         indent=2, sort_keys=True))
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
