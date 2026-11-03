#!/usr/bin/env bash
set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 363593e1-df8a-4f71-b084-db461e04f1ee
old=/home/xilinx/cop-live-final-20261103-r2
app=/home/xilinx/cop-app-r9-20261103
pkg=/home/xilinx/cop-pkg-r9-20261103
root=/home/xilinx/cop-live-r9-20261103-r1
py=/usr/local/share/pynq-venv/bin/python3
test ! -e "$root"
pid=$(cat "$old/service.pid")
test "$pid" -gt 1
tr '\0' ' ' <"/proc/$pid/cmdline" | grep -F '/home/xilinx/cop-app-final-20261103-62324fe/src/pynq_host/cop_product_service.py'
# The PC proxy is stopped first. Wait for old requests to finish before stopping
# this exact verified process; do not release DMA buffers under an active job.
for i in {1..150}; do
    count=$(ss -tnH '( sport = :8765 )' | wc -l)
    if [ "$count" = 0 ]; then break; fi
    sleep .2
done
test "$(ss -tnH '( sport = :8765 )' | wc -l)" = 0
kill -TERM "$pid"
for i in {1..100}; do if ! kill -0 "$pid" 2>/dev/null; then break; fi; sleep .1; done
if kill -0 "$pid" 2>/dev/null; then echo 'old service did not exit'; exit 1; fi
mkdir "$root"
flock -n /home/xilinx/fpga-product.lock "$py" "$pkg/payload/tools/cop_board_fast_run.py" \
    --package "$pkg" --case roi_001 --measurement "$root/golden.json"
nohup "$py" -u "$app/src/pynq_host/cop_product_service.py" --package "$pkg" \
    --root "$root/live" --background-mode local-fast --color-threshold 25 --min-score .8 \
    >"$root/service.log" 2>&1 </dev/null &
service_pid=$!
echo "$service_pid" >"$root/service.pid"
for i in {1..60}; do
    if curl -fsS --max-time 1 http://127.0.0.1:8765/v1/status >"$root/status.json"; then cat "$root/status.json"; exit 0; fi
    if ! kill -0 "$service_pid" 2>/dev/null; then cat "$root/service.log"; exit 1; fi
    sleep 1
done
cat "$root/service.log"
exit 1
