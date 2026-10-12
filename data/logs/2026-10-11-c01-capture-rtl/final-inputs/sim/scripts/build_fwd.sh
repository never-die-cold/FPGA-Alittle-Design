#!/usr/bin/env bash
# build_fwd.sh —— 构建转发专项测试程序：sim/riscv/fwd/fwd_test.S -> fwd_test.hex/.dis
# 复用 src/riscv_fw/ 的 start.S / link.ld / bin2hex.py（只读，不修改 bench 线文件）
# 前置：PATH 含 MSYS2 ucrt64 的 riscv32-unknown-elf-gcc；本机需可用 Python（bin2hex.py）
# 用法：bash sim/scripts/build_fwd.sh
set -euo pipefail

sim_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"   # -> sim/
fw_dir="$sim_dir/../src/riscv_fw"
out_dir="$sim_dir/riscv/fwd"

command -v riscv32-unknown-elf-gcc >/dev/null 2>&1 || {
    echo "ERROR: 找不到 riscv32-unknown-elf-gcc（请在 MSYS2 UCRT64 环境，或把 ucrt64/bin 加入 PATH）" >&2
    exit 1
}

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

PY="$(find_python)" || {
    echo "ERROR: 找不到可用的 Python（bin2hex.py 需要）" >&2
    exit 1
}

mkdir -p "$out_dir"
cd "$out_dir"

echo "== 汇编/链接（RV32I）=="
riscv32-unknown-elf-gcc -march=rv32i -mabi=ilp32 -mcmodel=medany -mno-relax -O2 \
    -ffreestanding -nostdlib -nostartfiles \
    -T "$fw_dir/link.ld" -Wl,--build-id=none \
    "$fw_dir/start.S" fwd_test.S -o fwd_test.elf

echo "== objcopy -> bin =="
riscv32-unknown-elf-objcopy -O binary fwd_test.elf fwd_test.bin

echo "== bin2hex -> hex =="
$PY "$fw_dir/bin2hex.py" fwd_test.bin fwd_test.hex

echo "== objdump -> dis（测试证据）=="
riscv32-unknown-elf-objdump -d fwd_test.elf > fwd_test.dis

echo "OK: $out_dir/fwd_test.hex (+ fwd_test.dis)"
