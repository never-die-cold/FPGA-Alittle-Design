source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /home/xilinx/cop-pkg-trained566b
python3 - <<"EOF"
from pynq import Overlay, MMIO
ov = Overlay("payload/pynq_cop_40mhz.bit", download=True)
print("loaded", ov.is_loaded())
cop = MMIO(0x40000000, 0x1000)
print("STATUS", hex(cop.read(0x00)))
print("DMA_BYTES", hex(cop.read(0x84)))
print("RESULT_SEQ", hex(cop.read(0x7C)))
EOF