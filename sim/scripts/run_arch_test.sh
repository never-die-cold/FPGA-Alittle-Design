#!/usr/bin/env bash
# run_arch_test.sh —— riscv-arch-test 单测：编译 → 仿真 → 签名比对（PYNQ-Z2 自研 v0 核）
# 用法：bash sim/scripts/run_arch_test.sh [测试名，默认 add-01] [扩展，默认 I]
# 前置：sim/scripts/fetch_arch_test.sh 已下载套件；MSYS2 UCRT64 工具链 + iverilog
# 产物：sim/build/arch_test/（hex/elf/签名输出，gitignore）
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
sim="$repo/sim"
suite="${ARCH_TEST_DIR:-$sim/arch_test/suite}"
test_name="${1:-add-01}"
device="${2:-I}"
xl=32
work="$sim/build/arch_test"
cycles="${ARCH_TEST_CYCLES:-200000}"

[ -d "$suite/.git" ] || {
    echo "ERROR: 未找到 arch-test 套件：$suite（先跑 sim/scripts/fetch_arch_test.sh 或设置 ARCH_TEST_DIR）" >&2
    exit 1
}

for tool in make riscv32-unknown-elf-gcc riscv32-unknown-elf-objcopy riscv32-unknown-elf-nm iverilog vvp; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: 找不到 $tool（请在 MSYS2 UCRT64 环境运行）" >&2
        exit 1
    }
done

find_python() {
    local c win_py
    for c in python3 python; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
            echo "$c"
            return 0
        fi
    done
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        win_py="$(cygpath "$USERPROFILE")/AppData/Local/Programs/Python/Python312/python.exe"
        if [ -x "$win_py" ]; then
            echo "$win_py"
            return 0
        fi
    fi
    if command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
        echo "py -3"
        return 0
    fi
    return 1
}
PY="$(find_python)" || { echo "ERROR: 找不到可用 Python（bin2hex.py 需要）" >&2; exit 1; }

if command -v git >/dev/null 2>&1; then
    suite_ver="$(git -C "$suite" rev-parse --short HEAD 2>/dev/null || echo unknown)"
else
    suite_ver="unknown（MSYS2 PATH 无 git）"
fi
echo "== [1/4] 编译 $test_name（套件 $suite_ver）=="
make -C "$suite" \
    RISCV_TARGET=pynq_z2_v0 \
    TARGETDIR="$sim/arch_test/target" \
    RISCV_DEVICE="$device" \
    XLEN="$xl" \
    RISCV_TEST="$test_name" \
    WORK="$work" \
    compile

elf="$work/rv${xl}i_m/$device/$test_name.elf"
ref="$suite/riscv-test-suite/rv${xl}i_m/$device/references/$test_name.reference_output"
[ -f "$elf" ] || { echo "ERROR: 未生成 $elf" >&2; exit 1; }
[ -f "$ref" ] || { echo "ERROR: 缺参考签名 $ref" >&2; exit 1; }

echo "== [2/4] 提取签名符号与参考 =="
sig_start=$(riscv32-unknown-elf-nm "$elf" | awk '$3=="begin_signature"{print $1}')
sig_end=$(riscv32-unknown-elf-nm "$elf" | awk '$3=="end_signature"{print $1}')
[ -n "$sig_start" ] && [ -n "$sig_end" ] || { echo "ERROR: ELF 中找不到 begin/end_signature 符号" >&2; exit 1; }
sig_words=$(( (16#$sig_end - 16#$sig_start) / 4 ))

mkdir -p "$work"
ref_clean="$work/ref_clean.txt"
grep -v '^[[:space:]]*#' "$ref" | grep -v '^[[:space:]]*$' > "$ref_clean"
ref_len=$(wc -l < "$ref_clean" | tr -d ' ')
echo "签名区 $sig_start..$sig_end（$sig_words 字），参考 $ref_len 行"
[ "$sig_words" -eq "$ref_len" ] || echo "WARN: 签名区字数与参考行数不一致"

echo "== [3/4] 镜像转换（bin -> hex）=="
riscv32-unknown-elf-objcopy -O binary "$elf" "$work/$test_name.bin"
$PY "$repo/src/riscv_fw/bin2hex.py" "$work/$test_name.bin" "$work/$test_name.hex"

echo "== [4/4] 仿真与签名比对（$cycles 周期）=="
iverilog -g2012 -s tb_arch_test -o "$work/tb_arch_test.vvp" "$sim/riscv/tb_arch_test.v" "$repo"/src/riscv/*.v

sig_out_abs="$work/rv${xl}i_m/$device/$test_name.signature.output"
mkdir -p "$(dirname "$sig_out_abs")"
work_rel="build/arch_test"
sig_out_rel="$work_rel/rv${xl}i_m/$device/$test_name.signature.output"

cd "$sim"
vvp "$work_rel/tb_arch_test.vvp" \
    +hex="$work_rel/$test_name.hex" \
    +ref="$work_rel/ref_clean.txt" \
    +ref_len="$ref_len" \
    +sig_start="$((16#$sig_start))" \
    +cycles="$cycles" \
    +sig_out="$sig_out_rel" \
    +name="$test_name"

echo "签名输出：$sig_out_abs"
