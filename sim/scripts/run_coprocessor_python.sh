#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/sim/scripts/vision_gate.sh"
BUILD="$ROOT/sim/build/coprocessor"
PY="${COPROCESSOR_PYTHON:-${VISION_PYTHON:-python3}}"
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
    all) run_test primitives; run_test tensors; run_test conv; run_test network ;;
    *) echo "usage: $0 [primitives|tensors|conv|network|all]" >&2; exit 2 ;;
esac
