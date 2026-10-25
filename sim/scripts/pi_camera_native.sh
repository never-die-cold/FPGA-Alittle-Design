#!/usr/bin/env bash
# Native CSI capture with a verified sensor test pattern; no libcamera owner.
set -uo pipefail
out=${1:?new project evidence directory required}
[[ "$out" = /home/edgesight/FPGA-Alittle-Design/data/logs/* ]] || exit 2
mkdir "$out" || exit 2
systemctl is-active --quiet pi-camera-preview.service && exit 2
sudo -n fuser -s /dev/video0
[[ "$?" = 1 ]] || exit 2
power=/sys/bus/i2c/devices/10-001a/power/control
previous_power=$(cat "$power") || exit 2
debug=/sys/module/bcm2835_unicam_legacy/parameters/debug
previous_debug=$(cat "$debug") || exit 2
previous_pattern=$(v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern | awk '{print $2}')
[[ "$previous_power" = auto || "$previous_power" = on ]] || exit 2
[[ "$previous_pattern" =~ ^[0-4]$ ]] || exit 2
[[ "$previous_debug" =~ ^[0-3]$ ]] || exit 2
cleanup() {
    local result=0
    v4l2-ctl -d /dev/v4l-subdev0 --set-ctrl "test_pattern=$previous_pattern" || result=1
    printf '%s\n' "$previous_power" | sudo -n tee "$power" >/dev/null || result=1
    printf '%s\n' "$previous_debug" | sudo -n tee "$debug" >/dev/null || result=1
    echo "RESTORE_FAILED=$result"
    [[ "$result" = 0 ]] || exit 2
}
trap cleanup EXIT
printf 'on\n' | sudo -n tee "$power" >/dev/null || exit 2
printf '3\n' | sudo -n tee "$debug" >/dev/null || exit 2
v4l2-ctl -d /dev/v4l-subdev0 --set-ctrl test_pattern=2 || exit 2
media-ctl -p -d /dev/media0 > "$out/media-graph.txt"
v4l2-ctl -d /dev/video0 --get-fmt-video > "$out/format.txt"
grep -Ei 'unicam|csi' /proc/interrupts > "$out/interrupts-before.txt" || true
v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern | tee "$out/pattern-before.txt"
timeout -k 3s 8s v4l2-ctl -d /dev/video0 --verbose --stream-mmap=3 \
    --stream-count=2 --stream-poll --stream-to="$out/diagnostic.raw" > "$out/capture.log" 2>&1 &
capture_pid=$!
sleep 0.4
v4l2-ctl -d /dev/video0 --log-status > "$out/live-status.txt" 2>&1
wait "$capture_pid"
result=$?
bytes=0
[[ ! -f "$out/diagnostic.raw" ]] || bytes=$(stat -c %s "$out/diagnostic.raw")
v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern | tee "$out/pattern-after.txt"
grep -Ei 'unicam|csi' /proc/interrupts > "$out/interrupts-after.txt" || true
sudo -n dmesg | tail -n 20 > "$out/kernel.txt"
cat "$out/capture.log" "$out/interrupts-before.txt" "$out/interrupts-after.txt"
echo "CAPTURE_EXIT=$result BYTES=$bytes"
if [[ "$result" = 0 && "$bytes" -gt 0 ]]; then
    echo 'PASS: diagnostic sensor pattern received; real camera image still unverified'
    exit 0
fi
echo 'FAIL: no native CSI test-pattern frames'
exit 1
