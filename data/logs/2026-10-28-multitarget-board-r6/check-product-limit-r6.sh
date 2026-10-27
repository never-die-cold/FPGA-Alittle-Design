#!/usr/bin/env bash
set -euo pipefail
pkg=/home/xilinx/cop-pkg-r6-multitarget-20261028-r1
app=/home/xilinx/cop-app-r6-20261028
vectors=/home/xilinx/cop-vectors-r6-20261028
evidence=/home/xilinx/cop-board-r6-20261028-r2
py=/usr/local/share/pynq-venv/bin/python3
test "$(cat /proc/sys/kernel/random/boot_id)" = 30d6fc34-e372-4b0e-b9de-e8f4617b40d6
if ss -lnt 'sport = :8765' | grep -q LISTEN; then exit 1; fi
test ! -e "$evidence"
mkdir -p "$evidence"
for scene in mixed holdout; do
    "$py" "$app/sim/scripts/check_cnn_board_vectors.py" --package "$pkg" \
        --app-root "$app" --vectors "$vectors/$scene" --output "$evidence/$scene" \
        2>&1 | tee "$evidence/$scene-console.log"
done
echo BOARD_R6_PRODUCT_LIMIT_VALIDATION_PASS
