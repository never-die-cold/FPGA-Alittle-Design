"""hud_text.py —— Pillow 文本引擎（HUD v4：以真实字体替代 Hershey 矢量字体）。

- 字体：随包分发的开源字体（assets/fonts/，OFL 协议；当前 Inter 变量字体，
  中文类别名待 M3 引入 Noto Sans SC 子集）。
- 渲染：文本 -> RGBA numpy 贴图并缓存（key = 文本/字号/字重/颜色），每帧仅做
  alpha 混合贴图；缓存满额整体清空（动态文本如时钟/计数不会无限增长）。
- 寻径：源码运行与 PyInstaller 打包（sys._MEIPASS）统一走 asset_path()。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CACHE_LIMIT = 1024


def asset_path(*parts):
    """源码运行 = 本文件旁 assets/；打包运行 = sys._MEIPASS 下（PyInstaller --add-data）。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath("assets", *parts)


class TextEngine:
    """字体句柄 + 文本贴图缓存。color 为 RGB 三元组。"""

    def __init__(self, font_file="InterVariable.ttf"):
        self.path = str(asset_path("fonts", font_file))
        self._fonts = {}
        self._cache = {}

    def _font(self, size, weight):
        key = (size, weight)
        font = self._fonts.get(key)
        if font is None:
            font = ImageFont.truetype(self.path, size)
            if weight:
                try:
                    font.set_variation_by_name(weight)  # 变量字体按名称取字重
                except (OSError, ValueError):
                    pass  # 静态字体或名称不匹配：保持默认字重
            self._fonts[key] = font
        return font

    def advance(self, text, size, weight="Regular"):
        return self._font(size, weight).getlength(text)

    def render(self, text, size, color, weight="Regular"):
        """返回 (rgba_ndarray, w, h)；同名同参数命中缓存。"""
        key = (text, size, tuple(color), weight)
        hit = self._cache.get(key)
        if hit is None:
            font = self._font(size, weight)
            left, top, right, bottom = font.getbbox(text)
            w, h = max(right - left, 1), max(bottom - top, 1)
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(canvas).text((-left, -top), text, font=font,
                                        fill=tuple(color) + (255,))
            hit = np.asarray(canvas)
            if len(self._cache) >= CACHE_LIMIT:
                self._cache.clear()
            self._cache[key] = hit
        return hit, hit.shape[1], hit.shape[0]

    def size(self, text, size, weight="Regular"):
        left, top, right, bottom = self._font(size, weight).getbbox(text)
        return max(right - left, 1), max(bottom - top, 1)

    def draw_cy(self, frame, text, x, cy, size, color, weight="Regular", align="left"):
        """以文本**实际墨迹像素**的垂直中心对准 cy 贴图。

        注意不能按包围盒中心：如 "7" 的盒≈墨迹，而 "--" 的盒高 13px 里墨迹只占 5px 左右，
        按盒居中会让短横线明显偏上（2026-10-09 实测修正）。
        """
        arr, _, h = self.render(text, size, color, weight)
        rows = np.where(arr[:, :, 3].any(axis=1))[0]
        ink_cy = (float(rows.min()) + float(rows.max())) / 2.0 if len(rows) else h / 2.0
        return self.draw(frame, text, x, int(round(cy - ink_cy)), size, color, weight, align)

    def draw(self, frame, text, x, y, size, color, weight="Regular", align="left"):
        """把文本以 alpha 混合贴到 BGR 帧；align 按文本宽做 left/center/right，y 为顶边。"""
        img, w, h = self.render(text, size, color, weight)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
            return w, h
        roi = frame[y:y + h, x:x + w]
        alpha = img[:, :, 3:4].astype(np.float32) / 255.0
        bgr = img[:, :, 2::-1].astype(np.float32)
        roi[:] = (bgr * alpha + roi.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)
        return w, h
