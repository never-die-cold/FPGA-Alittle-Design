source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /home/xilinx/cop-pkg-trained566b
grep -n "def download" -A 12 /usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/overlay.py | head -20
echo "=== dma regs ==="
python3 - <<"EOF"
from pynq import MMIO
dma = MMIO(0x40010000, 0x10000)
print("DMACR", hex(dma.read(0x00)))
print("DMASR", hex(dma.read(0x04)))
print("DMASA", hex(dma.read(0x18)))
print("DMALEN", hex(dma.read(0x28)))
EOF