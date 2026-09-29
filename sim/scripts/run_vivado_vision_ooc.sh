#!/usr/bin/env bash
# 模块二 OOC 综合一键入口（不上板）：逐模块综合，产出资源/时序基线报告
# 用法：bash sim/scripts/run_vivado_vision_ooc.sh
# 前置：Vivado 2026.1 安装于 D:/Vivado_downloads/2026.1（如路径不同请修改 VIVADO）
set -u
VIVADO="/d/Vivado_downloads/2026.1/Vivado/bin/vivado.bat"
cd "$(dirname "$0")/../.."    # -> 仓库根
mkdir -p build/reports/vision_ooc

for m in rgb2gray gaussian_3x3 sobel scaler; do
    echo "== OOC synth: $m =="
    "$VIVADO" -mode batch -source sim/scripts/synth_vision_ooc.tcl -tclargs "$m" \
        -log  build/reports/vision_ooc/${m}_vivado.log \
        -journal build/reports/vision_ooc/${m}_vivado.jou || exit 1
done
echo "== 全部 OOC 综合完成 =="
grep -h "OOC_RESULT" build/reports/vision_ooc/*_vivado.log || true
