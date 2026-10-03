#!/usr/bin/env bash
# run_fmax_compare.sh —— 核对比 Fmax 实测驱动（docs/core_comparison.md §3 约束递减收敛法）
# 跑 PicoRV32 regular/large（上游 README 面积表同参数集，经 synth_area_top.v 包装层）
# 与自研 v0 核，同器件 xc7z020clg400-1、同 Vivado 2026.1、同 OOC post-route。
# 逐轮日志 build/run/fmax/<label>.log，报告 build/reports/fmax/<label>/；
# 收敛轮次由人工判读后补跑（10ns→5ns→收敛，2–3 轮）。
cd "$(dirname "$0")/../.." || exit 1
VIV=/d/Vivado_downloads/2026.1/Vivado/bin
FILTER="${1:-all}"   # all | pico | core（按标签前缀过滤，便于只补跑一侧）
mkdir -p build/run/fmax

bash sim/scripts/fetch_picorv32.sh || exit 1

PICO_V="sim/build/picorv32/picorv32.v sim/build/picorv32/scripts/vivado/synth_area_top.v"

run() { # run <label> <top> <period_ns> <src...>
    local label=$1 top=$2 period=$3
    shift 3
    if [ "$FILTER" != "all" ] && [ "${label%%_*}" != "$FILTER" ]; then
        return 0
    fi
    echo "=== [$label] top=$top period=${period}ns ==="
    "$VIV/vivado.bat" -mode batch -source build/build_fmax.tcl \
        -tclargs "$top" "$label" "$period" "$@" \
        > "build/run/fmax/${label}.log" 2>&1
    if [ $? -ne 0 ]; then
        echo "FAILED: $label（见 build/run/fmax/${label}.log 末尾）"
        tail -5 "build/run/fmax/${label}.log"
        return 1
    fi
    grep -A 4 "FMAX RUN DONE" "build/run/fmax/${label}.log"
}

FAILS=0
# 第 1 轮：10ns（对齐 v0 基线口径）；WNS 大幅为正者第 2 轮降 5ns，再判收敛
run pico_regular_10ns top_regular 10.000 $PICO_V || FAILS=$((FAILS+1))
run pico_regular_5ns  top_regular  5.000 $PICO_V || FAILS=$((FAILS+1))
run pico_large_10ns   top_large   10.000 $PICO_V || FAILS=$((FAILS+1))
run pico_large_5ns    top_large    5.000 $PICO_V || FAILS=$((FAILS+1))
# 收敛轮：regular@5ns 已 WNS=-0.139（194.6），5.1ns 确认过零点；
# large 5↔10ns 间隙宽（140.6↔106.3），7.0ns 找过零点
run pico_regular_5.1ns top_regular 5.100 $PICO_V || FAILS=$((FAILS+1))
run pico_large_7ns     top_large   7.000 $PICO_V || FAILS=$((FAILS+1))
# v0 核两档：源码取 partA-v0 tag 快照（基线锚点，不含后并入的 v1 积木文件），
# 与 PicoRV32 同一脚本同法对跑；10ns 对齐既有基线，5ns 供收敛判读
V0_SRC=build/run/fmax/v0-src/src/riscv
mkdir -p build/run/fmax/v0-src
git archive partA-v0 src/riscv | tar -x -C build/run/fmax/v0-src
run core_v0_10ns core_top 10.000 "$V0_SRC" || FAILS=$((FAILS+1))
run core_v0_5ns  core_top  5.000 "$V0_SRC" || FAILS=$((FAILS+1))

echo "=== ROUND SET DONE, failures=$FAILS ==="
echo "v0 10ns 基线沿用 build/reports 或 data/logs 既有证据；如 WNS@5ns 为正需再跑 3ns 轮收敛。"
exit $FAILS
