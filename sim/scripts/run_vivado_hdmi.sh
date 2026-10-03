#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
VIV="${VISION_VIVADO_BIN:-/d/Vivado_downloads/2026.1/Vivado/bin}"
mkdir -p data/logs/2026-10-02-vision-offboard/hdmi
vision_run_checked data/logs/2026-10-02-vision-offboard/hdmi/driver.log \
    "$VIV/vivado.bat" -mode batch -source sim/scripts/build_hdmi.tcl \
    -log data/logs/2026-10-02-vision-offboard/hdmi/vivado.log \
    -journal data/logs/2026-10-02-vision-offboard/hdmi/vivado.jou
