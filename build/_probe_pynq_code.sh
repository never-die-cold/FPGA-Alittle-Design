echo "=== sizes ==="
ls -l /home/xilinx/cop-pkg/payload/pynq_cop_40mhz.bit /home/xilinx/cop-pkg-imem-20261026/payload/pynq_cop_40mhz.bit /home/xilinx/cop-pkg-gate566b/payload/pynq_cop_40mhz.bit | awk "{print \$5, \$9}"
echo "=== _get_bitstream_handler ==="
grep -n "_get_bitstream_handler" -A 25 /usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/pl_server/embedded_device.py | head -45
echo "=== get_parser ==="
sed -n "250,285p" /usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/pl_server/embedded_device.py