#!/usr/bin/env bash
# Historical failed probe: do not run on the kernel where bind crashed.
set -uo pipefail
if [[ "$(uname -r)" = '6.18.50+rpt-rpi-v8' ]]; then
    echo 'BLOCKED: sensor rebind crashed on this kernel; use a clean reboot'
    exit 2
fi
out=${1:?new project evidence directory required}
[[ "$out" = /home/edgesight/FPGA-Alittle-Design/data/logs/* ]] || exit 2
mkdir "$out" || exit 2
systemctl is-active --quiet pi-camera-preview.service && exit 2
sudo -n fuser -s /dev/video0
[[ "$?" = 1 ]] || exit 2
driver=/sys/bus/i2c/drivers/imx708
[[ -L "$driver/10-001a" ]] || exit 2
cleanup() {
    if [[ ! -L "$driver/10-001a" ]]; then
        printf '10-001a\n' | sudo -n tee "$driver/bind" >/dev/null || {
            echo 'FAIL: sensor rebind failed; reboot required'; exit 2;
        }
    fi
    echo 'SENSOR_DRIVER_BOUND=1'
}
trap cleanup EXIT
printf '10-001a\n' | sudo -n tee "$driver/unbind" >/dev/null || exit 2
sleep 1
printf '10-001a\n' | sudo -n tee "$driver/bind" >/dev/null || exit 2
udevadm settle --timeout=5
rpicam-hello --list-cameras 2>&1 | tee "$out/cameras.txt"
media-ctl -p -d /dev/media0 > "$out/media-graph.txt"
timeout -k 3s 12s rpicam-still --nopreview --width 640 --height 480 \
    --timeout 1000 --output "$out/real-camera.jpg" > "$out/still.log" 2>&1
result=$?
bytes=0
[[ ! -f "$out/real-camera.jpg" ]] || bytes=$(stat -c %s "$out/real-camera.jpg")
tail -n 15 "$out/still.log"
sudo -n dmesg | tail -n 25 > "$out/kernel.txt"
echo "CAPTURE_EXIT=$result BYTES=$bytes"
if [[ "$result" = 0 && "$bytes" -gt 0 ]]; then
    echo 'PASS: camera JPEG received after sensor rebind'; exit 0
fi
echo 'FAIL: sensor rebind did not recover camera frames'
exit 1
