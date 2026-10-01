#!/usr/bin/env bash
# 模块二 XSim 对拍：iverilog 全 PASS 后 XSim 复跑同判据（design_v0.md §6 / docs/partB-verify-plan.md §6）
# 用法：bash sim/scripts/run_vision_xsim.sh [rgb2gray|linebuf|gaussian|scaler|sobel|chain|fullchain|osd|axi|align|top|all]
# 前置：Vivado 2026.1（xvlog/xelab/xsim 于 PATH 或默认安装路径）；golden 路径相对 sim/ 解析，勿改 CWD
# 注意：tb_top 首跑约 2-3 分钟（XSim 编译+仿真），全套约 5-8 分钟
set -u
VIV="/d/Vivado_downloads/2026.1/Vivado/bin"
MODE="${1:-all}"
case "$MODE" in
    rgb2gray) TBS=(tb_rgb2gray) ;;
    linebuf)  TBS=(tb_line_buffer) ;;
    gaussian) TBS=(tb_gaussian3x3) ;;
    scaler)   TBS=(tb_scaler) ;;
    sobel)    TBS=(tb_sobel) ;;
    chain)    TBS=(tb_chain) ;;
    fullchain) TBS=(tb_fullchain) ;;
    osd)      TBS=(tb_osd) ;;
    axi)      TBS=(tb_axi_regs) ;;
    align)    TBS=(tb_in_align) ;;
    top)      TBS=(tb_top) ;;
    all)      TBS=(tb_rgb2gray tb_line_buffer tb_gaussian3x3 tb_scaler tb_sobel tb_chain tb_fullchain tb_osd tb_axi_regs tb_in_align tb_top) ;;
    *)        echo "用法: bash sim/scripts/run_vision_xsim.sh [单项|all]"; exit 1 ;;
esac
cd "$(dirname "$0")/.."    # -> sim/（tb 内 $readmemh 用 ../data/golden/... 相对此目录）

"${VIV}/xvlog.bat" ../src/vision/*.v vision/tb_*.v > /dev/null 2>&1 \
    || { echo "ERROR: xvlog 编译失败"; exit 1; }

for t in "${TBS[@]}"; do
    echo "== $t =="
    "${VIV}/xelab.bat" "work.$t" -s "${t}_xsim" > /dev/null 2>&1 \
        || { echo "ERROR: xelab 失败 $t"; exit 1; }
    "${VIV}/xsim.bat" "${t}_xsim" -R 2>&1 | grep -E "^PASS|FAIL|fatal" \
        || { echo "ERROR: xsim 无 PASS 判据 $t"; exit 1; }
done
echo "== XSim 全部完成（$MODE）=="
