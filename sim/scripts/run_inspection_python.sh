#!/usr/bin/env bash
# Offline inspection candidate; repository-local tests and outputs only.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source sim/scripts/vision_gate.sh
PY="${VISION_PYTHON:-python}"
mkdir -p sim/build/vision/inspection
for name in dataset_manifest dataset_audit roi_preprocess inspection_model inspection_rules inspection_artifacts inspection_replay inspection_viewer model_reference numpy_reference model_audit reference_tensors reference_package; do
    vision_run_checked "sim/build/vision/inspection/$name.log" \
        "$PY" "sim/vision/test_$name.py" || exit 1
done
