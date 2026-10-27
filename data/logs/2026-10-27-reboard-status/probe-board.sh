#!/bin/bash
set -eu
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
python3 - <<'PY'
import hashlib
import json
import time
from pathlib import Path
from pynq import PL, MMIO, Clocks

print('current_bitfile:', PL.bitfile_name)
print('ip_dict:', json.dumps(PL.ip_dict, default=str))
print('fclk_mhz:', [getattr(Clocks, 'fclk%d_mhz' % n) for n in range(4)])
expected = Path('/home/xilinx/vision_m2/vision.bit')
print('vision_bit_sha256:', hashlib.sha256(expected.read_bytes()).hexdigest())
if PL.bitfile_name and Path(PL.bitfile_name).resolve() == expected:
    # The current boot journal identifies this overlay's pipe at this address.
    pipe = PL.ip_dict.get('pipe', {})
    if pipe.get('phys_addr') == 0x40000000:
        mmio = MMIO(0x40000000, 128)
        for _ in range(3):
            print('vision_read_only:', {str(i): mmio.read(i * 4) for i in (0, 11, 12)})
            time.sleep(1)
    else:
        print('no MMIO: pipe address is not the expected vision mapping')
else:
    print('no MMIO: current overlay is not the expected vision overlay')
PY
