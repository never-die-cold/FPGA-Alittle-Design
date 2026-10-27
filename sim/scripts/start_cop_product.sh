#!/usr/bin/env bash
# Persistent app/package paths; the HTTP service owns the board until stopped.
set -euo pipefail
package=$1
app=$2
run_root=$3
source /etc/profile.d/xrt_setup.sh
source /etc/profile.d/pynq_venv.sh
mkdir -p "$run_root"
if test -e "$run_root/service.pid"; then
    echo "Run directory already has a service PID; use a fresh directory" >&2
    exit 1
fi
nohup python3 -u "$app/src/pynq_host/cop_product_service.py" \
    --package "$package" --root "$run_root" --order "${4:-2,4,4}" \
    --background-mode local --color-threshold 20 --min-score 0.8 \
    >"$run_root/service.log" 2>&1 </dev/null &
printf '%s\n' "$!" >"$run_root/service.pid"
echo "PRODUCT_SERVICE_PID=$! LOG=$run_root/service.log"
