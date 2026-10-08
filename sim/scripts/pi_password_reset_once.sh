#!/bin/bash
# Run once as root via systemd.run; restore the original boot command line.
set -euo pipefail
boot=/boot/firmware
test -f "$boot/pi-password-reset-backup/cmdline.txt"
mount -o remount,rw /
mount -o remount,rw "$boot"
exec >>"$boot/pi-password-reset.log" 2>&1
cleanup() {
    status=$?
    trap - EXIT
    cp "$boot/pi-password-reset-backup/cmdline.txt" "$boot/cmdline.txt"
    if [ "$status" -eq 0 ]; then
        printf 'PASS: pi and edgesight passwords applied; boot parameters restored\n'
        rm -- "$boot/pi-password-reset.sh" "$boot/pi-password-reset.hashes"
    else
        printf 'FAIL: password reset exited %s; boot parameters restored\n' "$status"
    fi
    sync
    exit "$status"
}
trap cleanup EXIT
for name in pi edgesight; do
    if ! getent passwd "$name" >/dev/null; then
        useradd -m -s /bin/bash "$name"
    fi
done
chpasswd -e <"$boot/pi-password-reset.hashes"
systemctl enable ssh
