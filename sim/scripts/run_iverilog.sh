#!/usr/bin/env bash
# iverilog 一键仿真：编译 sim/riscv/ 的 testbench + src/riscv/*.v 并逐个运行
# 用法：
#   bash sim/scripts/run_iverilog.sh          # 全量回归（含 CoreMark，约 2,100 万周期）
#   bash sim/scripts/run_iverilog.sh v0       # v0 回归集合（冒烟 + 逐指令自检）
#   bash sim/scripts/run_iverilog.sh fwd      # 转发专项（数据冒险 / 分支气泡，v0 对照档）
#   bash sim/scripts/run_iverilog.sh decode   # 译码源操作数使用标志
#   bash sim/scripts/run_iverilog.sh forwarding # 转发选择器单元自检
#   bash sim/scripts/run_iverilog.sh hazard    # 冒险与重定向控制自检
#   bash sim/scripts/run_iverilog.sh mem_wb    # MEM+WB 边界寄存器自检
#   bash sim/scripts/run_iverilog.sh id_ex     # ID+EX 组合级自检
#   bash sim/scripts/run_iverilog.sh muldiv   # RV32M 乘除单元模块级自检
#   bash sim/scripts/run_iverilog.sh rv32im   # RV32IM 固件整核冒烟
#   bash sim/scripts/run_iverilog.sh imem     # 32KB 同步读指令存储器模块级自检
#   bash sim/scripts/run_iverilog.sh dmem     # 32KB 异步读数据存储器模块级自检
#   bash sim/scripts/run_iverilog.sh coremark # CoreMark 2K/32 迭代 + golden 判据
#   bash sim/scripts/run_iverilog.sh soc      # hello_v0 SoC + tohost LED 自检
#   bash sim/scripts/run_iverilog.sh soc_check # SoC 预载 + 计时器端到端自检
#   bash sim/scripts/run_iverilog.sh bench    # benchmark v0.1 + CPI 统计
#   bash sim/scripts/run_iverilog.sh vision [单项|all] # 视觉专项；all 含核与视觉
#   bash sim/scripts/run_iverilog.sh vision_gate # 视觉回归失败门禁自检
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）
set -u

MODE="${1:-all}"

case "$MODE" in
    vision) exec bash "$(dirname "$0")/run_vision_iverilog.sh" "${2:-all}" ;;
    vision_gate) exec bash "$(dirname "$0")/test_vision_gate.sh" ;;
    vision_python) exec bash "$(dirname "$0")/run_vision_python.sh" ;;
    v0)  TBS=(riscv/tb_core_smoke.v riscv/tb_core_test.v) ;;
    fwd) TBS=(riscv/tb_core_fwd.v) ;;
    decode) TBS=(riscv/tb_decode.v) ;;
    forwarding) TBS=(riscv/tb_forwarding.v) ;;
    hazard) TBS=(riscv/tb_hazard.v) ;;
    mem_wb) TBS=(riscv/tb_mem_wb_stage.v) ;;
    id_ex) TBS=(riscv/tb_id_ex_stage.v) ;;
    muldiv) TBS=(riscv/tb_muldiv.v) ;;
    rv32im) TBS=(riscv/tb_core_muldiv.v) ;;
    imem) TBS=(riscv/tb_imem.v) ;;
    dmem) TBS=(riscv/tb_dmem.v) ;;
    coremark) TBS=(riscv/tb_core_coremark.v) ;;
    soc) TBS=(riscv/tb_soc_top.v) ;;
    soc_check) TBS=(riscv/tb_soc_check.v) ;;
    bench) TBS=(riscv/tb_core_coremark.v) ;;
    all) TBS=(riscv/tb_imem.v riscv/tb_dmem.v riscv/tb_core_smoke.v riscv/tb_core_test.v riscv/tb_core_fwd.v riscv/tb_decode.v riscv/tb_forwarding.v riscv/tb_hazard.v riscv/tb_mem_wb_stage.v riscv/tb_id_ex_stage.v riscv/tb_muldiv.v riscv/tb_core_muldiv.v riscv/tb_core_coremark.v riscv/tb_soc_top.v riscv/tb_soc_check.v) ;;
    *)   echo "用法: bash sim/scripts/run_iverilog.sh [v0|fwd|decode|forwarding|hazard|mem_wb|id_ex|muldiv|rv32im|imem|dmem|coremark|soc|soc_check|bench|all]"; exit 1 ;;
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
COREMARK_ARGS=(
    +hex=../src/riscv_fw/coremark.hex +exp_exit=0 +timer_addr=80008000 +max_cycles=50000000
    +exp_tohost=34713 +exp_iter=32 +exp_seedcrc=e9f5 +exp_crclist=e714
    +exp_crcmatrix=1fd7 +exp_crcstate=8e3a +exp_crcfinal=8799
)
BENCH_ARGS=(
    +hex=../src/riscv_fw/bench_v0_1.hex +exp_exit=0
    +exp_tohost=327535569 +max_cycles=200000
)
for tb in "${TBS[@]}"; do
    [ -f "$tb" ] || continue
    name=$(basename "$tb" .v)
    echo "== $name =="
    iverilog -g2012 -Wall -s "$name" -o "build/$name.vvp" "$tb" "${RTL_FILES[@]}" || exit 1
    if [ "$name" = "tb_core_coremark" ]; then
        if [ "$MODE" = "bench" ]; then
            vvp "build/$name.vvp" "${BENCH_ARGS[@]}" || exit 1
        else
            vvp "build/$name.vvp" "${COREMARK_ARGS[@]}" || exit 1
            if [ "$MODE" = "all" ]; then
                echo "== tb_bench_v0_1 =="
                vvp "build/$name.vvp" "${BENCH_ARGS[@]}" || exit 1
            fi
        fi
    else
        vvp "build/$name.vvp" || exit 1
    fi
done
if [ "$MODE" = "all" ]; then
    bash scripts/test_vision_gate.sh || exit 1
    bash scripts/run_vision_iverilog.sh all || exit 1
    bash scripts/run_vision_python.sh || exit 1
fi
