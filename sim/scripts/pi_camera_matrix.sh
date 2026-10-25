#!/usr/bin/env bash
# Exclusive, bounded camera diagnosis. Never changes boot configuration.
set -uo pipefail
out=${1:?new project evidence directory required}
[[ "$out" = /home/edgesight/FPGA-Alittle-Design/data/logs/* ]] || exit 2
mkdir "$out" || exit 2
if systemctl is-active --quiet pi-camera-preview.service; then
    echo 'FAIL: stop preview service before running matrix'; exit 2
fi
if pgrep -x rpicam-hello || pgrep -x rpicam-still || pgrep -x rpicam-raw; then
    echo 'FAIL: another camera process exists'; exit 2
fi
if [[ -e /dev/video0 ]]; then
    sudo -n fuser -s /dev/video0
    owner_rc=$?
    [[ "$owner_rc" = 1 ]] || { echo 'FAIL: exclusive access unconfirmed'; exit 2; }
fi
printf 'name,exit_code,bytes\n' > "$out/results.csv"
cat /proc/sys/kernel/random/boot_id > "$out/boot_id.txt"
rpicam-still --version > "$out/versions.txt" 2>&1
run_case() {
    local name=$1 file=$2
    shift 2
    printf '%q ' "$@" > "$out/$name.command"
    printf '\n' >> "$out/$name.command"
    timeout -k 3s 12s "$@" > "$out/$name.log" 2>&1
    local result=$? bytes=0
    [[ ! -f "$file" ]] || bytes=$(stat -c %s "$file")
    printf '%s,%s,%s\n' "$name" "$result" "$bytes" | tee -a "$out/results.csv"
    if [[ "$result" = 0 && "$bytes" -gt 0 ]]; then
        sha256sum "$file"
        echo "PASS: camera data captured: $name"
        return 0
    fi
    tail -n 3 "$out/$name.log"
    return 1
}
for mode in 1536:864:10:P 2304:1296:10:P 4608:2592:10:P; do
    tag=${mode//:/-}
    run_case "raw-$tag" "$out/raw-$tag.raw" rpicam-raw --nopreview \
        --mode "$mode" --framerate 2 --timeout 1000 --output "$out/raw-$tag.raw" && exit 0
done
run_case still-manual "$out/still-manual.jpg" rpicam-still --nopreview \
    --mode 1536:864:10:P --viewfinder-mode 1536:864:10:P --framerate 5 \
    --shutter 10000 --gain 1 --awbgains 1,1 --autofocus-mode manual \
    --denoise off --timeout 1000 --output "$out/still-manual.jpg" && exit 0
echo 'FAIL: no camera data in bounded RAW/manual matrix'
exit 1
