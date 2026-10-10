"""新鲜度条标注方案选项渲染（非产品代码）：出三张对比图供用户挑选。

10_option_a：条移入面板下沿空白区 + 左端小标签 "FRESHNESS"（推荐）
11_option_b：条移入面板下沿 + 双端语义标 "FRESH | EXPIRED"
12_option_c：不标注（现状：条浮在面板下方，靠 WAITING 状态文字传达）

运行：set PYTHONPATH=<deps> && py render_bar_options.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src/vision_client"))
import cv2
import numpy as np
from preview import AMBER, CYAN, DIM, TEXT, metrics_cells, mock_frame, put, render, tsize
from vision_protocol import mock_packet

OUT = Path(__file__).resolve().parent
X0, X1 = 736, 1256          # 指标面板左右边界（与 preview.draw_hud 一致）
STRIP_Y0, STRIP_Y1 = 105, 111   # 面板内条带（数字下方空白区）
BAR_FRAC = 0.7              # 示例：结果年龄约 30%

packet = mock_packet("2761ec40-0000-0000-0000-000000000000", 7, 2, 7)
hud = {"badge": ("MOCK ONLY", AMBER),
       "status": ("STREAMING | 1280x720 | session 2761ec40", DIM, 1),
       "metrics": metrics_cells(packet, 2, TEXT),
       "fresh": None}
base = render(mock_frame(packet), packet["targets"], hud)


def strip_bar(img, x_from, x_to, frac):
    """面板内条带：深色轨道 + 青色倒计填充。"""
    cv2.rectangle(img, (x_from, STRIP_Y0), (x_to, STRIP_Y1), (70, 62, 56), -1)
    if frac > 0:
        cv2.rectangle(img, (x_from, STRIP_Y0), (x_from + int((x_to - x_from) * frac), STRIP_Y1),
                      CYAN, -1)


# 10 方案 A：左端小标签 FRESHNESS + 条
img = base.copy()
put(img, "FRESHNESS", (X0 + 16, STRIP_Y1), 0.42, DIM, 1)
w, _ = tsize("FRESHNESS", 0.42, 1)
strip_bar(img, X0 + 16 + w + 14, X1 - 16, BAR_FRAC)
cv2.imwrite(str(OUT / "10_option_a.png"), img)


# 11 方案 B：双端语义标 FRESH | EXPIRED + 条
img = base.copy()
wf, _ = tsize("FRESH", 0.42, 1)
we, _ = tsize("EXPIRED", 0.42, 1)
put(img, "FRESH", (X0 + 16, STRIP_Y1), 0.42, DIM, 1)
put(img, "EXPIRED", (X1 - 16 - we, STRIP_Y1), 0.42, DIM, 1)
strip_bar(img, X0 + 16 + wf + 14, X1 - 16 - we - 14, BAR_FRAC)
cv2.imwrite(str(OUT / "11_option_b.png"), img)


# 12 方案 C：不标注（现状——条浮在面板下方）
img = base.copy()
cv2.rectangle(img, (X0, 121), (X1, 126), (70, 62, 56), -1)
cv2.rectangle(img, (X0, 121), (X0 + int((X1 - X0) * BAR_FRAC), 126), CYAN, -1)
cv2.imwrite(str(OUT / "12_option_c.png"), img)

print("PASS: bar label options ->", OUT)
