#!/usr/bin/env bash
# Run on PYNQ as root; preserve IP setup and back up before changing startup.
set -euo pipefail
backup=${1:?usage: install_pynq_vision_boot.sh /home/xilinx/fpga-startup-backups/RUN}
cron=/etc/cron.d/pynq-live
unit=/etc/systemd/system/fpga-vision-boot.service
runner=/home/xilinx/vision_m2/pynq_vision_boot.py
source_dir=$(cd -- "$(dirname -- "$0")" && pwd)
[[ $EUID -eq 0 ]] || { echo 'root required' >&2; exit 1; }
[[ $backup == /home/xilinx/fpga-startup-backups/* && ! -e $backup ]]
[[ -f $cron && ! -e $unit && ! -e $runner ]]
[[ $(grep -Ec 'm2_onboard\.py load|park_live_server_v7\.py' "$cron") == 2 ]]
systemctl cat bootpy.service >/dev/null
mkdir -p -- "$backup"
cp -a -- "$cron" "$backup/pynq-live"
systemctl cat bootpy.service > "$backup/bootpy.service.txt"
sha256sum "$cron" "$source_dir/fpga-vision-boot.service" > "$backup/SHA256SUMS.before"
awk '!/m2_onboard\.py load|park_live_server_v7\.py/' "$cron" > "$backup/pynq-live.filtered"
grep -Fxq '@reboot root ip addr add 192.168.50.99/24 dev eth0' "$backup/pynq-live.filtered"
rollback() {
    trap - ERR
    set +e
    cp -a -- "$backup/pynq-live" "$cron"
    systemctl disable --now fpga-vision-boot.service
    rm -f -- "$unit" "$runner"
    systemctl daemon-reload
    echo "INSTALL FAILED; startup configuration restored from $backup" >&2
}
trap rollback ERR
install -m 0644 -- "$source_dir/fpga-vision-boot.service" "$unit"
install -m 0644 -- "$source_dir/pynq_vision_boot.py" "$runner"
install -m 0644 -- "$backup/pynq-live.filtered" "$cron"
systemctl daemon-reload
[[ $(systemctl show fpga-vision-boot.service -p LoadState --value) == loaded ]]
systemctl enable --now fpga-vision-boot.service
systemctl is-enabled fpga-vision-boot.service
systemctl is-active fpga-vision-boot.service
sha256sum "$cron" "$unit" > "$backup/SHA256SUMS.after"
trap - ERR
echo "STARTUP_INSTALL_PASS backup=$backup"
