set -e
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
src=/home/xilinx/cop-pkg-imem-20261026
dst=/home/xilinx/cop-pkg-trained566b
rm -rf $dst
cp -r /home/xilinx/cop-pkg-gate566b $dst
cp $src/payload/pynq_cop_40mhz.bit $dst/payload/
cp $src/payload/pynq_cop_40mhz.hwh $dst/payload/
rm -f $dst/payload/pynq_cop_40mhz.xsa
sha256sum $dst/payload/pynq_cop_40mhz.bit
echo "=== trained roi_001 on proven bit ==="
cd $dst
python3 payload/tools/cop_board_fast_run.py --package . --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30 || echo "RUN_EXIT=$?"