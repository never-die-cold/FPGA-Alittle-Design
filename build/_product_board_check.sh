set -u
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
PKG=/home/xilinx/cop-pkg-product
cd $PKG || exit 2
echo "=== health: zero via fast runner"
python3 payload/tools/cop_board_fast_run.py --package . --case zero --measurement /tmp/product-zero.json --timeout 30; echo "ZERO_RC=$?"
echo "=== real image round (driver + engine)"
python3 sim/scripts/cop_hw_round.py --package $PKG --image /home/xilinx/frame.png --round-dir /home/xilinx/round-001 --order 3,2,1 2>&1 | tail -40; echo "ROUND_RC=$?"