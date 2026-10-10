#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
if [ -n "${VISION_PYTHON:-}" ]; then
    PY="$VISION_PYTHON"
elif command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "ERROR: 找不到 python/python3；可用 VISION_PYTHON 指定解释器"
    exit 1
fi
mkdir -p sim/build/vision/python
for name in vision_regs localize vision_protocol vision_rounds vision_records vision_export vision_live_standin arm_localize arm_localize_package; do
    vision_run_checked "sim/build/vision/python/$name.log" \
        "$PY" "sim/vision/test_$name.py" || exit 1
done
