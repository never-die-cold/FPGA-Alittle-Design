set -u
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
run_case() {
  pkg=$1; case_name=$2; out=$3
  echo "=== $pkg :: $case_name"
  cd "$pkg" || return 1
  python3 payload/tools/cop_board_fast_run.py --package . --case "$case_name" --measurement "/tmp/$out.json" --timeout 30
  rc=$?
  echo "RC=$rc"
  return $rc
}
run_case /home/xilinx/cop-pkg-trained566b roi_001 trained-roi001 || { echo "STOP: trained roi_001 failed; do not retry, power cycle first"; exit 1; }
run_case /home/xilinx/cop-pkg-trained566b frame trained-frame || { echo "STOP: trained frame failed"; exit 2; }
run_case /home/xilinx/cop-pkg-imem-20261026 zero known-zero || { echo "STOP: known-good zero failed"; exit 3; }
echo "ALL DONE"