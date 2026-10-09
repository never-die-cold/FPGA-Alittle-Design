"""HUD v4 布局定稿图（Pillow 字体引擎 PoC，非产品代码）。

产出 1600x900 目标设计图：顶栏（标题/状态/时钟）+ 视频视口（圆角/角标/绿框/序号片）
+ 右上指标面板（圆角/图标位）+ 右侧"DETECTED OBJECTS"列表（缩略图/坐标/绿色徽标）
+ RUN INSPECTION 渐变按钮 + 左下状态块。
运行：set PYTHONPATH=<deps> && py render_v4_mockup.py
"""
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
sys.path.insert(0, str(ROOT / "src/vision_client"))
from hud_text import TextEngine
from preview import mock_frame
from vision_protocol import mock_packet

OUT = Path(__file__).resolve().parent
W, H = 1600, 900

BG_TOP, BG_BOT = (14, 19, 28), (7, 10, 16)
PANEL, PANEL2, BORDER = (17, 24, 37), (23, 32, 48), (40, 52, 74)
MAIN, DIM = (230, 237, 246), (122, 134, 152)
CYAN, GREEN, AMBER = (0, 210, 255), (0, 230, 130), (255, 176, 32)
DARK_TXT = (10, 16, 12)


def bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


def rounded_rgba(size, radius, fill=None, outline=None, width=1):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius,
        fill=(fill + (255,)) if fill else None,
        outline=(outline + (255,)) if outline else None, width=width)
    return np.asarray(img)


def paste(frame, rgba, x, y):
    h, w = rgba.shape[:2]
    roi = frame[y:y + h, x:x + w]
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
    roi[:] = (rgba[:, :, :3][:, :, ::-1].astype(np.float32) * alpha
              + roi.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return (np.asarray(m).astype(np.float32) / 255.0)[..., None]


def tracked(engine, frame, text, x, y, size, color, weight="Regular", tracking=3):
    cx = x
    for ch in text:
        engine.draw(frame, ch, cx, y, size, color, weight)
        cx += engine.advance(ch, size, weight) + tracking
    return cx


def chip_text(engine, frame, text, x, y, size, fg, bg, pad=11, weight="SemiBold"):
    tw, th = engine.size(text, size, weight)
    paste(frame, rounded_rgba((tw + 2 * pad, th + 10), (th + 10) // 2, fill=bg), x, y)
    engine.draw(frame, text, x + pad, y + 5, size, fg, weight)
    return tw + 2 * pad, th + 10


engine = TextEngine()
packet = mock_packet("e13c07fe-0000-0000-0000-000000000000", 7, 2, 7)
scene = mock_frame(packet)

# —— 画布（垂直渐变底） ——
t = np.linspace(0, 1, H)[:, None, None]
bg = (np.array(BG_TOP) * (1 - t) + np.array(BG_BOT) * t).astype(np.uint8)
frame = np.ascontiguousarray(np.repeat(bg, W, axis=1)[:, :, [2, 1, 0]])

# —— 顶栏（左：运行状态信息，主要位置；右：系统状态/时钟；所有元素垂直居中于 y=32） ——
BAR_CY = 32
cv2.line(frame, (0, 64), (W, 64), bgr(BORDER), 1)


def draw_cy(frame, text, x, size, color, weight="Regular", cy=BAR_CY):
    w, h = engine.size(text, size, weight)
    engine.draw(frame, text, x, cy - h // 2, size, color, weight)
    return w, h


tw, th = engine.size("MOCK ONLY", 14, "SemiBold")
chip_text(engine, frame, "MOCK ONLY", 30, BAR_CY - (th + 10) // 2, 14, DARK_TXT, AMBER, pad=12)
px = 30 + tw + 24 + 18
w1, _ = draw_cy(frame, "STREAMING", px, 16, MAIN, "SemiBold")
draw_cy(frame, "1280 x 720  |  30 FPS  |  session e13c07fe", px + w1 + 16, 13, DIM)
cv2.circle(frame, (1120, BAR_CY), 5, bgr(GREEN), -1, cv2.LINE_AA)
draw_cy(frame, "SYSTEM ONLINE", 1134, 16, (205, 212, 222))
cv2.line(frame, (1300, 16), (1300, 48), bgr(BORDER), 1)
cv2.circle(frame, (1330, BAR_CY), 9, (188, 196, 208), 2, cv2.LINE_AA)
cv2.line(frame, (1330, BAR_CY), (1330, BAR_CY - 7), (188, 196, 208), 2, cv2.LINE_AA)
cv2.line(frame, (1330, BAR_CY), (1336, BAR_CY + 2), (188, 196, 208), 2, cv2.LINE_AA)
draw_cy(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1348, 16, (205, 212, 222))

# —— 视频视口（圆角 + 细边框 + 角标） ——
VX, VY, VW, VH = 24, 88, 1264, 711
video = cv2.resize(scene, (VW, VH), interpolation=cv2.INTER_AREA)
mask = rounded_mask((VW, VH), 14)
roi = frame[VY:VY + VH, VX:VX + VW]
roi[:] = (video * mask + roi * (1 - mask)).astype(np.uint8)
paste(frame, rounded_rgba((VW, VH), 14, outline=BORDER), VX, VY)
for bx, by, dx, dy in ((12, 12, 1, 1), (VW - 12, 12, -1, 1), (12, VH - 12, 1, -1), (VW - 12, VH - 12, -1, -1)):
    p = (VX + bx, VY + by)
    cv2.line(frame, p, (p[0] + dx * 26, p[1]), (206, 212, 222), 2, cv2.LINE_AA)
    cv2.line(frame, p, (p[0], p[1] + dy * 26), (206, 212, 222), 2, cv2.LINE_AA)

# —— 目标框 + 序号片（视频坐标 0.9875 映射进视口） ——
S = VW / 1280.0
for i, tgt in enumerate(packet["targets"]):
    x0, y0, x1, y1 = tgt["bbox"]
    p0 = (int(round(VX + x0 * S)), int(round(VY + y0 * S)))
    p1 = (int(round(VX + x1 * S)), int(round(VY + y1 * S)))
    c = bgr(GREEN)
    cv2.line(frame, p0, (p1[0], p0[1]), c, 2, cv2.LINE_AA)
    cv2.line(frame, (p1[0], p0[1]), p1, c, 2, cv2.LINE_AA)
    cv2.line(frame, p1, (p0[0], p1[1]), c, 2, cv2.LINE_AA)
    cv2.line(frame, (p0[0], p1[1]), p0, c, 2, cv2.LINE_AA)
    chip_text(engine, frame, f"T{i}", p0[0], p0[1] - 36, 17, DARK_TXT, GREEN, pad=12)

# —— 右上指标面板 ——
MX0, MY0, MX1, MY1 = 712, 108, 1272, 222
paste(frame, rounded_rgba((MX1 - MX0, MY1 - MY0), 12, fill=(13, 19, 30), outline=BORDER), MX0, MY0)
cells = [("ROUND", "7"), ("TARGETS", "2"), ("REC", "--")]
cw = (MX1 - MX0) // 3
for i, (label, value) in enumerate(cells):
    cx = MX0 + cw * i + cw // 2
    lw, _ = engine.size(label, 14)
    start = cx - (18 + 8 + lw) // 2
    cv2.circle(frame, (start + 9, MY0 + 30), 9, (150, 160, 176), 2, cv2.LINE_AA)
    cv2.circle(frame, (start + 9, MY0 + 30), 3, (150, 160, 176), -1, cv2.LINE_AA)
    engine.draw(frame, label, start + 26, MY0 + 21, 14, DIM)
    engine.draw_cy(frame, value, cx, MY0 + 55, 36, MAIN, "SemiBold", "center")  # 按墨迹居中：-- 占位符与数字同带
    if i:
        cv2.line(frame, (MX0 + cw * i, MY0 + 16), (MX0 + cw * i, MY1 - 16), bgr(BORDER), 1)
engine.draw(frame, "FRESHNESS", MX0 + 18, MY0 + 92, 13, DIM)
fw, _ = engine.size("FRESHNESS", 13)
bx0, bx1, by = MX0 + 18 + fw + 14, MX1 - 18, MY0 + 95
paste(frame, rounded_rgba((bx1 - bx0, 7), 3, fill=(30, 38, 52)), bx0, by)
paste(frame, rounded_rgba((int((bx1 - bx0) * 0.7), 7), 3, fill=CYAN), bx0, by)

# —— 右侧：DETECTED OBJECTS 列表 ——
RX0, RY0, RX1, RY1 = 1312, 88, 1576, 799
paste(frame, rounded_rgba((RX1 - RX0, RY1 - RY0), 14, fill=PANEL, outline=BORDER), RX0, RY0)
engine.draw(frame, "DETECTED OBJECTS", RX0 + 22, RY0 + 18, 17, MAIN, "SemiBold")
chip_text(engine, frame, "2/2", RX1 - 22 - (engine.size("2/2", 14, "SemiBold")[0] + 22),
          RY0 + 16, 14, DARK_TXT, GREEN, pad=11)
for i, tgt in enumerate(packet["targets"]):
    cy0 = RY0 + 62 + i * 148
    paste(frame, rounded_rgba((RX1 - RX0 - 32, 134), 10, fill=PANEL2, outline=BORDER), RX0 + 16, cy0)
    x0, y0, x1, y1 = tgt["bbox"]
    thumb = cv2.resize(scene[y0:y1, x0:x1], (88, 66), interpolation=cv2.INTER_AREA)
    tm = rounded_mask((88, 66), 8)
    troi = frame[cy0 + 14:cy0 + 80, RX0 + 30:RX0 + 118]
    troi[:] = (thumb * tm + troi * (1 - tm)).astype(np.uint8)
    tx = RX0 + 30 + 88 + 20
    chip_text(engine, frame, f"T{i}", tx, cy0 + 12, 15, DARK_TXT, GREEN, pad=11)
    engine.draw(frame, f"X: {x0}    Y: {y0}", tx, cy0 + 56, 15, DIM)
    engine.draw(frame, f"W: {x1 - x0}    H: {y1 - y0}", tx, cy0 + 84, 15, DIM)
# RUN INSPECTION 渐变按钮
BX0, BY0, BX1, BY1 = RX0 + 24, RY1 - 84, RX1 - 24, RY1 - 24
bw, bh = BX1 - BX0, BY1 - BY0
tg = np.linspace(0, 1, bw)[None, :, None]
bgrad = (np.array(CYAN) * (1 - tg) + np.array(GREEN) * tg).astype(np.uint8)
bimg = np.concatenate([np.repeat(bgrad, bh, 0),
                       np.full((bh, bw, 1), 255, np.uint8)], 2)
maskb = rounded_mask((bw, bh), bh // 2)
bimg[:, :, 3:] = (bimg[:, :, 3:] * maskb).astype(np.uint8)
paste(frame, bimg, BX0, BY0)
icx, icy = BX0 + 32, (BY0 + BY1) // 2
cv2.circle(frame, (icx, icy), 8, DARK_TXT, 2, cv2.LINE_AA)
cv2.circle(frame, (icx, icy), 2, DARK_TXT, -1, cv2.LINE_AA)
engine.draw_cy(frame, "RUN INSPECTION", (BX0 + 40 + BX1 - 33) // 2 + 2, icy, 15, DARK_TXT, "Bold", "center")
cv2.line(frame, (BX1 - 30, icy - 6), (BX1 - 23, icy), DARK_TXT, 3, cv2.LINE_AA)
cv2.line(frame, (BX1 - 23, icy), (BX1 - 30, icy + 6), DARK_TXT, 3, cv2.LINE_AA)

# —— 左下品牌块（logo + EdgeSight，次要位置） ——
SPX, SPY = 24, 823
paste(frame, rounded_rgba((252, 53), 12, fill=PANEL, outline=BORDER), SPX, SPY)
cv2.fillPoly(frame, [np.array([[SPX + 18, SPY + 40], [SPX + 30, SPY + 13], [SPX + 38, SPY + 13], [SPX + 26, SPY + 40]], np.int32)], bgr(CYAN))
cv2.fillPoly(frame, [np.array([[SPX + 33, SPY + 40], [SPX + 45, SPY + 13], [SPX + 53, SPY + 13], [SPX + 41, SPY + 40]], np.int32)], (140, 110, 70))
engine.draw(frame, "EdgeSight", SPX + 70, SPY + 14, 25, MAIN, "SemiBold")

cv2.imwrite(str(OUT / "v4_mockup.png"), frame)
print("PASS: v4 mockup ->", OUT / "v4_mockup.png")
