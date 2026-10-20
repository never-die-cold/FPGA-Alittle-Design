#!/usr/bin/env bash
# 重新生成本目录的 Windows 证据日志与退出码。在仓库根目录执行：
#   PATH=/ucrt64/bin:/usr/bin:/c/Users/ASUS/AppData/Local/Programs/Python/Python312:$PATH \
#     bash data/logs/2026-10-19-j04-closeout/windows-rerun.sh [all|cop_top|firmware|soc ...]
# 不带参数时按下面四个全跑；只跑其中几个就把名字当参数传进来。
set -u
D=data/logs/2026-10-19-j04-closeout
failed=0
run() {
    local name="$1" rc; shift
    "$@" > "$D/$name.log" 2>&1
    rc=$?
    echo "$rc" > "$D/$name.exit_code"
    printf '%-18s exit=%s\n' "$name" "$rc"
    [ "$rc" -eq 0 ] || failed=1
}
targets="${*:-all cop_top firmware soc}"
for t in $targets; do
    case "$t" in
        all)      run windows-all      bash sim/scripts/run_coprocessor_iverilog.sh all ;;
        cop_top)  run windows-cop_top  bash sim/scripts/run_coprocessor_iverilog.sh cop_top ;;
        firmware) run windows-firmware bash sim/scripts/run_coprocessor_iverilog.sh firmware ;;
        soc)      run windows-soc      bash sim/scripts/run_iverilog.sh soc ;;
        *) echo "unknown target: $t" >&2; exit 2 ;;
    esac
done
# 任一项失败都必须让一键入口本身非零退出，否则调用方会被"最后一条 printf 成功"骗过。
exit "$failed"
