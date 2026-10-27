source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /tmp
python3 - <<"EOF"
from pynq import Overlay, MMIO
dma = MMIO(0x40010000, 0x10000)
print("before DMACR", hex(dma.read(0x00)))
Overlay("/home/xilinx/cop-pkg-gate566b/payload/pynq_cop_40mhz.bit", download=True)
print("after gate566b DMACR", hex(dma.read(0x00)), "DMASR", hex(dma.read(0x04)))
Overlay("/home/xilinx/cop-pkg-trained566b/payload/pynq_cop_40mhz.bit", download=True)
print("after trained DMACR", hex(dma.read(0x00)), "DMASR", hex(dma.read(0x04)))
EOF