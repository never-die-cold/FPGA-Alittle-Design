#!/usr/bin/env python3
"""rgb2gray 黄金参考生成器（模块二，对应 src/vision/design_v0.md §3/§4）

生成：
  input_rgb.hex   测试图逐像素 24bit RGB888（每行一像素）
  expected_y.hex  契约定点公式 Y = (77R + 150G + 29B) >> 8 的期望输出（每行一字节）
自检：定点公式 vs 浮点理想值 (77R+150G+29B)/256 的最大绝对误差 <= 1 LSB。
用法：python gen_rgb2gray.py   （输出写到脚本所在目录）
"""
import os

W, H = 16, 8
MASK8 = 0xFF


def gen_image():
    """程序化测试图：水平渐变 + 棋盘 + 四角饱和值，覆盖中间值与极值。"""
    px = []
    for y in range(H):
        for x in range(W):
            if (x // 2 + y // 2) % 2 == 0:      # 棋盘基色
                r, g, b = 32, 200, 90
            else:
                r, g, b = 210, 40, 160
            r = min(255, r + x * 14)            # 水平渐变
            g = min(255, g + y * 8)
            if (x, y) in {(0, 0), (W - 1, H - 1)}:
                r, g, b = 255, 255, 255          # 白角
            if (x, y) in {(W - 1, 0), (0, H - 1)}:
                r, g, b = 0, 0, 0                # 黑角
            px.append((r, g, b))
    return px


def spec_y(r, g, b):
    return (77 * r + 150 * g + 29 * b) >> 8


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    px = gen_image()
    with open(os.path.join(here, "input_rgb.hex"), "w") as fi, \
         open(os.path.join(here, "expected_y.hex"), "w") as fe:
        for (r, g, b) in px:
            fi.write(f"{(r << 16) | (g << 8) | b:06x}\n")
            fe.write(f"{spec_y(r, g, b):02x}\n")

    max_err = 0
    for (r, g, b) in px:
        ideal = (77 * r + 150 * g + 29 * b) / 256.0
        max_err = max(max_err, abs(spec_y(r, g, b) - ideal))
    assert max_err <= 1.0, f"定点公式与浮点理想值偏差超界: {max_err}"
    print(f"PASS: rgb2gray golden {W}x{H}={W*H} px, max|int-float| err={max_err:.3f} LSB")


if __name__ == "__main__":
    main()
