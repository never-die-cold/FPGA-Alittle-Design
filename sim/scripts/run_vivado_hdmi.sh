#!/usr/bin/env bash
# 物理 HDMI 工程构建入口。证据目录可用 VISION_HDMI_EVDIR 覆盖——默认保持
# 2026-10-02 离板证据路径（当时 README 引用），但后续构建请显式指定自己的
# 日期目录，避免覆盖历史存证（2026-10-03 实测踩坑）。
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
VIV="${VISION_VIVADO_BIN:-/d/Vivado_downloads/2026.1/Vivado/bin}"
EVDIR="${VISION_HDMI_EVDIR:-data/logs/2026-10-02-vision-offboard/hdmi}"
mkdir -p "$EVDIR"
vision_run_checked "$EVDIR/driver.log" \
    "$VIV/vivado.bat" -mode batch -source sim/scripts/build_hdmi.tcl \
    -log "$EVDIR/vivado.log" \
    -journal "$EVDIR/vivado.jou"
