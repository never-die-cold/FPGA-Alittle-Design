source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /home/xilinx/cop-pkg-imem-20261026
echo "=== known-good package zero ==="
python3 payload/tools/cop_board_fast_run.py --package . --case zero --measurement /tmp/known-zero.json --timeout 30; echo "EXIT=$?"