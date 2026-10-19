"""EXE 识别范围表评审出图：一条命令五张（全选/子集实跑 + 三张交互态合成）。

运行（仓库根目录）：py data/logs/2026-10-17-exe-scope-redesign/render_scope_review.py
前置：本仓库 checkout（脚本自举 src/pynq_host、src/vision_client 与 vision-client-deps 路径）。
产出：本目录 scope-live-all.png / scope-live-subset.png / scope-state-hover.png /
      scope-state-queued.png / scope-state-running.png（1600×900）。
"""
import os
import subprocess
import sys
import threading
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[2]  # data/logs/<dir> -> 仓库根（here=目录，parents[0]=logs, [1]=data, [2]=仓库根）
deps = root / "sim" / "build" / "vision-client-deps"
for path in (root / "src" / "pynq_host", root / "src" / "vision_client", deps):
    if path not in sys.path:
        sys.path.append(str(path))

from vision_mock_service import make_server
from vision_protocol import mock_packet
from hud import AMBER_DEEP, GREEN, RED, Hud
from hud_text import TextEngine
from preview import mock_frame
import cv2

ALL = dict.fromkeys(("bolt", "nut", "washer"), True)
FULL = {"bolt": 2, "nut": 2, "washer": 2}

server = make_server(port=0, live=True)
threading.Thread(target=server.serve_forever, daemon=True).start()
for name, extra in (("scope-live-all.png", []),
                    ("scope-live-subset.png", ["--scope", "nut,washer"])):
    result = subprocess.run(
        [sys.executable, str(root / "src/vision_client/preview.py"), "--mock", "--headless",
         "--frames", "24", "--endpoint", f"http://127.0.0.1:{server.server_port}",
         "--save", str(here / name)] + extra,
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "PYTHONPATH": str(deps)})
    print(name, result.returncode, (result.stderr or "")[-200:] if result.returncode else "")
server.shutdown()
server.server_close()


def synth(path, selected, hover, button, counts, status):
    hud = Hud(TextEngine())
    p = mock_packet("s", 1, 0, 1)
    state = {"badge": ("LIVE", GREEN), "badge2": ("PROTOTYPE", RED),
             "status": (status, AMBER_DEEP, "SemiBold"),
             "detail": "1280 x 720 | 30 FPS | session 58301060",
             "clock": "2026-10-17 20:14:00",
             "scope": {"selected": selected, "counts": counts, "hover": hover,
                       "note": "ROUND 2 · REC 1", "button": button},
             "fresh": (0.7, (0, 210, 255)),
             "boxes": [("T0", (180, 170, 339, 289)), ("T1", (730, 380, 929, 520))],
             "list": [("T0", (180, 170, 339, 289), ("bolt", "0.97")),
                      ("T1", (730, 380, 929, 520), ("nut", "0.91"))]}
    cv2.imwrite(str(path), hud.render(mock_frame(p), state))
    print(path.name, "written")


synth(here / "scope-state-queued.png", ALL, None, "queued", FULL, "RECHECK -washerx1")
synth(here / "scope-state-running.png", ALL, None, "running", FULL, "CHECK_FAIL -washerx1")
synth(here / "scope-state-hover.png", {"bolt": True, "nut": True, "washer": False}, "nut",
      "idle", {"bolt": 1, "nut": 2, "washer": None}, "CHECK_PASS")
print("PASS: 5 review shots ->", here)
