#!/usr/bin/env bash
# make_board_pkg —— 从 XSA 与 src/pynq_host 组装模块二板上部署包
# 产物（sim/build/board_pkg，不入库）：vision.bit / vision.hwh + PS 脚本 + RUNBOOK
# 用法: bash sim/scripts/make_board_pkg.sh [vision.xsa 路径]
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
XSA="${1:-$(dirname "$REPO_ROOT")/FPGA-Alittle-Design/sim/build/hdmi-project/vision.xsa}"
OUT="${VISION_BOARD_PKG:-$REPO_ROOT/sim/build/board_pkg}"

[ -f "$XSA" ] || { echo "ERROR: XSA 不存在: $XSA" >&2; exit 1; }
mkdir -p "$OUT"

"${VISION_PYTHON:-python}" - "$XSA" "$OUT" <<'PY'
import sys, zipfile
xsa, out = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(xsa)
for name in ("vision.bit", "vision.hwh"):
    open(f"{out}/{name}", "wb").write(z.read(name))
    print(f"extract {name}")
PY

cp "$REPO_ROOT"/src/pynq_host/{vision_regs.py,vision_demo.py,m2_onboard.py,display_view.py} "$OUT/"
cp "$REPO_ROOT"/src/pynq_host/ONBOARD.md "$OUT/RUNBOOK.md"
"${VISION_PYTHON:-python}" - "$REPO_ROOT" "$OUT" <<'PY'
import hashlib, json, pathlib, subprocess, sys, zipfile
root, out = map(pathlib.Path, sys.argv[1:])
names = ["vision.bit", "vision.hwh", "vision_regs.py", "display_view.py",
         "m2_onboard.py", "vision_demo.py", "RUNBOOK.md"]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {"schema": 1, "files": {name: sha(out / name) for name in names},
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "source_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root)),
            "package_source_hashes": {str(p.relative_to(root)): sha(p) for p in sorted((root / "src/vision").glob("*.v"))}}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
with zipfile.ZipFile(out / "board_pkg.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in names + ["manifest.json"]:
        archive.write(out / name, name)
print("PASS: board package files, source hashes and UART ZIP assembled")
PY
ls -la "$OUT"
echo "board_pkg ready: $OUT"
