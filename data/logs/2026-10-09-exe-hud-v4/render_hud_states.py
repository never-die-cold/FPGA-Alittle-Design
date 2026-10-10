"""HUD v4 状态渲染校验（非产品代码）：用产品 hud.Hud 渲染"等待/过期"与"UVC-only"两种状态。

02/03 两张图由真实运行产生（preview.py --mock [--endpoint]）；本脚本补渲染另外两条
状态分支供人工目检（state 字典与 preview 的组装一致）。
运行：set PYTHONPATH=<deps> && py render_hud_states.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src/vision_client"))
import cv2
from hud import AMBER, AMBER_DEEP, DIM, MAIN, RED, Hud
from hud_text import TextEngine
from preview import clock_text, mock_frame
from vision_protocol import mock_packet

OUT = Path(__file__).resolve().parent
packet = mock_packet("b564747f-0000-0000-0000-000000000000", 7, 2, 7)
hud = Hud(TextEngine())

# 等待/过期状态（endpoint 模式、结果超龄）：字段同 preview.endpoint_state 的 waiting 分支
waiting = {"badge": ("MOCK ONLY", AMBER),
           "status": ("WAITING FOR RESULT", AMBER_DEEP, "SemiBold"),
           "detail": "1280 x 720 | 30 FPS | session b564747f",
           "clock": clock_text(),
           "cells": [("ROUND", "--", AMBER_DEEP), ("TARGETS", "--", AMBER_DEEP), ("REC", "2", MAIN)],
           "fresh": (1.0, RED), "boxes": None, "list": [], "button": True}
cv2.imwrite(str(OUT / "04_waiting_state.png"), hud.render(mock_frame(packet), waiting))

# UVC-only 状态（无结果服务）：隐藏指标面板与对象列表、无 RUN 按钮
uvc = {"badge": ("VIDEO ONLY", DIM),
       "status": ("UNASSOCIATED | no board recognition", DIM, "Regular"),
       "detail": "1280 x 720 | 30 FPS",
       "clock": clock_text(), "cells": None, "fresh": None,
       "boxes": None, "list": None, "button": False}
cv2.imwrite(str(OUT / "05_uvc_only.png"), hud.render(mock_frame(packet), uvc))
print("PASS: hud state renders ->", OUT)
