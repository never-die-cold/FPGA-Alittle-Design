#!/usr/bin/env bash
# Temporary sensor-power/test-pattern probes; restore both controls on exit.
set -uo pipefail
out=${1:?new project evidence directory required}
[[ "$out" = /home/edgesight/FPGA-Alittle-Design/data/logs/* ]] || exit 2
mkdir "$out" || exit 2
systemctl is-active --quiet pi-camera-preview.service && exit 2
sudo -n fuser -s /dev/video0
[[ "$?" = 1 ]] || { echo 'FAIL: camera not exclusively available'; exit 2; }
power=/sys/bus/i2c/devices/10-001a/power/control
previous_power=$(cat "$power") || exit 2
previous_pattern=$(v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern | awk '{print $2}')
[[ "$previous_power" = auto || "$previous_power" = on ]] || exit 2
[[ "$previous_pattern" =~ ^[0-4]$ ]] || exit 2
cleanup() {
    local restore_failed=0
    v4l2-ctl -d /dev/v4l-subdev0 --set-ctrl "test_pattern=$previous_pattern" || restore_failed=1
    printf '%s\n' "$previous_power" | sudo -n tee "$power" >/dev/null || restore_failed=1
    echo "RESTORE_FAILED=$restore_failed POWER=$previous_power PATTERN=$previous_pattern"
    [[ "$restore_failed" = 0 ]] || exit 2
}
trap cleanup EXIT
probe() {
    local name=$1 file=$2
    shift 2
    printf '%q ' "$@" > "$out/$name.command"
    printf '\n' >> "$out/$name.command"
    timeout -k 3s 10s "$@" > "$out/$name.log" 2>&1
    local result=$? bytes=0
    [[ ! -f "$file" ]] || bytes=$(stat -c %s "$file")
    echo "$name exit=$result bytes=$bytes"
    tail -n 3 "$out/$name.log"
    [[ "$result" = 0 && "$bytes" -gt 0 ]]
}
raw=(rpicam-raw --nopreview --mode 1536:864:10:P --framerate 30 --timeout 800
     --shutter 10000 --gain 1 --awbgains 1,1 --autofocus-mode manual)
probe raw30 "$out/raw30.raw" "${raw[@]}" -o "$out/raw30.raw" && exit 0
printf 'on\n' | sudo -n tee "$power" >/dev/null || exit 2
cat "$power" /sys/bus/i2c/devices/10-001a/power/runtime_status
probe power-on "$out/power-on.raw" "${raw[@]}" -o "$out/power-on.raw" && exit 0
v4l2-ctl -d /dev/v4l-subdev0 --set-ctrl test_pattern=2 || exit 2
v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern
if probe test-pattern "$out/test-pattern.raw" "${raw[@]}" -o "$out/test-pattern.raw"; then
    echo 'DIAGNOSTIC_ONLY: sensor test-pattern data received'; exit 3
fi
v4l2-ctl -d /dev/v4l-subdev0 --get-ctrl test_pattern
v4l2-ctl -d /dev/video0 --get-fmt-video > "$out/v4l-format.txt"
media-ctl -p -d /dev/media0 > "$out/media-graph.txt"
grep -Ei 'unicam|csi' /proc/interrupts > "$out/interrupts-before.txt" || true
if probe v4l-direct "$out/v4l-direct.raw" v4l2-ctl -d /dev/video0 --stream-mmap=3 \
    --stream-count=2 --stream-poll --stream-to="$out/v4l-direct.raw"; then
    echo 'DIAGNOSTIC_ONLY: direct V4L2 data received with test pattern'; exit 3
fi
grep -Ei 'unicam|csi' /proc/interrupts > "$out/interrupts-after.txt" || true
sudo -n dmesg | tail -n 35 > "$out/kernel-after.txt"
echo 'FAIL: no data after power-on, test-pattern and direct V4L2 probes'
exit 1
