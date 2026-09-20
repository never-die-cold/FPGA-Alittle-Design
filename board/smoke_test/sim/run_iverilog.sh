#!/usr/bin/env bash
set -euo pipefail
trap 'echo "TEST FAILED: simulation command failed" >&2' ERR
smoke_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
command -v iverilog >/dev/null
command -v vvp >/dev/null
# Kept within this isolated example and ignored by its own .gitignore.
# Unique directories preserve previous results; this script deletes nothing.
mkdir -p "$smoke_dir/.sim_build"
run_dir="$(mktemp -d "$smoke_dir/.sim_build/run.XXXXXX")"
echo "Simulation outputs: $run_dir"
for divider in 1 2 5 8; do
    iverilog -g2005-sv -Wall -s pynq_z2_smoke_tb \
        -Ppynq_z2_smoke_tb.DIV_CYCLES="$divider" \
        -o "$run_dir/div_${divider}.vvp" \
        "$smoke_dir/rtl/pynq_z2_smoke_top.v" \
        "$smoke_dir/sim/pynq_z2_smoke_tb.v"
    vvp "$run_dir/div_${divider}.vvp"
done
echo "TEST PASSED: all divider configurations"
