#!/usr/bin/env bash
# 模块二 XSim 对拍：iverilog 全 PASS 后 XSim 复跑同判据（design_v0.md §6 / docs/partB-verify-plan.md §6）
# 用法：bash sim/scripts/run_vision_xsim.sh [rgb2gray|linebuf|gaussian|scaler|sobel|chain|fullchain|osd|axi|align|top|all]
# 前置：Vivado 2026.1（xvlog/xelab/xsim 于 PATH 或默认安装路径）；golden 路径相对 sim/ 解析，勿改 CWD
# 注意：tb_top 首跑约 2-3 分钟（XSim 编译+仿真），全套约 5-8 分钟
set -uo pipefail
VIV="${VISION_VIVADO_BIN:-/d/Vivado_downloads/2026.1/Vivado/bin}"
MODE="${1:-all}"
case "$MODE" in
    rgb2gray) TBS=(tb_rgb2gray) ;;
    linebuf)  TBS=(tb_line_buffer) ;;
    gaussian) TBS=(tb_gaussian3x3) ;;
    scaler)   TBS=(tb_scaler) ;;
    scaler_ds) TBS=(tb_scaler_ds) ;;
    sobel)    TBS=(tb_sobel) ;;
    chain)    TBS=(tb_chain) ;;
    fullchain) TBS=(tb_fullchain) ;;
    osd)      TBS=(tb_osd) ;;
    axi)      TBS=(tb_axi_regs) ;;
    axi_split) TBS=(tb_axi_split) ;;
    config) TBS=(tb_config_bridge) ;;
    top_async) TBS=(tb_top_async) ;;
    color) TBS=(tb_top_color) ;;
    pipeline) TBS=(tb_video_pipeline) ;;
    real) TBS=(tb_video_real) ;;
    hdmi_wrapper) TBS=(tb_vision_axi) ;;
    patterns) TBS=(tb_patterns) ;;
    align)    TBS=(tb_in_align) ;;
    copbuf)   TBS=(tb_cop_buf) ;;
    copbuf_stress) TBS=(tb_cop_buf_stress) ;;
    top)      TBS=(tb_top) ;;
    all)      TBS=(tb_rgb2gray tb_line_buffer tb_gaussian3x3 tb_scaler tb_scaler_ds tb_sobel tb_chain tb_fullchain tb_osd tb_axi_regs tb_in_align tb_cop_buf tb_top) ;;
    *)        echo "用法: bash sim/scripts/run_vision_xsim.sh [单项|all]"; exit 1 ;;
esac
if [ "$MODE" = all ]; then TBS+=(tb_cop_buf_stress tb_axi_split tb_config_bridge tb_top_async tb_top_color); fi
if [ "$MODE" = all ]; then TBS+=(tb_video_pipeline tb_video_real); fi
if [ "$MODE" = all ]; then TBS+=(tb_vision_axi); fi
if [ "$MODE" = all ]; then TBS+=(tb_patterns); fi
cd "$(dirname "$0")/.." || exit 1
source scripts/vision_gate.sh
mkdir -p build/vision/xsim
for t in "${TBS[@]}"; do
    vision_require_tb "vision/$t.v" || exit 1
done

"${VIV}/xvlog.bat" ../src/vision/*.v vision/tb_*.v > build/vision/xsim/compile.log 2>&1 \
    || { cat build/vision/xsim/compile.log; echo "ERROR: xvlog 编译失败"; exit 1; }

for t in "${TBS[@]}"; do
    echo "== $t =="
    "${VIV}/xelab.bat" "work.$t" -s "${t}_xsim" > "build/vision/xsim/$t-elab.log" 2>&1 \
        || { cat "build/vision/xsim/$t-elab.log"; echo "ERROR: xelab 失败 $t"; exit 1; }
    vision_run_checked "build/vision/xsim/$t.log" "${VIV}/xsim.bat" "${t}_xsim" -R || exit 1
done
echo "== XSim 全部完成（$MODE）=="
