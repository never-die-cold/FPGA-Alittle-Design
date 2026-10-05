#!/usr/bin/env bash
# Part B D3.1b: same CoreMark image/tb, forwarding on vs off.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$repo/sim/scripts/run_iverilog.sh"
log_dir="${CPI_LOG_DIR:-$repo/data/logs/$(date +%F)-partB-v1-cycle-breakdown}"
mkdir -p "$log_dir"

{
    echo "repo_commit=$(git -C "$repo" rev-parse HEAD)"
    printf "rtl_sim_diff_sha256="
    git -C "$repo" diff -- src/riscv sim/riscv sim/scripts | sha256sum | cut -d' ' -f1
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
parse_class() {
    sed -n 's/^CLASS: mode=\([0-9][0-9]*\) mul=\([0-9][0-9]*\) div=\([0-9][0-9]*\) load_use=\([0-9][0-9]*\) raw_nofwd=\([0-9][0-9]*\) control=\([0-9][0-9]*\) other=\([0-9][0-9]*\) classified=\([0-9][0-9]*\)$/\1 \2 \3 \4 \5 \6 \7 \8/p' "$1"
}

read -r f_mode f_cycles f_retired f_bubbles < <(parse_pass "$log_dir/coremark-fwd.log")
read -r n_mode n_cycles n_retired n_bubbles < <(parse_pass "$log_dir/coremark-nofwd.log")
read -r fc_mode f_mul f_div f_load f_raw f_ctrl f_other f_classified < <(parse_class "$log_dir/coremark-fwd.log")
read -r nc_mode n_mul n_div n_load n_raw n_ctrl n_other n_classified < <(parse_class "$log_dir/coremark-nofwd.log")

[[ "$f_mode" == 1 && "$n_mode" == 0 ]] || { echo "FAIL: wrong forwarding modes"; exit 1; }
[[ "$fc_mode" == 1 && "$nc_mode" == 0 ]] || { echo "FAIL: wrong CLASS modes"; exit 1; }
[[ "$f_retired" == "$n_retired" ]] || { echo "FAIL: retired mismatch $f_retired/$n_retired"; exit 1; }
(( f_cycles == f_retired + f_bubbles )) || { echo "FAIL: fwd accounting mismatch"; exit 1; }
(( n_cycles == n_retired + n_bubbles )) || { echo "FAIL: nofwd accounting mismatch"; exit 1; }
(( f_classified == f_bubbles && n_classified == n_bubbles )) || { echo "FAIL: bubble classification mismatch"; exit 1; }
[[ "$f_mul $f_div $f_load $f_ctrl $f_other" == "$n_mul $n_div $n_load $n_ctrl $n_other" ]] || { echo "FAIL: common bubble classes differ"; exit 1; }
(( f_raw == 0 )) || { echo "FAIL: forwarding mode has RAW bubbles: $f_raw"; exit 1; }
(( n_raw - f_raw == n_cycles - f_cycles )) || { echo "FAIL: RAW delta does not explain cycle delta"; exit 1; }

awk -v fc="$f_cycles" -v nc="$n_cycles" -v r="$f_retired" \
    -v fm="$f_mul" -v fd="$f_div" -v fl="$f_load" -v fr="$f_raw" \
    -v fx="$f_ctrl" -v fo="$f_other" -v nr="$n_raw" 'BEGIN {
    fcp=fc/r; ncp=nc/r; gain=(ncp-fcp)/ncp*100;
    printf "RESULT: fwd cycles=%d retired=%d CPI=%.6f\n", fc, r, fcp;
    printf "RESULT: nofwd cycles=%d retired=%d CPI=%.6f\n", nc, r, ncp;
    printf "CLASS: fwd mul=%d div=%d load_use=%d raw_nofwd=%d control=%d other=%d\n", fm, fd, fl, fr, fx, fo;
    printf "CLASS: nofwd mul=%d div=%d load_use=%d raw_nofwd=%d control=%d other=%d\n", fm, fd, fl, nr, fx, fo;
    printf "RESULT: mul share of fwd cycles=%.2f%%; RAW delta=%d\n", fm/fc*100, nr-fr;
    printf "RESULT: CPI gain=%.2f%% (gate >=8.0%%)\n", gain;
    if (gain < 8.0) { print "FAIL: CPI gain below 8.0%"; exit 1; }
    print "PASS: CoreMark CPI gain gate";
}' | tee "$log_dir/summary.txt"
