#!/usr/bin/env bash
# 证明 %.dis 规则会把 objdump 的失败暴露成 make 失败，而不是被 tr 掩盖成一个空 .dis。
# 用法：bash sim/scripts/test_firmware_rules.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FW="$ROOT/src/riscv_fw"
OUT="$ROOT/sim/build/firmware-rules"
CROSS="${RISCV_CROSS:-riscv32-unknown-elf-}"
PY="${COPROCESSOR_PYTHON:-${VISION_PYTHON:-python}}"
if ! command -v "${CROSS}gcc" >/dev/null 2>&1 ||
   ! command -v "${CROSS}objdump" >/dev/null 2>&1; then
    CROSS=riscv64-unknown-elf-
    if ! command -v "${CROSS}gcc" >/dev/null 2>&1 ||
       ! command -v "${CROSS}objdump" >/dev/null 2>&1; then
        echo "SKIP: firmware rules require riscv32-unknown-elf- or riscv64-unknown-elf- gcc/objdump"
        exit 0
    fi
fi
mkdir -p "$OUT"

rm -f "$FW/cop_job.dis"   # 先删掉，避免上一轮失败留下的空文件被 make 当成"最新"
if ! make -C "$FW" CROSS="$CROSS" PYTHON="$PY" cop_job.dis > "$OUT/build.log" 2>&1; then
    echo "ERROR: 正常构建 cop_job.dis 失败，见 $OUT/build.log"
    exit 1
fi
before="$(sha256sum "$FW/cop_job.dis" | cut -d' ' -f1)"

# OBJDUMP=false 让 objdump 这一步必定失败；make 必须非零退出。
if make -B -C "$FW" CROSS="$CROSS" PYTHON="$PY" OBJDUMP=false cop_job.dis > "$OUT/objdump-fail.log" 2>&1; then
    echo "FAIL: objdump 失败时 make 仍返回 0（产物被当成成功）"
    exit 1
fi
after="$(sha256sum "$FW/cop_job.dis" | cut -d' ' -f1)"
if [ "$before" != "$after" ]; then
    echo "FAIL: objdump 失败时仍改写了 cop_job.dis"
    exit 1
fi
if [ ! -s "$FW/cop_job.dis" ]; then
    echo "FAIL: cop_job.dis 变成空文件"
    exit 1
fi
rm -f "$FW/cop_job.dis.tmp"
echo "PASS: objdump 失败 → make 非零退出，cop_job.dis 未被改写（sha256 ${before:0:12}…）"
