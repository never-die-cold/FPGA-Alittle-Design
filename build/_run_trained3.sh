source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
cd /home/xilinx/cop-pkg-trained566b
python3 payload/tools/cop_board_fast_run.py --package . --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30; echo "EXIT=$?"