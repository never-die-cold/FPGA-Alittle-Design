#!/usr/bin/env bash
# 共用判据：进程成功、存在 PASS、没有失败文本，三者缺一不可。
vision_require_tb() {
    [ -f "$1" ] || { echo "ERROR: missing testbench $1"; return 1; }
}
vision_run_checked() {
    local log="$1"
    shift
    "$@" 2>&1 | tee "$log"
    local status=("${PIPESTATUS[@]}")
    if [ "${status[0]}" -ne 0 ] || [ "${status[1]}" -ne 0 ] ||
       ! grep -Eq '^PASS:' "$log" ||
       grep -Eiq '^[[:space:]]*(FAIL|FATAL|ERROR)(:|[[:space:]])' "$log"; then
        echo "ERROR: simulation gate rejected $log"
        return 1
    fi
}
