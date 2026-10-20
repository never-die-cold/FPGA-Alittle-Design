#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/sim/scripts/vision_gate.sh"
BUILD="$ROOT/sim/build/coprocessor"
PY="${COPROCESSOR_PYTHON:-${VISION_PYTHON:-python3}}"
# 与 run_coprocessor_iverilog.sh 同一口径：本机没有 python3 这个名字就退回 python。
if ! command -v "$PY" >/dev/null 2>&1 || ! "$PY" -c 'import sys' >/dev/null 2>&1; then
    PY=python
fi
mkdir -p "$BUILD"
run_test() {
    vision_require_tb "$ROOT/sim/coprocessor/test_int8_$1.py"
    vision_run_checked "$BUILD/int8_$1.log" env PYTHONPATH="$ROOT/src/coprocessor:$BUILD/python_deps" \
        "$PY" "$ROOT/sim/coprocessor/test_int8_$1.py"
}
case "${1:-all}" in
    primitives) run_test primitives ;;
    tensors) run_test tensors ;;
    conv) run_test conv ;;
    network) run_test network ;;
    conv_layer) run_test conv_layer ;;
    gap_fc) run_test gap_fc ;;
    result) run_test result ;;
    model_schema) run_test model_schema ;;
    model_trace) run_test model_trace ;;
    manifests) run_test manifests ;;
    all) run_test primitives; run_test tensors; run_test conv; run_test network; run_test conv_layer; run_test gap_fc; run_test result; run_test model_schema; run_test model_trace; run_test manifests ;;
    *) echo "usage: $0 [primitives|tensors|conv|network|conv_layer|gap_fc|result|model_schema|model_trace|manifests|all]" >&2; exit 2 ;;
esac
