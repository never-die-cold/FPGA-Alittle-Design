#!/usr/bin/env bash
# 模块二 OOC 综合一键入口（不上板）：逐模块综合，产出资源/时序基线报告
# 用法：bash sim/scripts/run_vivado_vision_ooc.sh [unit|real|both]
#   unit（默认）：单元级参数（第一批基线）
#   real：720p 行宽参数（WIDTH=1280/HEIGHT=720，scaler 目标 224x224）
# 前置：Vivado 2026.1 安装于 D:/Vivado_downloads/2026.1（如路径不同请修改 VIVADO）
set -u
VIVADO="/d/Vivado_downloads/2026.1/Vivado/bin/vivado.bat"
VARIANT="${1:-unit}"
cd "$(dirname "$0")/../.."    # -> 仓库根
mkdir -p build/reports/vision_ooc

case "$VARIANT" in
    unit)  MODS="rgb2gray gaussian_3x3 sobel scaler" ;;
    real)  MODS="line_buffer gaussian_3x3 sobel scaler" ;;
    both)  MODS="rgb2gray line_buffer gaussian_3x3 sobel scaler" ;;
    *)     echo "用法: bash run_vivado_vision_ooc.sh [unit|real|both]"; exit 1 ;;
esac

for m in $MODS; do
    echo "== OOC synth: $m ($VARIANT) =="
    "$VIVADO" -mode batch -source sim/scripts/synth_vision_ooc.tcl -tclargs "$m" "$VARIANT" \
        -log  build/reports/vision_ooc/${m}_${VARIANT}_vivado.log \
        -journal build/reports/vision_ooc/${m}_${VARIANT}_vivado.jou || exit 1
done
echo "== 全部 OOC 综合完成（$VARIANT）=="
grep -h "OOC_RESULT" build/reports/vision_ooc/*_vivado.log || true
