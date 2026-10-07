#!/usr/bin/env bash
# Module 1: baseline RV32I subset + all eight RV32M operations, four profiles.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$repo/sim/scripts/run_arch_test.sh"
suite="${ARCH_TEST_DIR:-$repo/sim/arch_test/suite}"
log_dir="${ARCH_TEST_LOG_DIR:-$repo/data/logs/$(date +%F)-module1-arch-test}"
tests=(
    I:add-01 I:addi-01 I:and-01
    M:div-01 M:divu-01 M:mul-01 M:mulh-01 M:mulhsu-01 M:mulhu-01 M:rem-01 M:remu-01
)

[ -d "$suite/.git" ] || { echo "ERROR: arch-test suite missing: $suite" >&2; exit 1; }
[ ! -e "$log_dir/environment.txt" ] || { echo "ERROR: use a new ARCH_TEST_LOG_DIR to preserve evidence" >&2; exit 1; }
mkdir -p "$log_dir"

prefix="${RISCV_PREFIX:-riscv32-unknown-elf-}"
if ! command -v "${prefix}gcc" >/dev/null 2>&1; then prefix="riscv64-unknown-elf-"; fi
{
    echo "repo_commit=$(git -C "$repo" rev-parse HEAD)"
    printf "rtl_sim_diff_sha256="
    git -C "$repo" diff -- src/riscv sim/riscv sim/scripts sim/arch_test/target | sha256sum | cut -d' ' -f1
    echo "suite_commit=$(git -C "$suite" rev-parse HEAD)"
    "${prefix}gcc" --version | sed -n '1p'
    iverilog -V 2>&1 | sed -n '1p'
} > "$log_dir/environment.txt"
sha256sum "$repo"/src/riscv/*.v "$repo/sim/riscv/tb_arch_test.v" \
    "$repo/sim/arch_test/target/pynq_z2_v0/env/link.ld" "$runner" "$0" > "$log_dir/sources.sha256"

for entry in "${tests[@]}"; do
    device="${entry%%:*}"; test_name="${entry#*:}"
    sig_dir="$repo/sim/build/arch_test/rv32i_m/$device"
    for mode in fwd nofwd bht1 bht2; do
        echo "== $test_name $mode =="
        bash "$runner" "$test_name" "$device" "$mode" 2>&1 | tee "$log_dir/$test_name.$mode.log"
        cp "$sig_dir/$test_name.$mode.signature.output" "$log_dir/"
    done
    reference_hash="$(sha256sum "$log_dir/$test_name.fwd.signature.output" | cut -d' ' -f1)"
    for mode in nofwd bht1 bht2; do
        actual_hash="$(sha256sum "$log_dir/$test_name.$mode.signature.output" | cut -d' ' -f1)"
        [[ "$actual_hash" == "$reference_hash" ]] || { echo "FAIL: $test_name $mode signature differs"; exit 1; }
    done
    sha256sum "$log_dir/$test_name."*.signature.output \
        > "$log_dir/$test_name.signatures.sha256"
    echo "PASS: $test_name four profiles match golden and each other"
done

echo "PASS: arch-test matrix ${#tests[@]} tests x 4 modes"
