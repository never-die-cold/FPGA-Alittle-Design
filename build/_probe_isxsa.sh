source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
echo "=== dir contents ==="
ls /home/xilinx/cop-pkg/payload/ /home/xilinx/cop-pkg-imem-20261026/payload/ /home/xilinx/cop-pkg-gate566b/payload/
echo "=== is_xsa source ==="
grep -n "def is_xsa" -A 8 /usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/pl_server/embedded_device.py