#!/usr/bin/env bash
set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 30d6fc34-e372-4b0e-b9de-e8f4617b40d6
previous=/home/xilinx/cop-live-fresh-20261027-r1
pid=$(cat "$previous/service.pid")
tr '\0' ' ' < "/proc/$pid/cmdline" | grep -F -- '--root /home/xilinx/cop-live-fresh-20261027-r1'
grep -q 'PRODUCT_SERVICE_READY' "$previous/service.log"
kill -TERM "$pid"
sleep 2
if ss -ltn | grep -q ':8765 '; then
    echo 'Previous server is still listening; no second loader started' >&2
    exit 1
fi
flock -n /home/xilinx/fpga-product.lock true
bash /home/xilinx/start_cop_product_20261027.sh \
    /home/xilinx/cop-pkg-product-20261027-r1 \
    /home/xilinx/cop-app-product-20261027-r1 \
    /home/xilinx/cop-live-fresh-20261027-r2 2,4,4
