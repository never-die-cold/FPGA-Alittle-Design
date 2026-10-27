#!/usr/bin/env bash
set -euo pipefail
expected_boot=30d6fc34-e372-4b0e-b9de-e8f4617b40d6
test "$(cat /proc/sys/kernel/random/boot_id)" = "$expected_boot"
test "$(systemctl show bootpy.service -p ActiveState --value)" = inactive
test "$(systemctl show bootpy.service -p ExecMainStatus --value)" = 0
systemctl is-active --quiet fpga-vision-boot.service
if ss -ltn | grep -q ':8765 '; then
    echo 'Port 8765 already has an owner; leaving current service unchanged' >&2
    exit 1
fi
package=/home/xilinx/cop-pkg-product-20261027-r1
app=/home/xilinx/cop-app-product-20261027-r1
run_root=/home/xilinx/cop-live-fresh-20261027-r1
test ! -e "$run_root/service.pid"
mkdir -p "$run_root"
(cd "$package" && sha256sum -c SHA256SUMS) > "$run_root/package-check.log"
(cd "$app" && sha256sum -c SHA256SUMS) > "$run_root/app-check.log"
echo 'PACKAGE_AND_APP_SHA256_PASS'
systemctl stop fpga-vision-boot.service
bash "$app/sim/scripts/start_cop_product.sh" "$package" "$app" "$run_root" 2,4,4
