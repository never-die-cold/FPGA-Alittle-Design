#!/usr/bin/env bash
set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 30d6fc34-e372-4b0e-b9de-e8f4617b40d6
app=/home/xilinx/cop-app-fresh-20261027-r2
(cd "$app" && sha256sum -c SHA256SUMS)
pid=$(cat /home/xilinx/cop-live-fresh-20261027-r2/service.pid)
tr '\0' ' ' < "/proc/$pid/cmdline" | grep -F -- '--root /home/xilinx/cop-live-fresh-20261027-r2'
kill -TERM "$pid"
sleep 2
if ss -ltn | grep -q ':8765 '; then exit 1; fi
flock -n /home/xilinx/fpga-product.lock true
# Counts configure only the application checker; collection/comparison do not use its verdict.
bash "$app/sim/scripts/start_cop_product.sh" \
    /home/xilinx/cop-pkg-product-20261027-r1 "$app" \
    /home/xilinx/cop-live-data-20261027-r1 3,3,3
