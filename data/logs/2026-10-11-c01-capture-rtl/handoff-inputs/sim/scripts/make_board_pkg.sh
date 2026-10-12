#!/usr/bin/env bash
# make_board_pkg —— 从 XSA 与 src/pynq_host 组装模块二板上部署包
# 产物（sim/build/board_pkg，不入库）：vision.bit / vision.hwh + PS 脚本 + RUNBOOK
# 用法: bash sim/scripts/make_board_pkg.sh [vision.xsa 路径]
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
XSA="${1:-$(dirname "$REPO_ROOT")/FPGA-Alittle-Design/sim/build/hdmi-project/vision.xsa}"
OUT="$REPO_ROOT/sim/build/board_pkg"

[ -f "$XSA" ] || { echo "ERROR: XSA 不存在: $XSA" >&2; exit 1; }
mkdir -p "$OUT"

python - "$XSA" "$OUT" <<'PY'
import sys, zipfile
xsa, out = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(xsa)
for name in ("vision.bit", "vision.hwh"):
    open(f"{out}/{name}", "wb").write(z.read(name))
    print(f"extract {name}")
PY

cp "$REPO_ROOT"/src/pynq_host/{vision_regs.py,vision_demo.py,m2_onboard.py} "$OUT/"
cp "$REPO_ROOT"/src/pynq_host/ONBOARD.md "$OUT/RUNBOOK.md"
ls -la "$OUT"
echo "board_pkg ready: $OUT"
