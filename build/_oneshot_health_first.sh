set -u
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
# 1) board health: the case that PASSED at 21:40
cd /home/xilinx/cop-pkg-imem-20261026
python3 payload/tools/cop_board_fast_run.py --package . --case zero --measurement /tmp/health-zero.json --timeout 30
echo "HEALTH_RC=$?"
# 2) trained payload, same proven bit
cd /home/xilinx/cop-pkg-trained566b
python3 payload/tools/cop_board_fast_run.py --package . --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30
echo "TRAINED_RC=$?"