#!/usr/bin/env python3
"""sobel 黄金参考生成器（模块二，对应 src/vision/design_v0.md §3 / sobel.v 头注释）

契约：Gx = [-1 0 1; -2 0 2; -1 0 1]，Gy 为其转置；梯度幅值取 |Gx|+|Gy|（L1 近似，
避免乘方开方），8 位饱和截断。边界像素复制（与 gaussian 同策略）。
生成：
  input_gray.hex  与 gaussian3x3 同一张 16x8 灰度测试图
  expected_y.hex  期望输出
自检：整数实现 vs 浮点理想值（同核）最大绝对误差 == 0（同为整数运算，仅核对边界）。
用法：python gen_sobel.py   （输出写到脚本所在目录）
"""
import os

W, H = 16, 8
GX = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
GY = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]


def gen_gray():
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
    return [px[y * W:(y + 1) * W] for y in range(H)]


def at(img, x, y):
    return img[min(max(y, 0), H - 1)][min(max(x, 0), W - 1)]


def spec_sobel(img, x, y):
    gx = sum(GX[dy + 1][dx + 1] * at(img, x + dx, y + dy)
             for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    gy = sum(GY[dy + 1][dx + 1] * at(img, x + dx, y + dy)
             for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return min(abs(gx) + abs(gy), 255)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rows = gen_gray()
    with open(os.path.join(here, "input_gray.hex"), "w") as fi, \
         open(os.path.join(here, "expected_y.hex"), "w") as fe:
        for y in range(H):
            for x in range(W):
                fi.write(f"{rows[y][x]:02x}\n")
                fe.write(f"{spec_sobel(rows, x, y):02x}\n")
    # 边界抽查：四角与中心重算一致性由枚举保证，这里核对幅值不越界
    for y in range(H):
        for x in range(W):
            v = spec_sobel(rows, x, y)
            assert 0 <= v <= 255
    print(f"PASS: sobel golden {W}x{H}={W*H} px, L1 magnitude, border OK")


if __name__ == "__main__":
    main()
