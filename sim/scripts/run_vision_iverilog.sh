#!/usr/bin/env bash
# 模块二（vision）一键仿真：编译 sim/vision/ 的 tb + src/vision/*.v 并逐个运行
# 与模块一的 run_iverilog.sh 分离：模块二 tb 不进入模块一 `all` 门禁，反之亦然。
# 用法：
#   bash sim/scripts/run_vision_iverilog.sh            # 全部
#   bash sim/scripts/run_vision_iverilog.sh rgb2gray   # 灰度化单项
#   bash sim/scripts/run_vision_iverilog.sh linebuf    # 行缓存单项
#   bash sim/scripts/run_vision_iverilog.sh gaussian   # 高斯滤波单项
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）；黄金参考由
#       data/golden/vision/*/gen_*.py 生成（见各脚本头注释）。
set -u

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
    align)    TBS=(vision/tb_in_align.v) ;;
    top)      TBS=(vision/tb_top.v) ;;
    all)      TBS=(vision/tb_rgb2gray.v vision/tb_line_buffer.v vision/tb_gaussian3x3.v vision/tb_scaler.v vision/tb_scaler_ds.v vision/tb_sobel.v vision/tb_chain.v vision/tb_fullchain.v vision/tb_osd.v vision/tb_axi_regs.v vision/tb_in_align.v vision/tb_top.v) ;;
    *)   echo "用法: bash sim/scripts/run_vision_iverilog.sh [rgb2gray|linebuf|gaussian|scaler|scaler_ds|sobel|chain|fullchain|osd|axi|align|top|all]"; exit 1 ;;
esac

cd "$(dirname "$0")/.."          # -> sim/

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
    [ -f "$tb" ] || continue
    name=$(basename "$tb" .v)
    echo "== $name =="
    iverilog -g2012 -Wall -s "$name" -o "build/vision/$name.vvp" "$tb" "${RTL_FILES[@]}" || exit 1
    vvp "build/vision/$name.vvp" || exit 1
done
