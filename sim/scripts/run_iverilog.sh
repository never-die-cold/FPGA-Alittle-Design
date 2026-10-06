#!/usr/bin/env bash
# iverilog 一键仿真：编译 sim/riscv/ 的 testbench + src/riscv/*.v 并逐个运行
# 用法：
#   bash sim/scripts/run_iverilog.sh          # 全量回归（含 CoreMark，约 2,100 万周期）
#   bash sim/scripts/run_iverilog.sh v0       # v0 回归集合（冒烟 + 逐指令自检）
#   bash sim/scripts/run_iverilog.sh fwd      # 转发专项（数据冒险 / 分支气泡，v0 对照档）
#   bash sim/scripts/run_iverilog.sh v1_fwd       # CoreMark：转发开、BHT 关
#   bash sim/scripts/run_iverilog.sh v1_nofwd     # CoreMark：转发关、BHT 关
#   bash sim/scripts/run_iverilog.sh v1_fwd_bht1  # CoreMark：转发开、1-bit BHT
#   bash sim/scripts/run_iverilog.sh v1_fwd_bht2  # CoreMark：转发开、2-bit BHT
#   bash sim/scripts/run_iverilog.sh v1_hazard_fwd   # v1 整核冒险边界，转发开启
#   bash sim/scripts/run_iverilog.sh v1_hazard_nofwd # v1 整核冒险边界，转发关闭
#   bash sim/scripts/run_iverilog.sh decode   # 译码源操作数使用标志
#   bash sim/scripts/run_iverilog.sh forwarding # 转发选择器单元自检
#   bash sim/scripts/run_iverilog.sh hazard    # 冒险与重定向控制自检
#   bash sim/scripts/run_iverilog.sh branch_predict # BHT 三档单元自检
#   bash sim/scripts/run_iverilog.sh pc_control # PC/flush 与优化前真值表等价
#   bash sim/scripts/run_iverilog.sh if_stage # IF valid-only flush 与停顿保持
#   bash sim/scripts/run_iverilog.sh mem_wb    # MEM+WB 边界寄存器自检
#   bash sim/scripts/run_iverilog.sh id_ex     # ID+EX 组合级自检
#   bash sim/scripts/run_iverilog.sh v1_mem    # v1 整核访存宽度与扩展自检
#   bash sim/scripts/run_iverilog.sh v1_muldiv_flow # v1 M 启动/等待流控自检
#   bash sim/scripts/run_iverilog.sh v1_muldiv_fwd   # v1 M 流控，转发开启
#   bash sim/scripts/run_iverilog.sh v1_muldiv_nofwd # v1 M 流控，转发关闭
#   bash sim/scripts/run_iverilog.sh muldiv   # RV32M 乘除单元模块级自检
#   bash sim/scripts/run_iverilog.sh rv32im   # RV32IM 固件整核冒烟
#   bash sim/scripts/run_iverilog.sh imem     # 32KB 同步读指令存储器模块级自检
#   bash sim/scripts/run_iverilog.sh dmem     # 32KB 异步读数据存储器模块级自检
#   bash sim/scripts/run_iverilog.sh clock_cfg # PYNQ-Z2 40/125 MHz MMCM 参数自检
#   bash sim/scripts/run_iverilog.sh coremark # CoreMark 2K/32 迭代 + golden 判据
#   bash sim/scripts/run_iverilog.sh coremark_fwd|coremark_nofwd # CoreMark CPI 双档
#   bash sim/scripts/run_iverilog.sh soc      # hello_v0 SoC + tohost LED 自检
#   bash sim/scripts/run_iverilog.sh soc_check # SoC 预载 + 计时器端到端自检
#   bash sim/scripts/run_iverilog.sh bench    # benchmark v0.1 + CPI 统计
#   bash sim/scripts/run_iverilog.sh bench_fwd|bench_nofwd # benchmark CPI 双档
#   bash sim/scripts/run_iverilog.sh vision [单项|all] # 视觉专项；all 含核与视觉
#   bash sim/scripts/run_iverilog.sh vision_gate # 视觉回归失败门禁自检
# 前置：PATH 中含 MSYS2 ucrt64 的 iverilog / vvp（13.0+）
set -u

MODE="${1:-all}"
IVERILOG_ARGS=()

case "$MODE" in
    vision) exec bash "$(dirname "$0")/run_vision_iverilog.sh" "${2:-all}" ;;
    vision_gate) exec bash "$(dirname "$0")/test_vision_gate.sh" ;;
    vision_python) exec bash "$(dirname "$0")/run_vision_python.sh" ;;
    v0)  TBS=(riscv/tb_core_smoke.v riscv/tb_core_test.v) ;;
    fwd) TBS=(riscv/tb_core_fwd.v) ;;
    v1_fwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=1 -Ptb_core_coremark.BHT_MODE=0) ;;
    v1_nofwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=0 -Ptb_core_coremark.BHT_MODE=0) ;;
    v1_fwd_bht1) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=1 -Ptb_core_coremark.BHT_MODE=1) ;;
    v1_fwd_bht2) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=1 -Ptb_core_coremark.BHT_MODE=2) ;;
    v1_hazard_fwd) TBS=(riscv/tb_core_v1_hazard.v); IVERILOG_ARGS=(-Ptb_core_v1_hazard.ENABLE_FORWARDING=1) ;;
    v1_hazard_nofwd) TBS=(riscv/tb_core_v1_hazard.v); IVERILOG_ARGS=(-Ptb_core_v1_hazard.ENABLE_FORWARDING=0) ;;
    decode) TBS=(riscv/tb_decode.v) ;;
    forwarding) TBS=(riscv/tb_forwarding.v) ;;
    hazard) TBS=(riscv/tb_hazard.v) ;;
    branch_predict) TBS=(riscv/tb_branch_predict.v) ;;
    pc_control) TBS=(riscv/tb_core_pc_control.v) ;;
    if_stage) TBS=(riscv/tb_if_stage.v) ;;
    bht_flow|bht_flow_2) TBS=(riscv/tb_core_bht_flow.v); IVERILOG_ARGS=(-Ptb_core_bht_flow.BHT_MODE=2) ;;
    bht_flow_1) TBS=(riscv/tb_core_bht_flow.v); IVERILOG_ARGS=(-Ptb_core_bht_flow.BHT_MODE=1) ;;
    bht_flow_off) TBS=(riscv/tb_core_bht_flow.v); IVERILOG_ARGS=(-Ptb_core_bht_flow.BHT_MODE=0) ;;
    mem_wb) TBS=(riscv/tb_mem_wb_stage.v) ;;
    id_ex) TBS=(riscv/tb_id_ex_stage.v) ;;
    v1_flow) TBS=(riscv/tb_core_v1_flow.v) ;;
    v1_mem) TBS=(riscv/tb_core_v1_mem.v) ;;
    v1_muldiv_flow) TBS=(riscv/tb_core_v1_muldiv_flow.v) ;;
    v1_muldiv_fwd) TBS=(riscv/tb_core_v1_muldiv_flow.v); IVERILOG_ARGS=(-Ptb_core_v1_muldiv_flow.ENABLE_FORWARDING=1) ;;
    v1_muldiv_nofwd) TBS=(riscv/tb_core_v1_muldiv_flow.v); IVERILOG_ARGS=(-Ptb_core_v1_muldiv_flow.ENABLE_FORWARDING=0) ;;
    muldiv) TBS=(riscv/tb_muldiv.v) ;;
    rv32im) TBS=(riscv/tb_core_muldiv.v) ;;
    imem) TBS=(riscv/tb_imem.v) ;;
    dmem) TBS=(riscv/tb_dmem.v) ;;
    clock_cfg) TBS=(riscv/tb_pynq_z2_clock_config.v) ;;
    coremark) TBS=(riscv/tb_core_coremark.v) ;;
    coremark_fwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=1) ;;
    coremark_nofwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=0) ;;
    soc) TBS=(riscv/tb_soc_top.v) ;;
    soc_check) TBS=(riscv/tb_soc_check.v) ;;
    bench) TBS=(riscv/tb_core_coremark.v) ;;
    bench_fwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=1) ;;
    bench_nofwd) TBS=(riscv/tb_core_coremark.v); IVERILOG_ARGS=(-Ptb_core_coremark.ENABLE_FORWARDING=0) ;;
    all) TBS=(riscv/tb_imem.v riscv/tb_dmem.v riscv/tb_pynq_z2_clock_config.v riscv/tb_core_smoke.v riscv/tb_core_test.v riscv/tb_core_v1_mem.v riscv/tb_core_fwd.v riscv/tb_decode.v riscv/tb_forwarding.v riscv/tb_hazard.v riscv/tb_branch_predict.v riscv/tb_core_pc_control.v riscv/tb_if_stage.v riscv/tb_core_bht_flow.v riscv/tb_mem_wb_stage.v riscv/tb_id_ex_stage.v riscv/tb_muldiv.v riscv/tb_core_muldiv.v riscv/tb_soc_top.v riscv/tb_soc_check.v) ;;
    *)   echo "用法: bash sim/scripts/run_iverilog.sh [v0|fwd|v1_fwd|v1_nofwd|v1_hazard_fwd|v1_hazard_nofwd|v1_muldiv_fwd|v1_muldiv_nofwd|decode|forwarding|hazard|branch_predict|mem_wb|id_ex|v1_flow|v1_mem|v1_muldiv_flow|muldiv|rv32im|imem|dmem|clock_cfg|coremark|coremark_fwd|coremark_nofwd|soc|soc_check|bench|bench_fwd|bench_nofwd|all]"; exit 1 ;;
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
    iverilog -g2012 -Wall "${IVERILOG_ARGS[@]}" -s "$name" -o "build/$name.vvp" "$tb" "${RTL_FILES[@]}" || exit 1
    if [ "$name" = "tb_core_coremark" ]; then
        if [[ "$MODE" = bench* ]]; then
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
    bash scripts/run_iverilog.sh v1_nofwd || exit 1
    bash scripts/run_iverilog.sh v1_fwd || exit 1
    bash scripts/run_iverilog.sh v1_fwd_bht1 || exit 1
    bash scripts/run_iverilog.sh v1_fwd_bht2 || exit 1
    bash scripts/run_iverilog.sh v1_hazard_fwd || exit 1
    bash scripts/run_iverilog.sh v1_hazard_nofwd || exit 1
    bash scripts/run_iverilog.sh v1_muldiv_fwd || exit 1
    bash scripts/run_iverilog.sh v1_muldiv_nofwd || exit 1
    bash scripts/run_iverilog.sh bht_flow_off || exit 1
    bash scripts/run_iverilog.sh bht_flow_1 || exit 1
    bash scripts/test_vision_gate.sh || exit 1
    bash scripts/run_vision_iverilog.sh all || exit 1
    bash scripts/run_vision_python.sh || exit 1
fi
