#!/usr/bin/env bash
# 仓库内可复现的故障注入；不删除源文件、不依赖工作区外临时文件。
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/vision_gate.sh
mkdir -p build/vision/gate
checked=0
expect() {
    local wanted="$1" label="$2" result=0
    shift 2
    "$@" || result=$?
    if { [ "$wanted" = accept ] && [ "$result" -ne 0 ]; } ||
       { [ "$wanted" = reject ] && [ "$result" -eq 0 ]; }; then
        echo "FAIL: gate $label result=$result wanted=$wanted"
        exit 1
    fi
    checked=$((checked+1))
    echo "CASE: $label result=$result wanted=$wanted"
}
run() { vision_run_checked "build/vision/gate/$label.log" "$@"; }
expect accept pass run bash -c 'echo "PASS: injected"'
expect accept tcl_echo run bash -c 'echo "# if true { error failed }"; echo "PASS: injected"'
expect reject fail_zero run bash -c 'echo "FAIL: injected"'
expect reject mixed run bash -c 'echo "PASS: injected"; echo "FAIL: injected"'
expect reject fatal run bash -c 'echo "FATAL: injected"'
expect reject no_pass run bash -c 'echo "INFO: no verdict"'
expect reject process_failed run bash -c 'echo "PASS: injected"; exit 7'
expect reject missing_tb vision_require_tb build/vision/gate/not-a-testbench.v
echo "PASS: vision gate $checked cases (PASS/FAIL/fatal/exit/missing tb)"
