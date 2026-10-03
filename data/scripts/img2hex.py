#!/usr/bin/env python3
"""img2hex —— 任意图片 -> 模块二灰度 hex（真实测试图替换通路，需求单 §6"≥3 张真实图"）

用法：
  python img2hex.py <图片路径> [--width 1280] [--height 720] [--out input_gray.hex]
  python img2hex.py photo.jpg -w 32 -H 16 -o data/golden/vision/scaler_ds/input_gray.hex

行为：
  1. 读图（PIL 支持jpg/png/bmp等），转灰度（BT.601，与 rgb2gray 同矩阵）；
  2. resize 到 --width x --height（默认 1280x720，即演示源分辨率）；
  3. 输出每像素一行两位 hex（tb $readmemh / gen 脚本同格式）。
真实图进 golden 的流程：img2hex 生成 input -> 手工或脚本喂 gen_*.py 的参考实现算
expected -> 回归。自拍图（斜线/棋盘/人脸纹理）拍好后即用本工具入库。
"""
import argparse
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow：pip install pillow")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("-w", "--width", type=int, default=1280)
    ap.add_argument("-H", "--height", type=int, default=720)
    ap.add_argument("-o", "--out", default="input_gray.hex")
    a = ap.parse_args()

    img = Image.open(a.image).convert("L")          # BT.601 等效灰度（PIL L = 0.299R+0.587G+0.114B）
    img = img.resize((a.width, a.height), Image.BILINEAR)
    px = list(img.getdata())
    with open(a.out, "w") as f:
        for v in px:
            f.write(f"{v:02x}\n")
    print(f"PASS: {a.image} -> {a.out} ({a.width}x{a.height}, {a.width*a.height} px, BT.601 gray)")


if __name__ == "__main__":
    main()
