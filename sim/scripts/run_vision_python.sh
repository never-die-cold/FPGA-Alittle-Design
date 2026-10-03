#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
PY="${VISION_PYTHON:-python}"
mkdir -p sim/build/vision/python
for name in vision_regs localize vision_protocol arm_localize; do
    vision_run_checked "sim/build/vision/python/$name.log" \
        "$PY" "sim/vision/test_$name.py" || exit 1
done
