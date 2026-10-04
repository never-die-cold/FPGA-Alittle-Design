#!/usr/bin/env bash
# Part B v1 arch-test matrix: same tests/reference, forwarding on and off.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$repo/sim/scripts/run_arch_test.sh"
suite="${ARCH_TEST_DIR:-$repo/sim/arch_test/suite}"
log_dir="${ARCH_TEST_LOG_DIR:-$repo/data/logs/$(date +%F)-partB-v1-arch-test}"
sig_dir="$repo/sim/build/arch_test/rv32i_m/I"
tests=(add-01 addi-01 and-01)

[ -d "$suite/.git" ] || { echo "ERROR: arch-test suite missing: $suite" >&2; exit 1; }
mkdir -p "$log_dir"

prefix="${RISCV_PREFIX:-riscv32-unknown-elf-}"
if ! command -v "${prefix}gcc" >/dev/null 2>&1; then prefix="riscv64-unknown-elf-"; fi
{
    echo "repo_commit=$(git -C "$repo" rev-parse HEAD)"
    echo "suite_commit=$(git -C "$suite" rev-parse HEAD)"
    "${prefix}gcc" --version | head -n 1
    iverilog -V 2>&1 | head -n 1
} > "$log_dir/environment.txt"

for test_name in "${tests[@]}"; do
    for mode in fwd nofwd; do
        echo "== $test_name $mode =="
        bash "$runner" "$test_name" I "$mode" 2>&1 | tee "$log_dir/$test_name.$mode.log"
    done
    cmp "$sig_dir/$test_name.fwd.signature.output" \
        "$sig_dir/$test_name.nofwd.signature.output"
    sha256sum "$sig_dir/$test_name."*.signature.output \
        > "$log_dir/$test_name.signatures.sha256"
    echo "PASS: $test_name fwd/nofwd signatures identical"
done

echo "PASS: arch-test matrix ${#tests[@]} tests x 2 modes"
