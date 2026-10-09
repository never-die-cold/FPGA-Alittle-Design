"""CJK 渲染样本（Noto Sans SC 子集，M3 类别名/工单判定的显示能力预置，非产品代码）。

运行：set PYTHONPATH=<deps> && py render_cjk_sample.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src/vision_client"))
import cv2
import numpy as np

from hud import AMBER_DEEP, DIM, GREEN, MAIN
from hud_text import TextEngine

OUT = Path(__file__).resolve().parent
engine = TextEngine()

W, H = 780, 400
img = np.full((H, W, 3), (30, 24, 18), np.uint8)  # BGR 深底（近面板色）
rows = [
    ("类别名（M3 预置）", 22, "螺栓  螺母  垫圈", "SemiBold", MAIN),
    ("工单判定（M3 预置）", 22, "通过  失败  复检  无法确认", "SemiBold", GREEN),
    ("等待状态", 26, "等待结果", "SemiBold", AMBER_DEEP),
    ("标签尺寸", 15, "工单  数量  记录  导出  批次  异常", "Regular", DIM),
    ("混合文本", 18, "螺栓 ×3   螺母 ×2   垫圈 ×1", "Regular", MAIN),
]
y = 26
for caption, size, text, weight, color in rows:
    engine.draw(img, caption, 24, y, 13, DIM)
    engine.draw(img, text, 24, y + 20, size, color, weight)
    y += 76
cv2.imwrite(str(OUT / "cjk_sample.png"), img)
print("PASS: cjk sample ->", OUT / "cjk_sample.png")
