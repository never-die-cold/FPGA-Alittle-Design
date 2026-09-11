#!/usr/bin/env bash
# iverilog 一键仿真（核冒烟）：编译 sim/riscv/tb_core_smoke.v + src/riscv/*.v 并运行
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）
set -u

cd "$(dirname "$0")/.."          # -> sim/

if ! command -v iverilog >/dev/null 2>&1; then
    echo "ERROR: 找不到 iverilog；请在 MSYS2 UCRT64 shell 中运行，或把其 ucrt64/bin 加入 PATH"
    exit 1
fi

# 把 iverilog 所在目录排到 PATH 最前，避免其他 MinGW 目录里的同名 DLL 抢加载
IVERILOG_DIR=$(dirname "$(command -v iverilog)")
export PATH="$IVERILOG_DIR:$PATH"

shopt -s nullglob
RTL_FILES=(../src/riscv/*.v)
if [ ${#RTL_FILES[@]} -eq 0 ]; then
    echo "ERROR: src/riscv/ 下暂无 .v RTL（Part A 未开工）；脚本已就位，RTL 落盘后即可跑"
    exit 1
fi

mkdir -p build
iverilog -g2012 -Wall -o build/tb_core_smoke.vvp \
    riscv/tb_core_smoke.v "${RTL_FILES[@]}" || exit 1

vvp build/tb_core_smoke.vvp
