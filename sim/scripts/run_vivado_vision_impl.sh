#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
VIV="${VISION_VIVADO_BIN:-/d/Vivado_downloads/2026.1/Vivado/bin}"
mkdir -p data/logs/2026-10-02-vision-offboard/route
vision_run_checked data/logs/2026-10-02-vision-offboard/route/driver.log \
    "$VIV/vivado.bat" -mode batch -source sim/scripts/impl_vision.tcl \
    -log data/logs/2026-10-02-vision-offboard/route/vivado.log \
    -journal data/logs/2026-10-02-vision-offboard/route/vivado.jou
