#!/usr/bin/env python3
"""scaler 黄金参考生成器（模块二，对应 src/vision/design_v0.md §3.1 / scaler.v 头注释）

契约（与 RTL 逐位一致的 16.16 定点双线性）：
  x_src(xd) = (2*xd+1)*SW/(2*DW) - 0.5，clamp 到 [0, SW-1]；y 同。
  x0 = floor(clamp)，x1 = min(x0+1, SW-1)；fx = frac 的高 8 位。
  out = lerp( lerp(P(y0,x0), P(y0,x1), fx), lerp(P(y1,x0), P(y1,x1), fx), fy )
生成：
  input_gray.hex   源灰度图（与 gaussian3x3 同一张 16x8 测试图，SW x SH）
  expected_y.hex   目标尺寸 DW x DH 期望输出
自检：定点结果 vs 浮点理想值最大绝对误差 <= 2 LSB。
用法：python gen_scaler.py   （输出写到脚本所在目录）
"""
import os

SW, SH = 16, 8
DW, DH = 32, 16
FR = 16                     # 定点小数位
FXH = 8                     # 插值使用的 frac 高位宽


def gen_gray():
    """与 gen_gaussian3x3.py 同一张程序化测试图（契约公式转灰度）。"""
    px = []
    for y in range(SH):
        for x in range(SW):
            if (x // 2 + y // 2) % 2 == 0:
                r, g, b = 32, 200, 90
            else:
                r, g, b = 210, 40, 160
            r = min(255, r + x * 14)
            g = min(255, g + y * 8)
            if (x, y) in {(0, 0), (SW - 1, SH - 1)}:
                r, g, b = 255, 255, 255
            if (x, y) in {(SW - 1, 0), (0, SH - 1)}:
                r, g, b = 0, 0, 0
            px.append((77 * r + 150 * g + 29 * b) >> 8)
    return [px[y * SW:(y + 1) * SW] for y in range(SH)]


def at(img, x, y):
    return img[min(max(y, 0), SH - 1)][min(max(x, 0), SW - 1)]


def src_coord(d, src_len, dst_len):
    """定点源坐标：返回 (i0, i1, f8)，与 RTL 的 16.16 累加/钳位逐位一致。"""
    step = (src_len << FR) // dst_len
    init = ((src_len - dst_len) << (FR - 1)) // dst_len
    acc = init + d * step
    v = max(acc, 0)                          # 负相位钳到 0
    i0 = min(v >> FR, src_len - 1)
    i1 = min(i0 + 1, src_len - 1)
    f8 = (v & 0xFFFF) >> (FR - FXH)
    return i0, i1, f8


def lerp8(a, b, f):
    return ((256 - f) * a + f * b) >> FXH


def spec_scale(img, xd, yd):
    x0, x1, fx = src_coord(xd, SW, DW)
    y0, y1, fy = src_coord(yd, SH, DH)
    top = lerp8(at(img, x0, y0), at(img, x1, y0), fx)
    bot = lerp8(at(img, x0, y1), at(img, x1, y1), fx)
    return lerp8(top, bot, fy)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = gen_gray()
    with open(os.path.join(here, "input_gray.hex"), "w") as fi, \
         open(os.path.join(here, "expected_y.hex"), "w") as fe:
        for yd in range(DH):
            for xd in range(DW):
                fe.write(f"{spec_scale(img, xd, yd):02x}\n")
        for y in range(SH):
            for x in range(SW):
                fi.write(f"{img[y][x]:02x}\n")

    max_err = 0.0
    for yd in range(DH):
        for xd in range(DW):
            x0, x1, fx = src_coord(xd, SW, DW)
            y0, y1, fy = src_coord(yd, SH, DH)
            fs, fyf = fx / 256.0, fy / 256.0
            ideal = ((1 - fs) * (1 - fyf) * at(img, x0, y0) + fs * (1 - fyf) * at(img, x1, y0)
                     + (1 - fs) * fyf * at(img, x0, y1) + fs * fyf * at(img, x1, y1))
            max_err = max(max_err, abs(spec_scale(img, xd, yd) - ideal))
    assert max_err <= 2.0, f"定点与浮点理想值偏差超界: {max_err}"
    print(f"PASS: scaler golden {SW}x{SH}->{DW}x{DH}, max|int-float| err={max_err:.3f} LSB")


if __name__ == "__main__":
    main()
