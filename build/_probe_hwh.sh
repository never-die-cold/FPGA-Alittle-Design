source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /tmp
python3 - <<"EOF"
from pynq.pl_server.embedded_device import _get_bitstream_handler
pkgs = ["/home/xilinx/cop-pkg", "/home/xilinx/cop-pkg-imem-20261026", "/home/xilinx/cop-pkg-gate566b"]
for pkg in pkgs:
    bit = pkg + "/payload/pynq_cop_40mhz.bit"
    try:
        h = _get_bitstream_handler(bit)
        data = h.get_hwh_data()
        print(pkg.split("/")[-1], "handler", type(h).__name__, "hwh", None if data is None else len(data))
    except Exception as exc:
        print(pkg.split("/")[-1], "ERR", type(exc).__name__, str(exc)[:120])
EOF
echo "=== our hwh head ==="
head -c 200 /home/xilinx/cop-pkg-gate566b/payload/pynq_cop_40mhz.hwh; echo
echo "=== old hwh head ==="
head -c 200 /home/xilinx/cop-pkg-imem-20261026/payload/pynq_cop_40mhz.hwh; echo