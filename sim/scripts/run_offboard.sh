#!/usr/bin/env bash
# Final off-board checks. all needs MSYS2 make/RISC-V tools and a fetched arch suite.
# software does not rerun unchanged RTL/CoreMark. No board access occurs here.
set -euo pipefail
cd "$(dirname "$0")/../.."
MODE="${1:-all}"
PY="${VISION_PYTHON:-python}"
case "$MODE" in all|software) ;; *) echo "usage: $0 [all|software]" >&2; exit 2 ;; esac
if [ "$MODE" = all ]; then
    bash sim/scripts/run_iverilog.sh all
    bash sim/scripts/run_iverilog.sh v1_flow
    bash sim/scripts/run_iverilog.sh bht_flow_2
    bash sim/scripts/run_coprocessor_iverilog.sh bram_network
    bash sim/scripts/run_coprocessor_iverilog.sh watchdog
    bash board/smoke_test/sim/run_iverilog.sh
    export ARCH_TEST_LOG_DIR="${ARCH_TEST_LOG_DIR:-$PWD/sim/build/offboard-arch-$(date +%Y%m%d-%H%M%S)}"
    bash sim/scripts/run_arch_test_matrix.sh
else
    bash sim/scripts/run_vision_python.sh
    bash sim/scripts/run_coprocessor_python.sh all
fi
bash sim/scripts/run_inspection_python.sh
for name in class_aware_metrics localization_data n03_board_capture n03_buffer_lifecycle \
            web_server live_service_guards release_tools work_order_live; do
    "$PY" "sim/vision/test_$name.py"
done
"$PY" sim/tools/test_verify_rv32i.py
node --test sim/vision/test_web_protocol.mjs sim/vision/test_web_refresh.mjs
"$PY" sim/scripts/check_repo_hygiene.py
git diff --check
echo "PASS: offboard $MODE"
