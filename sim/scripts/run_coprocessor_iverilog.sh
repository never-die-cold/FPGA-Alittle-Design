#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/sim/scripts/vision_gate.sh"
BUILD="$ROOT/sim/build/coprocessor"
mkdir -p "$BUILD"
PY="${COPROCESSOR_PYTHON:-${VISION_PYTHON:-python3}}"
if ! command -v "$PY" >/dev/null 2>&1 || ! "$PY" -c 'import sys' >/dev/null 2>&1; then
    PY=python
fi
CROSS="${RISCV_CROSS:-riscv32-unknown-elf-}"
if ! command -v "${CROSS}gcc" >/dev/null 2>&1 && command -v riscv64-unknown-elf-gcc >/dev/null 2>&1; then
    CROSS=riscv64-unknown-elf-
fi
VECTORS="$BUILD/arithmetic-vectors"
"$PY" "$ROOT/sim/coprocessor/generate_arithmetic_vectors.py" --output "$VECTORS"
run_test() {
    local name="$1"
    vision_require_tb "$ROOT/sim/coprocessor/tb_$name.v"
    iverilog -g2001 -Wall -s "tb_$name" -o "$BUILD/$name.vvp" \
        "$ROOT/sim/coprocessor/tb_$name.v" "$ROOT"/src/coprocessor/*.v
    vision_run_checked "$BUILD/$name.log" vvp "$BUILD/$name.vvp" "+vectors=$VECTORS"
}
run_convolution() {
    local dir="$BUILD/conv-vectors" name
    "$PY" "$ROOT/sim/coprocessor/generate_conv_vectors.py" --output "$dir"
    iverilog -g2001 -Wall -s tb_conv_engine -o "$BUILD/conv_engine.vvp" \
        "$ROOT/sim/coprocessor/tb_conv_engine.v" "$ROOT"/src/coprocessor/*.v
    while IFS= read -r name; do
        if [ "${1:-}" = watchdog ]; then
            vision_run_checked "$BUILD/watchdog_conv.log" vvp "$BUILD/conv_engine.vvp" "+case=$dir/$name" +watchdog_only
            break
        fi
        if [ "$name" = padding_tail ]; then
            vision_run_checked "$BUILD/conv_$name.log" vvp "$BUILD/conv_engine.vvp" "+case=$dir/$name" +fault_tests
        else
            vision_run_checked "$BUILD/conv_$name.log" vvp "$BUILD/conv_engine.vvp" "+case=$dir/$name"
        fi
    done < "$dir/cases.txt"
}
run_network() {
    local dir="$BUILD/network-vectors" name
    "$PY" "$ROOT/sim/coprocessor/generate_network_vectors.py" --output "$dir"
    iverilog -g2001 -Wall -s tb_cnn_sequencer -o "$BUILD/cnn_sequencer.vvp" \
        "$ROOT/sim/coprocessor/tb_cnn_sequencer.v" "$ROOT"/src/coprocessor/*.v
    while IFS= read -r name; do
        if [ "${1:-}" = watchdog ]; then
            vision_run_checked "$BUILD/watchdog_network.log" vvp "$BUILD/cnn_sequencer.vvp" "+model=$dir" "+case=$dir/$name" +watchdog_only
            break
        fi
        if [ "$name" = pattern ]; then
            vision_run_checked "$BUILD/network_$name.log" vvp "$BUILD/cnn_sequencer.vvp" "+model=$dir" "+case=$dir/$name" +fault_tests
        else
            vision_run_checked "$BUILD/network_$name.log" vvp "$BUILD/cnn_sequencer.vvp" "+model=$dir" "+case=$dir/$name"
        fi
    done < "$dir/cases.txt"
}
run_top() {
    local dir="$BUILD/network-vectors"
    "$PY" "$ROOT/sim/coprocessor/generate_network_vectors.py" --output "$dir"
    iverilog -g2001 -Wall -s tb_cop_top -o "$BUILD/cop_top.vvp" \
        "$ROOT/sim/coprocessor/tb_cop_top.v" "$ROOT"/src/coprocessor/*.v
    vision_run_checked "$BUILD/cop_top.log" vvp "$BUILD/cop_top.vvp" "+model=$dir" "+case=$dir/zero"
}
run_firmware() {
    make -C "$ROOT/src/riscv_fw" CROSS="$CROSS" PYTHON="$PY" cop_job.elf
    gcc -std=c99 -Wall -Wextra -Werror -I"$ROOT/src/riscv_fw" \
        "$ROOT/sim/coprocessor/test_cop_work_order.c" -o "$BUILD/test_cop_work_order"
    vision_run_checked "$BUILD/cop_work_order.log" "$BUILD/test_cop_work_order"
    vision_run_checked "$BUILD/firmware_rules.log" bash "$ROOT/sim/scripts/test_firmware_rules.sh"
}
case "${1:-all}" in
    mac_lane) run_test mac_lane ;;
    dot8) run_test dot8 ;;
    mmio_gate) run_test cop_core_mmio_gate ;;
    ctrl_regs) run_test cop_ctrl_regs ;;
    mailbox) run_test cop_cdc_mailbox ;;
    config_regs) run_test cop_config_regs ;;
    dma_loader) run_test cop_dma_loader ;;
    task_ctrl) run_test cop_task_ctrl ;;
    decision_ab) run_test cop_ctrl_regs; run_test cop_task_ctrl ;;
    cop_top) run_top ;;
    axi_lite) run_test cop_axi_lite_frontend ;;
    firmware) run_firmware ;;
    mac) run_test int8_mac ;;
    array) run_test mac_array ;;
    requant) run_test int8_requant ;;
    gap) run_test int8_gap ;;
    logits) run_test int8_logits ;;
    conv) run_convolution ;;
    network) run_network ;;
    watchdog) run_convolution watchdog; run_network watchdog ;;
    pipeline) run_test mac_array_pipeline; run_test int8_requant_pipeline ;;
    all) run_test cop_core_mmio_gate; run_test cop_ctrl_regs; run_test cop_cdc_mailbox; run_test cop_config_regs; run_test cop_dma_loader; run_test cop_task_ctrl; run_test cop_axi_lite_frontend; run_firmware; run_top; run_test mac_lane; run_test dot8; run_test int8_mac; run_test mac_array; run_test int8_requant; run_test int8_gap; run_test int8_logits; run_test mac_array_pipeline; run_test int8_requant_pipeline; run_convolution; run_network ;;
    *) echo 'usage: run_coprocessor_iverilog.sh [mmio_gate|ctrl_regs|mailbox|config_regs|dma_loader|task_ctrl|decision_ab|axi_lite|firmware|cop_top|mac_lane|dot8|mac|array|requant|gap|logits|pipeline|conv|network|watchdog|all]'; exit 2 ;;
esac
