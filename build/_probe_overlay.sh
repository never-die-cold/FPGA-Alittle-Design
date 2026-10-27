source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /tmp
for pkg in /home/xilinx/cop-pkg /home/xilinx/cop-pkg-imem-20261026 /home/xilinx/cop-pkg-gate566b; do
  echo "== $pkg"
  ls -l $pkg/payload/*.hwh 2>/dev/null | awk "{print \$5, \$9}"
  python3 - "$pkg/payload/pynq_cop_40mhz.bit" <<"EOF"
import sys
try:
    from pynq import Overlay
    ov = Overlay(sys.argv[1])
    print("OVERLAY_OK", ov.is_loaded())
except Exception as exc:
    print("OVERLAY_FAIL", type(exc).__name__, exc)
EOF
done