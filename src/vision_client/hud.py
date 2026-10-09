"""hud.py —— HUD v4 应用外壳渲染层（EdgeSight）。

结构（性能方案）：
- 静态基座（背景渐变/顶栏底线/品牌块/SYSTEM ONLINE/时钟图标）启动预渲染一次，
  每帧仅 `base.copy()`；
- 形状固定的元素（视频视口框、指标面板、列表面板、卡片、RUN 按钮、徽标药丸）预渲染
  为 RGBA 贴图缓存，每帧仅 alpha 粘贴；
- 动态文本全部走 hud_text.TextEngine（贴图级缓存）；缩略图按轮次缓存。

坐标以 1600x900 画布为准；视频视口比例 1264/711 = 0.9875（源 1280x720 接近原生像素）。
state 字典字段（由 preview 组装）：
  badge=(text, bg_rgb) / status=(text, rgb, weight) / detail=text / clock=text /
  cells=[(label, value, rgb)] 或 None / fresh=(剩余比例, rgb) 或 None /
  boxes=[bbox...] 或 None（源视频坐标）/ list=同 boxes 或 None / button=bool
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from hud_text import TextEngine

# 画布与布局（与 data/logs/2026-10-09-exe-hud-v4/v4_mockup.png 一致）
W, H = 1600, 900
VIEW = (24, 88, 1264, 711)
VIEW_SCALE = VIEW[2] / 1280.0
MPANEL = (712, 108, 1272, 222)
LPANEL = (1312, 88, 1576, 799)
BRAND = (24, 823, 252, 53)
BUTTON = (1336, 715, 216, 60)

# 调色板（RGB）
BG_TOP, BG_BOT = (14, 19, 28), (7, 10, 16)
PANEL, PANEL2, PANEL3, BORDER = (17, 24, 37), (23, 32, 48), (13, 19, 30), (40, 52, 74)
MAIN, DIM = (230, 237, 246), (122, 134, 152)
CYAN, GREEN, AMBER = (0, 210, 255), (0, 230, 130), (255, 176, 32)
AMBER_DEEP, RED, DARK_TXT = (240, 150, 0), (255, 77, 79), (10, 16, 12)


def bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


def rounded_rgba(size, radius, fill=None, outline=None, width=1):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius,
        fill=(fill + (255,)) if fill else None,
        outline=(outline + (255,)) if outline else None, width=width)
    return np.array(img)  # np.array 而非 asarray：返回可写数组（cv2 绘制需要）


def _paste(canvas, rgba, x, y):
    """uint16 整数混合（>>8 代替 //255 再提速；±1 灰阶误差不可见）。"""
    h, w = rgba.shape[:2]
    roi = canvas[y:y + h, x:x + w]
    a = rgba[:, :, 3].astype(np.uint16)[..., None]
    src = rgba[:, :, :3][:, :, ::-1].astype(np.uint16)
    roi[:] = ((src * a + roi.astype(np.uint16) * (255 - a)) >> 8).astype(np.uint8)


def _corner_tiles(keep, r=17):
    h, w = keep.shape
    return ((0, r, 0, r), (0, r, w - r, w), (h - r, h, 0, r), (h - r, h, w - r, w))


def _blit(canvas, img, keep, x, y, outside_bgr=None, outside_patches=None):
    """不透明图形快速粘贴：矩形区直拷（memcpy），圆角外像素一次布尔赋值恢复底层。

    outside_patches 为整块预取背景（图形圆角外是静态底图时用）；否则 outside_bgr 单色。
    """
    h, w = img.shape[:2]
    roi = canvas[y:y + h, x:x + w]
    roi[:] = img
    out = ~keep
    if outside_patches is not None:
        roi[out] = outside_patches[out]
    else:
        roi[out] = outside_bgr


def _mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return (np.asarray(m).astype(np.float32) / 255.0)[..., None]


class Hud:
    """固定布局的 HUD 渲染器；线程内使用，不做并发保护。"""

    def __init__(self, engine: TextEngine):
        self.engine = engine
        self.mask = _mask((VIEW[2], VIEW[3]), 14)
        self.base = self._build_base()
        self.view_frame = self._build_view_frame()
        self.mpanel = rounded_rgba((MPANEL[2] - MPANEL[0], MPANEL[3] - MPANEL[1]), 12,
                                   fill=PANEL3, outline=BORDER)
        lw, lh = LPANEL[2] - LPANEL[0], LPANEL[3] - LPANEL[1]
        self.lpanel_img, self.lpanel_keep = self._shape((lw, lh), 14, fill=PANEL, outline=BORDER)
        self._lpanel_bg = self.base[LPANEL[1]:LPANEL[3], LPANEL[0]:LPANEL[2]].copy()
        self.card_img, self.card_keep = self._shape((lw - 32, 134), 10, fill=PANEL2, outline=BORDER)
        self.panel_bgr = bgr(PANEL)
        self._bar_x0 = int(MPANEL[0] + 18 + engine.advance("FRESHNESS", 13) + 14)
        self._bar_x1 = MPANEL[2] - 18
        self.track = rounded_rgba((self._bar_x1 - self._bar_x0, 7), 3, fill=(30, 38, 52))
        # 视频圆角只在四角有非 1 掩码：中间直拷、四角小块混合（避免全视口浮点运算）
        vw, vh = VIEW[2], VIEW[3]
        r = 17
        self._corners = [(y0, y1, x0, x1, self.mask[y0:y1, x0:x1])
                         for y0, y1, x0, x1 in ((0, r, 0, r), (0, r, vw - r, vw),
                                                (vh - r, vh, 0, r), (vh - r, vh, vw - r, vw))]
        self.button_img, self.button_keep = self._build_button()
        self._chip_cache = {}
        self._thumb_key = None
        self._thumbs = []

    # ---------- 预渲染 ----------
    def _build_base(self):
        t = np.linspace(0, 1, H)[:, None, None]
        bg = (np.array(BG_TOP) * (1 - t) + np.array(BG_BOT) * t).astype(np.uint8)
        base = np.ascontiguousarray(np.repeat(bg, W, axis=1)[:, :, [2, 1, 0]])
        cv2.line(base, (0, 64), (W, 64), bgr(BORDER), 1)
        cv2.circle(base, (1120, 32), 5, bgr(GREEN), -1, cv2.LINE_AA)
        self.engine.draw_cy(base, "SYSTEM ONLINE", 1134, 32, 16, (205, 212, 222))
        cv2.line(base, (1300, 16), (1300, 48), bgr(BORDER), 1)
        cv2.circle(base, (1330, 32), 9, (188, 196, 208), 2, cv2.LINE_AA)
        cv2.line(base, (1330, 32), (1330, 25), (188, 196, 208), 2, cv2.LINE_AA)
        cv2.line(base, (1330, 32), (1336, 34), (188, 196, 208), 2, cv2.LINE_AA)
        # 品牌块：logo + EdgeSight
        bx, by, bw, bh = BRAND
        _paste(base, rounded_rgba((bw, bh), 12, fill=PANEL, outline=BORDER), bx, by)
        cv2.fillPoly(base, [np.array([[bx + 18, by + 40], [bx + 30, by + 13],
                                      [bx + 38, by + 13], [bx + 26, by + 40]], np.int32)], bgr(CYAN))
        cv2.fillPoly(base, [np.array([[bx + 33, by + 40], [bx + 45, by + 13],
                                      [bx + 53, by + 13], [bx + 41, by + 40]], np.int32)], (140, 110, 70))
        self.engine.draw(base, "EdgeSight", bx + 70, by + 14, 25, MAIN, "SemiBold")
        return base

    def _build_view_frame(self):
        w, h = VIEW[2], VIEW[3]
        arr = rounded_rgba((w, h), 14, outline=BORDER)
        for bx, by, dx, dy in ((12, 12, 1, 1), (w - 12, 12, -1, 1),
                               (12, h - 12, 1, -1), (w - 12, h - 12, -1, -1)):
            cv2.line(arr, (bx, by), (bx + dx * 26, by), (222, 212, 205, 255), 2, cv2.LINE_AA)
            cv2.line(arr, (bx, by), (bx, by + dy * 26), (222, 212, 205, 255), 2, cv2.LINE_AA)
        # 只保留四条边缘带（边框环 + 四角标所在区域），中部全透明不必逐帧粘贴
        edge = 40
        return [(arr[0:edge, :], 0, 0),
                (arr[h - edge:h, :], 0, h - edge),
                (arr[edge:h - edge, 0:edge], 0, edge),
                (arr[edge:h - edge, w - edge:w], w - edge, edge)]

    @staticmethod
    def _shape(size, radius, fill=None, outline=None):
        """不透明圆角图形 → (BGR 矩形图, 不透明布尔掩码)。"""
        rgba = rounded_rgba(size, radius, fill=fill, outline=outline)
        img = np.ascontiguousarray(rgba[:, :, :3][:, :, ::-1])
        return img, rgba[:, :, 3] > 127

    def _build_button(self):
        bw, bh = BUTTON[2], BUTTON[3]
        tg = np.linspace(0, 1, bw)[None, :, None]
        grad = (np.array(bgr(CYAN)) * (1 - tg) + np.array(bgr(GREEN)) * tg).astype(np.uint8)
        img = np.repeat(grad, bh, 0)
        icy = bh // 2
        cv2.circle(img, (32, icy), 8, bgr(DARK_TXT), 2, cv2.LINE_AA)
        cv2.circle(img, (32, icy), 2, bgr(DARK_TXT), -1, cv2.LINE_AA)
        self.engine.draw_cy(img, "RUN INSPECTION", (40 + bw - 33) // 2 + 2, icy, 15,
                            DARK_TXT, "Bold", "center")
        cv2.line(img, (bw - 30, icy - 6), (bw - 23, icy), bgr(DARK_TXT), 3, cv2.LINE_AA)
        cv2.line(img, (bw - 23, icy), (bw - 30, icy + 6), bgr(DARK_TXT), 3, cv2.LINE_AA)
        return img, _mask((bw, bh), bh // 2)[..., 0] > 0.5

    # ---------- 缓存贴图 ----------
    def _chip(self, canvas, text, x, y, bg_rgb, size=17, fg=DARK_TXT, pad=12):
        """药丸贴片：先铺底色再在其上画文字，最后套圆角 alpha（v4 修复：直接替换法会盖掉底色）。"""
        key = (text, size, bg_rgb, fg, pad)
        rgba = self._chip_cache.get(key)
        if rgba is None:
            tw, th = self.engine.size(text, size, "SemiBold")
            w_, h_ = tw + 2 * pad, th + 10
            img = np.empty((h_, w_, 3), np.uint8)
            img[:] = bgr(bg_rgb)
            self.engine.draw_cy(img, text, pad, h_ // 2, size, fg, "SemiBold")
            m = _mask((w_, h_), h_ // 2)
            rgba = np.dstack([img[:, :, 2::-1], (m[..., 0] * 255).astype(np.uint8)])
            self._chip_cache[key] = rgba
        _paste(canvas, rgba, x, y)
        return rgba.shape[1], rgba.shape[0]

    def _box_chip(self, canvas, text, x, y):
        """目标序号片（绿底深字，贴布时用 alpha 混合保证盖住画面）。"""
        return self._chip(canvas, text, x, y, GREEN, size=17)

    # ---------- 每帧渲染 ----------
    def render(self, video, state):
        canvas = self.base.copy()
        vx, vy, vw, vh = VIEW
        small = cv2.resize(video, (vw, vh), interpolation=cv2.INTER_LINEAR)
        roi = canvas[vy:vy + vh, vx:vx + vw]
        bg_corners = [(canvas[vy + y0:vy + y1, vx + x0:vx + x1].copy(), y0, y1, x0, x1, mt)
                      for y0, y1, x0, x1, mt in self._corners]
        roi[:] = small  # 直拷（~99% 区域掩码=1）
        for back, y0, y1, x0, x1, mt in bg_corners:  # 仅四角小块做掩码混合
            sub = roi[y0:y1, x0:x1]
            sub[:] = (small[y0:y1, x0:x1] * mt + back * (1.0 - mt)).astype(np.uint8)
        for tile, tx, ty in self.view_frame:
            _paste(canvas, tile, vx + tx, vy + ty)

        if state.get("boxes"):
            for i, (x0, y0, x1, y1) in enumerate(state["boxes"]):
                p0 = (int(round(vx + x0 * VIEW_SCALE)), int(round(vy + y0 * VIEW_SCALE)))
                p1 = (int(round(vx + x1 * VIEW_SCALE)), int(round(vy + y1 * VIEW_SCALE)))
                for a, b in ((p0, (p1[0], p0[1])), ((p1[0], p0[1]), p1),
                             (p1, (p0[0], p1[1])), ((p0[0], p1[1]), p0)):
                    cv2.line(canvas, a, b, bgr(GREEN), 2, cv2.LINE_AA)
                self._box_chip(canvas, f"T{i}", p0[0], p0[1] - 36)

        self._topbar(canvas, state)
        if state.get("cells"):
            self._metrics(canvas, state)
        if state.get("list") is not None:
            self._list_panel(canvas, video, state["list"])
        if state.get("button"):
            _blit(canvas, self.button_img, self.button_keep, BUTTON[0], BUTTON[1],
                  outside_bgr=self.panel_bgr)
        return canvas

    def _topbar(self, canvas, state):
        cy = 32
        text, bg_rgb = state["badge"]
        tw, th = self.engine.size(text, 14, "SemiBold")
        chip_h = th + 10
        self._chip(canvas, text, 30, cy - chip_h // 2, bg_rgb, size=14)
        px = 30 + tw + 24 + 18
        stext, scolor, sweight = state["status"]
        w1, _ = self.engine.draw_cy(canvas, stext, px, cy, 16, scolor, sweight)
        detail = state.get("detail")
        if detail:
            self.engine.draw_cy(canvas, detail, px + w1 + 16, cy, 13, DIM)
        self.engine.draw_cy(canvas, state["clock"], 1348, cy, 16, (205, 212, 222))

    def _metrics(self, canvas, state):
        mx0, my0, mx1, my1 = MPANEL
        _paste(canvas, self.mpanel, mx0, my0)
        cw = (mx1 - mx0) // 3
        for i, (label, value, color) in enumerate(state["cells"]):
            cx = mx0 + cw * i + cw // 2
            lw, _ = self.engine.size(label, 14)
            start = cx - (18 + 8 + lw) // 2
            cv2.circle(canvas, (start + 9, my0 + 30), 9, (150, 160, 176), 2, cv2.LINE_AA)
            cv2.circle(canvas, (start + 9, my0 + 30), 3, (150, 160, 176), -1, cv2.LINE_AA)
            self.engine.draw(canvas, label, start + 26, my0 + 21, 14, DIM)
            self.engine.draw_cy(canvas, value, cx, my0 + 55, 36, color, "SemiBold", "center")
            if i:
                cv2.line(canvas, (mx0 + cw * i, my0 + 16), (mx0 + cw * i, my1 - 16), bgr(BORDER), 1)
        self.engine.draw(canvas, "FRESHNESS", mx0 + 18, my0 + 92, 13, DIM)
        bar_x0, bar_x1, by = self._bar_x0, self._bar_x1, my0 + 95
        _paste(canvas, self.track, bar_x0, by)
        if state.get("fresh") is not None:
            frac, color = state["fresh"]
            if frac > 0:
                cv2.rectangle(canvas, (bar_x0, by), (bar_x0 + int((bar_x1 - bar_x0) * frac), by + 7),
                              bgr(color), -1)

    def _thumbs_for(self, video, targets, key):
        if key != self._thumb_key:
            self._thumbs = []
            for x0, y0, x1, y1 in targets[:4]:
                crop = video[max(y0, 0):y1, max(x0, 0):x1]
                if crop.size == 0:
                    crop = np.zeros((2, 2, 3), np.uint8)
                thumb = cv2.resize(crop, (88, 66), interpolation=cv2.INTER_AREA)
                rgba = np.dstack([thumb[:, :, 2::-1], (_mask((88, 66), 8)[..., 0] * 255).astype(np.uint8)])
                self._thumbs.append(rgba)
            self._thumb_key = key
        return self._thumbs

    def _list_panel(self, canvas, video, targets):
        rx0, ry0, rx1, ry1 = LPANEL
        _blit(canvas, self.lpanel_img, self.lpanel_keep, rx0, ry0,
              outside_patches=self._lpanel_bg)
        self.engine.draw(canvas, "DETECTED OBJECTS", rx0 + 22, ry0 + 18, 17, MAIN, "SemiBold")
        code = str(len(targets)) if targets else "--"
        bw = self.engine.size(code, 14, "SemiBold")[0] + 24
        self._chip(canvas, code, rx1 - 22 - bw, ry0 + 16, GREEN if targets else PANEL3, size=14,
                   fg=DARK_TXT if targets else DIM)
        shown = self._thumbs_for(video, targets, (tuple(map(tuple, targets[:4])), len(targets)))
        for i, (x0, y0, x1, y1) in enumerate(targets[:4]):
            cy0 = ry0 + 62 + i * 148
            _blit(canvas, self.card_img, self.card_keep, rx0 + 16, cy0, outside_bgr=self.panel_bgr)
            _paste(canvas, shown[i], rx0 + 30, cy0 + 14)
            tx = rx0 + 30 + 88 + 20
            self._chip(canvas, f"T{i}", tx, cy0 + 12, GREEN, size=15)
            self.engine.draw(canvas, f"X: {x0}    Y: {y0}", tx, cy0 + 56, 15, DIM)
            self.engine.draw(canvas, f"W: {x1 - x0}    H: {y1 - y0}", tx, cy0 + 84, 15, DIM)
        if len(targets) > 4:
            self.engine.draw(canvas, f"+{len(targets) - 4} more", rx0 + 22, ry0 + 62 + 4 * 148 + 6,
                             14, DIM)
