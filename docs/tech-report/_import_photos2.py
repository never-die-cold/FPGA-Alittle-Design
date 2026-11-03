# -*- coding: utf-8 -*-
"""一次性：把 2026-11-03 实验室实拍与新版界面截图入库到 figures/。"""
import os
from PIL import Image

SRC = r"D:\Desktop\contests\2026fpga\技术文档插图"
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
MAP = {
    "整机实物图2.jpg": "photo_workstation2.jpg",
    "板卡与树莓派2.jpg": "photo_board_pi2.jpg",
    "板卡特写2.jpg": "photo_board_closeup2.jpg",
    "摄像头特写.jpg": "photo_camera.jpg",
    "前端界面2.png": "webui_live2.png",
}
for src_name, dst_name in MAP.items():
    im = Image.open(os.path.join(SRC, src_name))
    # 照片最长边 1600；界面截图保持原宽但不超过 2000
    limit = 2000 if dst_name.endswith(".png") else 1600
    if max(im.width, im.height) > limit:
        s = limit / max(im.width, im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    out = os.path.join(DST, dst_name)
    if dst_name.endswith(".jpg"):
        im.convert("RGB").save(out, quality=88, optimize=True)
    else:
        im.save(out, optimize=True)
    print(dst_name, im.size, os.path.getsize(out), "bytes")
