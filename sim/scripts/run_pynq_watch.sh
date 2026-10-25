#!/usr/bin/env bash
# Board-side persistent evidence runner; does not load an overlay or stop services.
set -uo pipefail
seconds=${1:?seconds required}
watch_script=${2:?absolute onboard_smoke.py path required}
log=${3:?new absolute log path required}
[[ "$seconds" =~ ^[1-9][0-9]*$ ]] && (( seconds <= 3600 )) || exit 2
[[ "$watch_script" = /home/xilinx/vision_m2/c01-*/onboard_smoke.py ]] || exit 2
[[ "$log" = /home/xilinx/vision_m2/c01-*/*.log ]] || exit 2
[[ -f "$watch_script" && ! -e "$log" ]] || exit 2
set -o noclobber
exec >"$log" 2>&1
printf 'WATCH_STARTED_UTC=%s\n' "$(date -u +%FT%TZ)"
printf 'BOOT_ID_BEFORE=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
sha256sum "$watch_script" /home/xilinx/vision_m2/vision_regs.py
source /etc/profile.d/xrt_setup.sh || exit 2
source /etc/profile.d/pynq_venv.sh || exit 2
export PYTHONPATH=/home/xilinx/vision_m2
timeout -k 5s "$((seconds + 20))s" python3 -u "$watch_script" watch "$seconds"
result=$?
printf 'WATCH_EXIT_CODE=%s\n' "$result"
printf 'BOOT_ID_AFTER=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
printf 'WATCH_FINISHED_UTC=%s\n' "$(date -u +%FT%TZ)"
exit "$result"
