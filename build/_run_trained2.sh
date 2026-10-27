set -e
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
src=/home/xilinx/cop-pkg-imem-20261026
dst=/home/xilinx/cop-pkg-trained566b
cp $src/payload/pynq_cop_40mhz.bit $dst/payload/
cp $src/payload/pynq_cop_40mhz.hwh $dst/payload/
rm -f $dst/payload/pynq_cop_40mhz.xsa
ls $dst/golden
cd $dst
python3 payload/tools/cop_board_fast_run.py --package . --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30