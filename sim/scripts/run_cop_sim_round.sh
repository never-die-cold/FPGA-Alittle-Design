#!/usr/bin/env bash
# One-command evidence run: COP_SIM service + real EXE headless, display/save/trace.
# Usage: bash sim/scripts/run_cop_sim_round.sh [repository-relative-output]
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
if [ -n "${VISION_PYTHON:-}" ]; then
    PY="$VISION_PYTHON"
elif [ -x sim/build/vision-venv/Scripts/python.exe ]; then
    PY=sim/build/vision-venv/Scripts/python.exe
elif [ -x sim/build/vision-venv/bin/python ]; then
    PY=sim/build/vision-venv/bin/python
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "ERROR: no Python found; set VISION_PYTHON" >&2
    exit 1
fi
OUT="${1:-sim/build/vision/cop-round}"
case "$OUT" in
    /*) ;;
    *) OUT="$PWD/$OUT" ;;
esac
case "$OUT" in
    "$PWD"/*) ;;
    *) echo "ERROR: output must stay inside the repository" >&2; exit 1 ;;
esac
export COP_ROUND_DIR="$OUT"
"$PY" sim/vision/test_cop_exe_round.py
