#!/usr/bin/env python3
"""gaussian_3x3 黄金参考生成器（模块二，对应 src/vision/design_v0.md §3/§4）

生成：
  input_gray.hex  3x3 窗口输入（内部先按 rgb2gray 契约公式转灰度，与上级链路一致）
  expected_y.hex  高斯核 [1 2 1;2 4 2;1 2 1]/16、边界像素复制的期望输出
自检：定点整数实现 vs 浮点理想值最大绝对误差 <= 1 LSB；边界像素复制策略显式核对。
用法：python gen_gaussian3x3.py   （输出写到脚本所在目录）
"""
import os

W, H = 16, 8
KERNEL = [[1, 2, 1], [2, 4, 2], [1, 2, 1]]


def gen_gray():
    """与 gen_rgb2gray.py 同一张程序化测试图，按契约公式转灰度。"""
    px = []
    for y in range(H):
        for x in range(W):
            if (x // 2 + y // 2) % 2 == 0:
                r, g, b = 32, 200, 90
            else:
                r, g, b = 210, 40, 160
            r = min(255, r + x * 14)
            g = min(255, g + y * 8)
            if (x, y) in {(0, 0), (W - 1, H - 1)}:
                r, g, b = 255, 255, 255
            if (x, y) in {(W - 1, 0), (0, H - 1)}:
                r, g, b = 0, 0, 0
            px.append((77 * r + 150 * g + 29 * b) >> 8)
    return px


def at(img, x, y):
    """边界复制（replicate）：坐标钳到图内。"""
    return img[min(max(y, 0), H - 1)][min(max(x, 0), W - 1)]


def spec_gauss(img, x, y):
    acc = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            acc += KERNEL[dy + 1][dx + 1] * at(img, x + dx, y + dy)
    return acc >> 4


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rows = [gen_gray()[y * W:(y + 1) * W] for y in range(H)]
    with open(os.path.join(here, "input_gray.hex"), "w") as fi, \
         open(os.path.join(here, "expected_y.hex"), "w") as fe:
        for y in range(H):
            for x in range(W):
                fi.write(f"{rows[y][x]:02x}\n")
                fe.write(f"{spec_gauss(rows, x, y):02x}\n")

    max_err = 0
    for y in range(H):
        for x in range(W):
            ideal = sum(KERNEL[dy + 1][dx + 1] * at(rows, x + dx, y + dy)
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 16.0
            max_err = max(max_err, abs(spec_gauss(rows, x, y) - ideal))
    assert max_err <= 1.0, f"定点实现与浮点理想值偏差超界: {max_err}"
    # 边界抽查：四角像素只用到复制进来的邻居
    corner = spec_gauss(rows, 0, 0)
    expect_corner = (1 * rows[0][0] + 2 * rows[0][0] + 1 * rows[0][1] +
                     2 * rows[0][0] + 4 * rows[0][0] + 2 * rows[0][1] +
                     1 * rows[1][0] + 2 * rows[1][0] + 1 * rows[1][1]) >> 4
    assert corner == expect_corner, "边界复制策略与预期不符"
    print(f"PASS: gaussian3x3 golden {W}x{H}={W*H} px, max|int-float| err={max_err:.3f} LSB, border OK")


if __name__ == "__main__":
    main()
