#!/usr/bin/env bash
set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 363593e1-df8a-4f71-b084-db461e04f1ee
old=/home/xilinx/cop-live-r9-20261103-r1
app=/home/xilinx/cop-app-filming-guard-20261103
pkg=/home/xilinx/cop-pkg-r9-20261103
root=/home/xilinx/cop-live-filming-guard-20261103
py=/usr/local/share/pynq-venv/bin/python3
test ! -e "$root"
pid=$(cat "$old/service.pid")
test "$pid" -gt 1
tr '\0' ' ' <"/proc/$pid/cmdline" | grep -F '/home/xilinx/cop-app-r9-20261103/src/pynq_host/cop_product_service.py'
for i in {1..200}; do
    if [ "$(ss -tnH '( sport = :8765 )' | wc -l)" = 0 ]; then break; fi
    sleep .2
done
test "$(ss -tnH '( sport = :8765 )' | wc -l)" = 0
"$py" - <<'PY'
import time
import pynq.pl_server.embedded_device
from pynq import MMIO
vdma=MMIO(0x43000000,0x10000)
assert vdma.read(0x34)&1, 'capture DMA is still active; do not free its buffers'
dma=MMIO(0x40010000,0x10000)
dma.write(0,4)
for _ in range(1000):
    if not dma.read(0)&4: break
    time.sleep(.001)
assert not dma.read(0)&4 and dma.read(4)&1, 'MM2S reset/halt unconfirmed'
print('PASS: no HTTP job; capture halted; MM2S reset/halt confirmed')
PY
kill -TERM "$pid"
for i in {1..100}; do if ! kill -0 "$pid" 2>/dev/null; then break; fi; sleep .1; done
if kill -0 "$pid" 2>/dev/null; then exit 1; fi
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
