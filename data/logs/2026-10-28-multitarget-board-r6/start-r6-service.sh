#!/usr/bin/env bash
set -euo pipefail
pkg=/home/xilinx/cop-pkg-r6-multitarget-20261028-r1
app=/home/xilinx/cop-app-r6-20261028
root=/home/xilinx/cop-live-r6-20261028
py=/usr/local/share/pynq-venv/bin/python3
if ss -lnt 'sport = :8765' | grep -q LISTEN; then
    echo 'port 8765 already has an owner'; exit 1
fi
test ! -e "$root"
mkdir -p "$root"
nohup "$py" -u "$app/src/pynq_host/cop_product_service.py" --package "$pkg" \
    --root "$root" --order 3,3,3 --background-mode local --color-threshold 25 \
    --min-score .8 >"$root/service.log" 2>&1 </dev/null &
service_pid=$!
echo "$service_pid" >"$root/service.pid"
for attempt in {1..45}; do
    if curl -fsS --max-time 1 http://127.0.0.1:8765/v1/status >"$root/status.json"; then
        cat "$root/status.json"; exit 0
    fi
    if ! kill -0 "$service_pid" 2>/dev/null; then
        cat "$root/service.log"; exit 1
    fi
    sleep 1
done
cat "$root/service.log"
echo 'product service startup timed out'
exit 1
