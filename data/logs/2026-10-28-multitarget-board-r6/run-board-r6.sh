#!/usr/bin/env bash
set -euo pipefail
pkg=/home/xilinx/cop-pkg-r6-multitarget-20261028
app=/home/xilinx/cop-app-r6-20261028
vectors=/home/xilinx/cop-vectors-r6-20261028
evidence=/home/xilinx/cop-board-r6-20261028
py=/usr/local/share/pynq-venv/bin/python3
test "$(cat /proc/sys/kernel/random/boot_id)" = 30d6fc34-e372-4b0e-b9de-e8f4617b40d6
test ! -e "$evidence"
mkdir -p "$evidence"
tr '\0' ' ' </proc/2566/cmdline | tee "$evidence/previous-service.txt"
grep -q '/home/xilinx/cop-app-fresh-20261027-r2/src/pynq_host/cop_product_service.py' "$evidence/previous-service.txt"
curl -fsS http://127.0.0.1:8765/v1/status >"$evidence/previous-status.json"
kill -TERM 2566
for attempt in {1..100}; do
    if ! kill -0 2566 2>/dev/null; then break; fi
    sleep .1
done
if kill -0 2566 2>/dev/null; then echo 'previous service did not stop'; exit 1; fi
flock -n /home/xilinx/fpga-product.lock "$py" "$pkg/payload/tools/cop_board_fast_run.py" \
    --package "$pkg" --case roi_001 --measurement "$evidence/golden-roi_001.json" \
    2>&1 | tee "$evidence/golden-console.log"
for scene in mixed holdout; do
    "$py" "$app/sim/scripts/check_cnn_board_vectors.py" --package "$pkg" \
        --app-root "$app" --vectors "$vectors/$scene" --output "$evidence/$scene" \
        2>&1 | tee "$evidence/$scene-console.log"
done
echo BOARD_R6_NUMERIC_VALIDATION_PASS
