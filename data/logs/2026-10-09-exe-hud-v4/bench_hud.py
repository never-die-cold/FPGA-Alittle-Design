"""HUD v4 渲染性能基准（临时诊断）。用法：set PYTHONPATH=<deps> && py bench_hud.py"""
import sys
import time
from pathlib import Path

root = Path(r"D:\Desktop\contests\2026fpga\FPGA-Alittle-Design\sim\build\exe-wt")
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from hud import Hud
from hud_text import TextEngine
from preview import clock_text, mock_frame
from vision_protocol import mock_packet

p = mock_packet("x", 7, 2, 7)
video = mock_frame(p)
hud = Hud(TextEngine())
state = {"badge": ("MOCK ONLY", (255, 176, 32)),
         "status": ("STREAMING", (230, 237, 246), "SemiBold"),
         "detail": "1280 x 720 | 30 FPS | session abc", "clock": clock_text(),
         "cells": [("ROUND", "7", (230, 237, 246)), ("TARGETS", "2", (230, 237, 246)),
                   ("REC", "2", (230, 237, 246))],
         "fresh": (0.7, (0, 210, 255)),
         "boxes": [tuple(t["bbox"]) for t in p["targets"]],
         "list": [tuple(t["bbox"]) for t in p["targets"]], "button": True}
for _ in range(3):
    hud.render(video, state)
t = time.perf_counter()
n = 20
for _ in range(n):
    hud.render(video, state)
print(f"render = {1000 * (time.perf_counter() - t) / n:.1f} ms/frame")
