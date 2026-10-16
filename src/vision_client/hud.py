"""hud.py —— HUD v4 应用外壳渲染层（EdgeSight）。

结构（性能方案）：
- 静态基座（背景渐变/顶栏底线/品牌块/SYSTEM ONLINE/时钟图标）启动预渲染一次，
  每帧仅 `base.copy()`；
- 形状固定的元素（视频视口框、指标面板、列表面板、卡片、RUN 按钮、徽标药丸）预渲染
  为 RGBA 贴图缓存，每帧仅 alpha 粘贴；
- 动态文本全部走 hud_text.TextEngine（贴图级缓存）；缩略图按轮次缓存。

坐标以 1600x900 画布为准；视频视口比例 1264/711 = 0.9875（源 1280x720 接近原生像素）。
state 字典字段（由 preview / replay_viewer 组装）：
  badge=(text, bg_rgb) / status=(text, rgb, weight) / detail=text / clock=text /
  boxes=[(chip, bbox)...] 或 None（源视频坐标）/ list=[(chip, bbox, label|None)...] 或 None /
  fresh=(剩余比例, rgb) 或 None /
  scope=识别范围表 {selected, counts, hover, note, button|None, readonly?} 或省略（隐藏面板）
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
SCOPE = (1312, 88, 264, 246)  # 识别范围面板：侧栏顶部（类别/勾选/数目 + FRESHNESS + RUN 按钮）
SCOPE_ROW_H = 34
LPANEL = (1312, 342, 1576, 799)  # 检测对象列表：识别范围面板之下
BRAND = (24, 823, 252, 53)
CLASSES = ("bolt", "nut", "washer")

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

    def __init__(self, engine: TextEngine, system=("SYSTEM ONLINE", GREEN)):
        self.engine = engine
        self.system = system
        self.mask = _mask((VIEW[2], VIEW[3]), 14)
        self.base = self._build_base()
        self.view_frame = self._build_view_frame()
        sx, sy, sw, sh = SCOPE
        pad = 14
        self.scope_panel = rounded_rgba((sw, sh), 14, fill=PANEL, outline=BORDER)
        self.scope_hover = rounded_rgba((sw - 20, SCOPE_ROW_H - 4), 8, fill=PANEL2)
        self.scope_check = {"on": self._scope_check_sprite(True),
                            "off": self._scope_check_sprite(False)}
        self.scope_rects = {}
        first_row = sy + 52
        for index, name in enumerate(CLASSES):
            self.scope_rects[name] = (sx + 10, first_row + index * SCOPE_ROW_H, sw - 20, SCOPE_ROW_H)
        run = (sx + pad, sy + sh - pad - 42, sw - 2 * pad, 42)
        self.scope_rects["run"] = run
        self.scope_button = {
            "idle": self._scope_button_sprite(run[2], run[3], "RUN INSPECTION",
                                              DARK_TXT, CYAN, (0, 166, 230)),
            "queued": self._scope_button_sprite(run[2], run[3], "QUEUED · WAITING",
                                                DARK_TXT, AMBER, None),
            "running": self._scope_button_sprite(run[2], run[3], "RUNNING",
                                                 CYAN, PANEL2, None)}
        self._scope_bar_x0 = int(sx + pad + engine.advance("FRESHNESS", 12) + 12)
        self._scope_bar_x1 = sx + sw - pad
        self.scope_track = rounded_rgba((self._scope_bar_x1 - self._scope_bar_x0, 7), 3,
                                        fill=(30, 38, 52))
        lw, lh = LPANEL[2] - LPANEL[0], LPANEL[3] - LPANEL[1]
        self.lpanel_img, self.lpanel_keep = self._shape((lw, lh), 14, fill=PANEL, outline=BORDER)
        self._lpanel_bg = self.base[LPANEL[1]:LPANEL[3], LPANEL[0]:LPANEL[2]].copy()
        self.card_img, self.card_keep = self._shape((lw - 32, 116), 10, fill=PANEL2, outline=BORDER)
        self.panel_bgr = bgr(PANEL)
        # 视频圆角只在四角有非 1 掩码：中间直拷、四角小块混合（避免全视口浮点运算）
        vw, vh = VIEW[2], VIEW[3]
        r = 17
        self._corners = [(y0, y1, x0, x1, self.mask[y0:y1, x0:x1])
                         for y0, y1, x0, x1 in ((0, r, 0, r), (0, r, vw - r, vw),
                                                (vh - r, vh, 0, r), (vh - r, vh, vw - r, vw))]
        self._chip_cache = {}
        self._thumb_key = None
        self._thumbs = []

    # ---------- 预渲染 ----------
    def _build_base(self):
        t = np.linspace(0, 1, H)[:, None, None]
        bg = (np.array(BG_TOP) * (1 - t) + np.array(BG_BOT) * t).astype(np.uint8)
        base = np.ascontiguousarray(np.repeat(bg, W, axis=1)[:, :, [2, 1, 0]])
        cv2.line(base, (0, 64), (W, 64), bgr(BORDER), 1)
        cv2.circle(base, (1120, 32), 5, bgr(self.system[1]), -1, cv2.LINE_AA)
        self.engine.draw_cy(base, self.system[0], 1134, 32, 16, (205, 212, 222))
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

    def _scope_check_sprite(self, checked):
        """勾选框贴片（20×20）：on＝品牌青填充＋深色对钩；off＝深底＋描边。"""
        rgba = rounded_rgba((20, 20), 6, fill=(CYAN if checked else PANEL2),
                            outline=None if checked else BORDER, width=2)
        if checked:
            img = np.ascontiguousarray(rgba[:, :, :3][:, :, ::-1])
            cv2.line(img, (5, 11), (9, 15), bgr(DARK_TXT), 2, cv2.LINE_AA)
            cv2.line(img, (9, 15), (15, 6), bgr(DARK_TXT), 2, cv2.LINE_AA)
            rgba = np.dstack([img[:, :, 2::-1], rgba[:, :, 3]])
        return rgba

    def _scope_button_sprite(self, width, height, text, fg, fill, gradient_to=None):
        """RUN 按钮贴片（RGBA，圆角药丸）；三态共用：idle 青色渐变 / queued 琥珀 / running 暗底。"""
        img = np.empty((height, width, 3), np.uint8)
        if gradient_to is not None:
            tg = np.linspace(0, 1, width)[None, :, None]
            grad = (np.array(bgr(fill)) * (1 - tg) + np.array(bgr(gradient_to)) * tg).astype(np.uint8)
            img[:] = np.repeat(grad, height, 0)
        else:
            img[:] = bgr(fill)
        icy = height // 2
        cv2.circle(img, (26, icy), 8, bgr(fg), 2, cv2.LINE_AA)
        cv2.circle(img, (26, icy), 2, bgr(fg), -1, cv2.LINE_AA)
        self.engine.draw_cy(img, text, (34 + width - 27) // 2 + 2, icy, 15, fg, "Bold", "center")
        cv2.line(img, (width - 26, icy - 6), (width - 19, icy), bgr(fg), 3, cv2.LINE_AA)
        cv2.line(img, (width - 19, icy), (width - 26, icy + 6), bgr(fg), 3, cv2.LINE_AA)
        mask = _mask((width, height), height // 2)
        return np.dstack([img[:, :, 2::-1], (mask[..., 0] * 255).astype(np.uint8)])

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
            for chip, (x0, y0, x1, y1) in state["boxes"]:
                p0 = (int(round(vx + x0 * VIEW_SCALE)), int(round(vy + y0 * VIEW_SCALE)))
                p1 = (int(round(vx + x1 * VIEW_SCALE)), int(round(vy + y1 * VIEW_SCALE)))
                for a, b in ((p0, (p1[0], p0[1])), ((p1[0], p0[1]), p1),
                             (p1, (p0[0], p1[1])), ((p0[0], p1[1]), p0)):
                    cv2.line(canvas, a, b, bgr(GREEN), 2, cv2.LINE_AA)
                self._box_chip(canvas, chip, p0[0], p0[1] - 36)

        self._topbar(canvas, state)
        if state.get("scope"):
            self._scope_panel(canvas, state["scope"], state.get("fresh"))
        if state.get("list") is not None:
            self._list_panel(canvas, video, state["list"])
        return canvas

    def hit_test(self, mx, my):
        """画布坐标 → 交互目标：("toggle", 类别) / ("run", None) / None（非交互区）。"""
        for name in CLASSES:
            x, y, w, h = self.scope_rects[name]
            if x <= mx <= x + w and y <= my <= y + h:
                return ("toggle", name)
        x, y, w, h = self.scope_rects["run"]
        if x <= mx <= x + w and y <= my <= y + h:
            return ("run", None)
        return None

    def _topbar(self, canvas, state):
        cy = 32
        text, bg_rgb = state["badge"]
        tw, th = self.engine.size(text, 14, "SemiBold")
        chip_h = th + 10
        self._chip(canvas, text, 30, cy - chip_h // 2, bg_rgb, size=14)
        px = 30 + tw + 24 + 18
        badge2 = state.get("badge2")
        if badge2:
            t2, bg2 = badge2
            w2, h2 = self.engine.size(t2, 14, "SemiBold")
            self._chip(canvas, t2, px, cy - (h2 + 10) // 2, bg2, size=14)
            px += w2 + 24 + 12
        stext, scolor, sweight = state["status"]
        w1, _ = self.engine.draw_cy(canvas, stext, px, cy, 16, scolor, sweight)
        detail = state.get("detail")
        if detail:
            self.engine.draw_cy(canvas, detail, px + w1 + 16, cy, 13, DIM)
        self.engine.draw_cy(canvas, state["clock"], 1348, cy, 16, (205, 212, 222))

    def _scope_panel(self, canvas, scope, fresh):
        """识别范围表（侧栏顶部）：类别 / 勾选框 / 计数（行悬停高亮）+ FRESHNESS + RUN 按钮。"""
        sx, sy, sw, sh = SCOPE
        pad = 14
        _paste(canvas, self.scope_panel, sx, sy)
        self.engine.draw(canvas, "INSPECTION SCOPE", sx + pad, sy + 12, 15, MAIN, "SemiBold")
        note = scope.get("note")
        if note:
            self.engine.draw(canvas, note, sx + pad, sy + 33, 12, DIM)
        readonly = scope.get("readonly")
        for name in CLASSES:
            rx, ry, rw, rh = self.scope_rects[name]
            cy = ry + rh // 2
            if scope.get("hover") == name:
                _paste(canvas, self.scope_hover, rx, ry + 2)
            checked = bool(scope["selected"].get(name, True))
            if not readonly:
                _paste(canvas, self.scope_check["on" if checked else "off"], sx + pad + 2, cy - 10)
            text_x = sx + pad + (0 if readonly else 34)
            self.engine.draw(canvas, name, text_x, cy - 9, 17,
                             MAIN if (checked or readonly) else DIM, "SemiBold")
            value = scope["counts"].get(name)
            vtext = str(value) if value is not None else "--"
            vw, _ = self.engine.size(vtext, 17, "SemiBold")
            self.engine.draw(canvas, vtext, sx + sw - pad - vw, cy - 9, 17,
                             MAIN if (value is not None and (checked or readonly)) else DIM,
                             "SemiBold")
        fy = sy + 164
        self.engine.draw(canvas, "FRESHNESS", sx + pad, fy, 12, DIM)
        _paste(canvas, self.scope_track, self._scope_bar_x0, fy + 2)
        if fresh is not None:
            frac, color = fresh
            if frac > 0:
                cv2.rectangle(canvas, (self._scope_bar_x0, fy + 2),
                              (self._scope_bar_x0 +
                               int((self._scope_bar_x1 - self._scope_bar_x0) * frac), fy + 9),
                              bgr(color), -1)
        button = scope.get("button")
        if button:
            run = self.scope_rects["run"]
            _paste(canvas, self.scope_button[button], run[0], run[1])

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

    def _list_panel(self, canvas, video, entries):
        """entries=[(chip, bbox, (类别, 分数)|None)...]；chip 用目标原始序号，过滤后不重编号。

        识别范围面板占侧栏上部后，列表为 3 张紧凑卡片 + “+N more”一行。
        """
        rx0, ry0, rx1, ry1 = LPANEL
        _blit(canvas, self.lpanel_img, self.lpanel_keep, rx0, ry0,
              outside_patches=self._lpanel_bg)
        self.engine.draw(canvas, "DETECTED OBJECTS", rx0 + 22, ry0 + 18, 17, MAIN, "SemiBold")
        code = str(len(entries)) if entries else "--"
        bw = self.engine.size(code, 14, "SemiBold")[0] + 24
        self._chip(canvas, code, rx1 - 22 - bw, ry0 + 16, GREEN if entries else PANEL3, size=14,
                   fg=DARK_TXT if entries else DIM)
        boxes = [bbox for _, bbox, _ in entries[:3]]
        shown = self._thumbs_for(video, boxes, (tuple(map(tuple, boxes)), len(boxes)))
        for i, (chip, (x0, y0, x1, y1), label) in enumerate(entries[:3]):
            cy0 = ry0 + 56 + i * 126
            _blit(canvas, self.card_img, self.card_keep, rx0 + 16, cy0, outside_bgr=self.panel_bgr)
            _paste(canvas, shown[i], rx0 + 30, cy0 + 12)
            tx = rx0 + 30 + 88 + 20
            self._chip(canvas, chip, tx, cy0 + 10, GREEN, size=15)
            if label:
                self.engine.draw(canvas, f"{label[0]}  {label[1]}", tx + 52, cy0 + 14, 15, MAIN)
            self.engine.draw(canvas, f"X: {x0}    Y: {y0}", tx, cy0 + 44, 15, DIM)
            self.engine.draw(canvas, f"W: {x1 - x0}    H: {y1 - y0}", tx, cy0 + 68, 15, DIM)
        if len(entries) > 3:
            self.engine.draw(canvas, f"+{len(entries) - 3} more", rx0 + 22, ry1 - 26, 14, DIM)
