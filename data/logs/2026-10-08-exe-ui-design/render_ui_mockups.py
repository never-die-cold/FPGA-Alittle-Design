"""EXE HUD 设计提案渲染器（非产品代码，仅用于设计评审出图）。

输出三张 1280×720 对比图到本目录：
  01_current.png          当前实现（黑条 + 绿框 + 等宽小字）
  02_proposal_ok.png      提案：结果有效状态
  03_proposal_waiting.png 提案：等待/过期撤框状态
运行：py data/logs/2026-10-08-exe-ui-design/render_ui_mockups.py
"""
import cv2
import numpy as np
from pathlib import Path

W, H = 1280, 720
OUT = Path(__file__).resolve().parent
FONT = cv2.FONT_HERSHEY_DUPLEX

# 调色板（BGR）。深色面板 + 青色主色 + 语义状态色（绿=有效 / 琥珀=等待 / 红=故障）
PANEL = (34, 26, 20)      # 深蓝黑 #141A22
CYAN = (255, 210, 0)      # #00D2FF 主色/刻度
GREEN = (130, 230, 0)     # #00E682 目标框/有效
AMBER = (32, 176, 255)    # #FFB020 徽标琥珀
AMBER_DEEP = (0, 150, 240)  # #F09600 深琥珀：等待文字（浅底不再发虚）
RED = (79, 77, 255)       # #FF4D4F 故障（预留）
TEXT = (246, 248, 250)
DIM = (150, 156, 160)
SEP = (88, 80, 74)
BORDER = (150, 140, 130)  # 信息框细边框（冷灰）


def tsize(text, scale, th=1):
    (w, h), base = cv2.getTextSize(text, FONT, scale, th)
    return w, h, base


def put(img, text, org, scale, color, th=1, align="left"):
    w, h, _ = tsize(text, scale, th)
    x, y = org
    if align == "right":
        x -= w
    elif align == "center":
        x -= w // 2
    cv2.putText(img, text, (x, y), FONT, scale, color, th, cv2.LINE_AA)
    return w, h


def panel(img, rect, color=PANEL, alpha=0.62):
    x0, y0, x1, y1 = rect
    roi = img[y0:y1, x0:x1]
    base = np.empty_like(roi)
    base[:] = color
    cv2.addWeighted(base, alpha, roi, 1.0 - alpha, 0, roi)


def framed(img, rect, border=BORDER, alpha=0.55):
    """信息框：半透明衬底 + 细边框（v3：去四角刻线）。"""
    panel(img, rect, alpha=alpha)
    x0, y0, x1, y1 = rect
    cv2.rectangle(img, (x0, y0), (x1, y1), border, 1)


def brackets(img, rect, color, arm=20, th=3):  # v3 起不再用于目标框，保留仅供旧图复核
    x0, y0, x1, y1 = rect
    for px, py, dx, dy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        cv2.line(img, (px, py), (px + dx * arm, py), color, th, cv2.LINE_AA)
        cv2.line(img, (px, py), (px, py + dy * arm), color, th, cv2.LINE_AA)


def chip(img, x, y, text, fg, bg, scale=0.55, th=2, pad=8):
    w, h, _ = tsize(text, scale, th)
    cv2.rectangle(img, (x, y), (x + w + 2 * pad, y + h + 12), bg, -1)
    put(img, text, (x + pad, y + h + 6), scale, fg, th)


def scene(with_parts=True):
    img = np.full((H, W, 3), (196, 200, 204), np.uint8)  # 冷灰工作台
    for x in range(0, W, 80):
        cv2.line(img, (x, 0), (x, H), (188, 192, 196), 1)
    for y in range(0, H, 80):
        cv2.line(img, (0, y), (W, y), (188, 192, 196), 1)
    if with_parts:
        cv2.ellipse(img, (260, 230), (95, 72), 15, 0, 360, (96, 100, 106), -1, cv2.LINE_AA)
        cv2.ellipse(img, (830, 480), (110, 86), -10, 0, 360, (86, 90, 97), -1, cv2.LINE_AA)
    return img


BOXES = [(180, 170, 339, 289), (730, 400, 929, 559)]


def draw_current():
    img = scene()
    for x0, y0, x1, y1 in BOXES:
        cv2.rectangle(img, (x0, y0), (x1, y1), (40, 160, 30), 2)
        put(img, "target", (x0, y0 - 8), 0.6, (20, 180, 40), 2)
    cv2.rectangle(img, (0, 0), (W, 55), (35, 35, 35), -1)
    put(img, "MOCK ONLY | ROUND 7 | 0.3s ago | 2 targets | REC 2", (16, 36), 0.8, (255, 255, 255), 2)
    cv2.imwrite(str(OUT / "01_current.png"), img)


def draw_proposal(ok=True):
    img = scene(with_parts=ok)

    # —— 左上：状态框（细边框 + 四角刻线），内含模式徽标与状态行 ——
    framed(img, (24, 20, 384, 122))
    chip(img, 40, 36, "MOCK ONLY", (16, 14, 12), AMBER, scale=0.8, th=2, pad=12)
    if ok:
        put(img, "STREAMING | 1280x720 | session b564747f", (42, 103), 0.45, DIM, 1)
    else:
        put(img, "WAITING FOR RESULT", (42, 104), 0.55, AMBER_DEEP, 2)

    # —— 右上：四格指标面板（同样带边框与四角刻线；底部新鲜度条） ——
    x1, y0 = W - 24, 20
    x0, y1 = x1 - 520, 116
    framed(img, (x0, y0, x1, y1))
    cells = [
        ("ROUND", "7" if ok else "--"),
        ("TARGETS", "2" if ok else "--"),
        ("REC", "2"),
        ("AGE", "0.3s" if ok else "1.4s"),
    ]
    cell_w = (x1 - x0) // 4
    for i, (label, value) in enumerate(cells):
        cx = x0 + cell_w * i + cell_w // 2
        put(img, label, (cx, y0 + 26), 0.42, DIM, 1, "center")
        color = TEXT if (ok or label == "REC") else AMBER
        put(img, value, (cx, y0 + 74), 1.2, color, 2, "center")
        if i:
            cv2.line(img, (x0 + cell_w * i, y0 + 14), (x0 + cell_w * i, y1 - 14), SEP, 1)
    # 新鲜度条：有效=青色满到按年龄收缩；过期=红
    bar_y = y1 + 5
    cv2.rectangle(img, (x0, bar_y), (x1, bar_y + 5), (70, 62, 56), -1)
    frac = 0.7 if ok else 0.0
    if frac > 0:
        cv2.rectangle(img, (x0, bar_y), (x0 + int((x1 - x0) * frac), bar_y + 5), CYAN, -1)
    else:
        cv2.rectangle(img, (x0, bar_y), (x1, bar_y + 5), RED, -1)

    # —— 目标框（v3：实线绿方框 + 序号片；颜色+形状+文字三重编码） ——
    if ok:
        for i, (x0b, y0b, x1b, y1b) in enumerate(BOXES):
            cv2.rectangle(img, (x0b, y0b), (x1b, y1b), GREEN, 2, cv2.LINE_AA)
            chip(img, x0b, y0b - 34, f"T{i}", (10, 20, 10), GREEN, scale=0.55, th=2)

    # —— M3 预留注释（不渲染）：画面中上方为工单判定大徽标 PASS/FAIL/RECHECK ——
    cv2.imwrite(str(OUT / ("02_proposal_ok.png" if ok else "03_proposal_waiting.png")), img)


if __name__ == "__main__":
    draw_current()
    draw_proposal(ok=True)
    draw_proposal(ok=False)
    print("PASS: ui mockups ->", OUT)
