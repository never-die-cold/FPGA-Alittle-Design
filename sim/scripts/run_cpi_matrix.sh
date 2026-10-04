#!/usr/bin/env bash
# Part B D3.1b: same CoreMark image/tb, forwarding on vs off.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$repo/sim/scripts/run_iverilog.sh"
log_dir="${CPI_LOG_DIR:-$repo/data/logs/$(date +%F)-partB-v1-coremark-cpi}"
mkdir -p "$log_dir"

{
    echo "repo_commit=$(git -C "$repo" rev-parse HEAD)"
    iverilog -V 2>&1 | head -n 1
    sha256sum "$repo/src/riscv_fw/coremark.hex"
} > "$log_dir/environment.txt"

for mode in fwd nofwd; do
    echo "== CoreMark $mode =="
    bash "$runner" "coremark_$mode" 2>&1 | tee "$log_dir/coremark-$mode.log"
done

parse_pass() {
    sed -n 's/^PASS: coremark mode=\([0-9][0-9]*\) cycles=\([0-9][0-9]*\) retired=\([0-9][0-9]*\) bubbles=\([0-9][0-9]*\) cpi=.*/\1 \2 \3 \4/p' "$1"
}

read -r f_mode f_cycles f_retired f_bubbles < <(parse_pass "$log_dir/coremark-fwd.log")
read -r n_mode n_cycles n_retired n_bubbles < <(parse_pass "$log_dir/coremark-nofwd.log")

[[ "$f_mode" == 1 && "$n_mode" == 0 ]] || { echo "FAIL: wrong forwarding modes"; exit 1; }
[[ "$f_retired" == "$n_retired" ]] || { echo "FAIL: retired mismatch $f_retired/$n_retired"; exit 1; }
(( f_cycles == f_retired + f_bubbles )) || { echo "FAIL: fwd accounting mismatch"; exit 1; }
(( n_cycles == n_retired + n_bubbles )) || { echo "FAIL: nofwd accounting mismatch"; exit 1; }

awk -v fc="$f_cycles" -v nc="$n_cycles" -v r="$f_retired" 'BEGIN {
    fcp=fc/r; ncp=nc/r; gain=(ncp-fcp)/ncp*100;
    printf "RESULT: fwd cycles=%d retired=%d CPI=%.6f\n", fc, r, fcp;
    printf "RESULT: nofwd cycles=%d retired=%d CPI=%.6f\n", nc, r, ncp;
    printf "RESULT: CPI gain=%.2f%% (gate >=25%%)\n", gain;
    if (gain < 25) { print "FAIL: CPI gain below 25%"; exit 1; }
    print "PASS: CoreMark CPI gain gate";
}' | tee "$log_dir/summary.txt"
