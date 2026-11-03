#!/usr/bin/env bash
set -euo pipefail
pkg=/home/xilinx/cop-pkg-r6-multitarget-20261028-r1
app=/home/xilinx/cop-app-final-20261103-62324fe
root=/home/xilinx/cop-live-final-20261103-r1
py=/usr/local/share/pynq-venv/bin/python3
test "$(cat /proc/sys/kernel/random/boot_id)" = 89d82a5c-64cd-48d7-b8cf-51be273ccf62
test ! -e "$root"
if ss -lnt 'sport = :8765' | grep -q LISTEN; then
    echo 'port 8765 already has an owner'; exit 1
fi
flock -n /home/xilinx/fpga-product.lock true
echo "a929904866213f4133a6c12ee1a3dada0538ea99da6db89ab6f3fb6316807ce9  $pkg/payload/pynq_cop_40mhz.bit" | sha256sum -c -
echo "f01b96a3f9435b369595ef7bcdaaa32980213130df6b4e9a0f0ff622cd8c3527  $pkg/payload/pynq_cop_40mhz.hwh" | sha256sum -c -
mkdir "$root"
# Deliberately no --order: wait for an explicitly applied web work order.
nohup "$py" -u "$app/src/pynq_host/cop_product_service.py" --package "$pkg" \
    --root "$root" --background-mode local --color-threshold 25 --min-score .8 \
    >"$root/service.log" 2>&1 </dev/null &
service_pid=$!
echo "$service_pid" >"$root/service.pid"
for attempt in {1..60}; do
    if curl -fsS --max-time 1 http://127.0.0.1:8765/v1/status >"$root/status.json"; then
        cat "$root/status.json"; exit 0
    fi
    if ! kill -0 "$service_pid" 2>/dev/null; then cat "$root/service.log"; exit 1; fi
    sleep 1
done
cat "$root/service.log"
echo 'product service startup timed out'
exit 1
