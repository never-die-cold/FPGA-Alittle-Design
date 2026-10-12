"""Stop the known base VDMA without reprogramming or allocating video frames."""
import time
from pathlib import Path
from pynq import MMIO, PL

print("CURRENT_BIT:", PL.bitfile_name, flush=True)
if not PL.bitfile_name or Path(PL.bitfile_name).name != "base.bit":
    raise RuntimeError("base configuration identity unconfirmed; do not touch DMA")
matches = [entry for name, entry in PL.ip_dict.items() if "axi_vdma" in name]
if len(matches) != 1 or matches[0]["phys_addr"] != 0x43000000:
    raise RuntimeError("base VDMA address differs from verified HWH")
dma = MMIO(0x43000000, 0x10000)
print("BEFORE:", hex(dma.read(0x04)), hex(dma.read(0x34)), flush=True)
dma.write(0x00, 0x00011080)
dma.write(0x30, 0x00011080)
deadline = time.monotonic() + 3
while time.monotonic() < deadline:
    if dma.read(0x04) & 1 and dma.read(0x34) & 1:
        break
    time.sleep(0.01)
else:
    raise TimeoutError("VDMA halt unconfirmed; require reboot before reprogramming")
print("AFTER:", hex(dma.read(0x04)), hex(dma.read(0x34)), flush=True)
print("PASS: both VDMA channels halted; no video buffers allocated", flush=True)
