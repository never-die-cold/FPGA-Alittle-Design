#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/sim/scripts/vision_gate.sh"
BUILD="$ROOT/sim/build/coprocessor"
mkdir -p "$BUILD"
run_test() {
    vision_require_tb "$ROOT/sim/coprocessor/test_int8_$1.py"
    vision_run_checked "$BUILD/int8_$1.log" env PYTHONPATH="$ROOT/src/coprocessor:$BUILD/python_deps" \
        python3 "$ROOT/sim/coprocessor/test_int8_$1.py"
}
case "${1:-all}" in
    primitives) run_test primitives ;;
    tensors) run_test tensors ;;
    conv) run_test conv ;;
    conv_layer) run_test conv_layer ;;
    gap_fc) run_test gap_fc ;;
    result) run_test result ;;
    model_schema) run_test model_schema ;;
    model_trace) run_test model_trace ;;
    all) run_test primitives; run_test tensors; run_test conv; run_test conv_layer; run_test gap_fc; run_test result; run_test model_schema; run_test model_trace ;;
    *) echo "usage: $0 [primitives|tensors|conv|conv_layer|gap_fc|result|model_schema|model_trace|all]" >&2; exit 2 ;;
esac
