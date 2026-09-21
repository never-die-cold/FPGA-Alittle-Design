#!/usr/bin/env bash
# iverilog 一键仿真：编译 sim/riscv/ 的 testbench + src/riscv/*.v 并逐个运行
# 用法：
#   bash sim/scripts/run_iverilog.sh          # 全部（v0 回归 + 转发专项）
#   bash sim/scripts/run_iverilog.sh v0       # v0 回归集合（冒烟 + 逐指令自检）
#   bash sim/scripts/run_iverilog.sh fwd      # 转发专项（数据冒险 / 分支气泡，v0 对照档）
#   bash sim/scripts/run_iverilog.sh muldiv   # RV32M 乘除单元模块级自检
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）
set -u

MODE="${1:-all}"

case "$MODE" in
    v0)  TBS=(riscv/tb_core_smoke.v riscv/tb_core_test.v) ;;
    fwd) TBS=(riscv/tb_core_fwd.v) ;;
    muldiv) TBS=(riscv/tb_muldiv.v) ;;
    all) TBS=(riscv/tb_core_smoke.v riscv/tb_core_test.v riscv/tb_core_fwd.v riscv/tb_muldiv.v) ;;
    *)   echo "用法: bash sim/scripts/run_iverilog.sh [v0|fwd|muldiv|all]"; exit 1 ;;
esac

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
for tb in "${TBS[@]}"; do
    [ -f "$tb" ] || continue
    name=$(basename "$tb" .v)
    echo "== $name =="
    iverilog -g2012 -Wall -o "build/$name.vvp" "$tb" "${RTL_FILES[@]}" || exit 1
    vvp "build/$name.vvp" || exit 1
done
