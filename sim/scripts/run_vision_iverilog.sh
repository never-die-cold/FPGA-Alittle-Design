#!/usr/bin/env bash
# 模块二（vision）一键仿真：编译 sim/vision/ 的 tb + src/vision/*.v 并逐个运行
# 专项入口；统一 run_iverilog.sh 的 vision/all 同样调用本脚本。
# 用法：
#   bash sim/scripts/run_vision_iverilog.sh            # 全部
#   bash sim/scripts/run_vision_iverilog.sh rgb2gray   # 灰度化单项
#   bash sim/scripts/run_vision_iverilog.sh linebuf    # 行缓存单项
#   bash sim/scripts/run_vision_iverilog.sh gaussian   # 高斯滤波单项
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）；黄金参考由
#       data/golden/vision/*/gen_*.py 生成（见各脚本头注释）。
set -uo pipefail

MODE="${1:-all}"

case "$MODE" in
    rgb2gray) TBS=(vision/tb_rgb2gray.v) ;;
    linebuf)  TBS=(vision/tb_line_buffer.v) ;;
    gaussian) TBS=(vision/tb_gaussian3x3.v) ;;
    scaler)   TBS=(vision/tb_scaler.v) ;;
    scaler_ds) TBS=(vision/tb_scaler_ds.v) ;;
    sobel)    TBS=(vision/tb_sobel.v) ;;
    chain)    TBS=(vision/tb_chain.v) ;;
    fullchain) TBS=(vision/tb_fullchain.v) ;;
    osd)      TBS=(vision/tb_osd.v) ;;
    axi)      TBS=(vision/tb_axi_regs.v) ;;
    axi_split) TBS=(vision/tb_axi_split.v) ;;
    config) TBS=(vision/tb_config_bridge.v) ;;
    top_async) TBS=(vision/tb_top_async.v) ;;
    color) TBS=(vision/tb_top_color.v) ;;
    pipeline) TBS=(vision/tb_video_pipeline.v) ;;
    real) TBS=(vision/tb_video_real.v) ;;
    hdmi_wrapper) TBS=(vision/tb_vision_axi.v) ;;
    patterns) TBS=(vision/tb_patterns.v) ;;
    align)    TBS=(vision/tb_in_align.v) ;;
    copbuf)   TBS=(vision/tb_cop_buf.v) ;;
    copbuf_stress) TBS=(vision/tb_cop_buf_stress.v) ;;
    top)      TBS=(vision/tb_top.v) ;;
    all)      TBS=(vision/tb_rgb2gray.v vision/tb_line_buffer.v vision/tb_gaussian3x3.v vision/tb_scaler.v vision/tb_scaler_ds.v vision/tb_sobel.v vision/tb_chain.v vision/tb_fullchain.v vision/tb_osd.v vision/tb_axi_regs.v vision/tb_in_align.v vision/tb_cop_buf.v vision/tb_top.v) ;;
    *)   echo "用法: bash sim/scripts/run_vision_iverilog.sh [rgb2gray|linebuf|gaussian|scaler|scaler_ds|sobel|chain|fullchain|osd|axi|align|copbuf|top|all]"; exit 1 ;;
esac
if [ "$MODE" = all ]; then TBS+=(vision/tb_cop_buf_stress.v vision/tb_axi_split.v vision/tb_config_bridge.v vision/tb_top_async.v vision/tb_top_color.v); fi
if [ "$MODE" = all ]; then TBS+=(vision/tb_video_pipeline.v vision/tb_video_real.v); fi
if [ "$MODE" = all ]; then TBS+=(vision/tb_vision_axi.v); fi
if [ "$MODE" = all ]; then TBS+=(vision/tb_patterns.v); fi

cd "$(dirname "$0")/.." || exit 1  # -> sim/
source scripts/vision_gate.sh

if ! command -v iverilog >/dev/null 2>&1; then
    echo "ERROR: 找不到 iverilog；请在 MSYS2 UCRT64 shell 中运行，或把其 ucrt64/bin 加入 PATH"
    exit 1
fi
IVERILOG_DIR=$(dirname "$(command -v iverilog)")
export PATH="$IVERILOG_DIR:$PATH"

shopt -s nullglob
RTL_FILES=(../src/vision/*.v)
if [ ${#RTL_FILES[@]} -eq 0 ]; then
    echo "ERROR: src/vision/ 下暂无 .v RTL"
    exit 1
fi

mkdir -p build/vision
for tb in "${TBS[@]}"; do
    vision_require_tb "$tb" || exit 1
    name=$(basename "$tb" .v)
    echo "== $name =="
    iverilog -g2012 -Wall -s "$name" -o "build/vision/$name.vvp" "$tb" "${RTL_FILES[@]}" || exit 1
    vision_run_checked "build/vision/$name.log" vvp "build/vision/$name.vvp" || exit 1
done
