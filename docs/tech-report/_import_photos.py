# -*- coding: utf-8 -*-
"""一次性：把评审插图转名、缩放、压缩入 figures/（用后可删）。"""
import os
from PIL import Image

SRC = r"D:\Desktop\contests\2026fpga\技术文档插图"
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
MAP = {
    "整机工位图.jpg": "photo_workstation.jpg",
    "板卡与树莓派.jpg": "photo_board_pi.jpg",
    "板卡特写.jpg": "photo_board_closeup.jpg",
    "前端界面（包含采集卡回传信息）.png": "webui_live.png",
}
for src_name, dst_name in MAP.items():
    im = Image.open(os.path.join(SRC, src_name))
    if max(im.width, im.height) > 1600:
        s = 1600 / max(im.width, im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    out = os.path.join(DST, dst_name)
    if dst_name.endswith(".jpg"):
        im.convert("RGB").save(out, quality=88, optimize=True)
    else:
        im.save(out, optimize=True)
    print(dst_name, im.size, os.path.getsize(out), "bytes")
