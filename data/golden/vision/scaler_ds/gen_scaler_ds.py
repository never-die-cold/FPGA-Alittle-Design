#!/usr/bin/env python3
"""scaler 缩小档黄金参考生成器（模块二第二尺寸档，需求单 design_v0.md §6"两组尺寸档"之缩小档）

契约与 gen_scaler.py 完全一致（16.16 定点双线性），差异仅尺寸与测试图：
  SW=32 SH=16 -> DW=8 DH=4（缩小档，SH/DH=4 <= NLINES-2=6，覆盖行槽滑动复用路径——
  放大档 16x8->32x16 不触发行槽重用，缩小档才是真实 720p->CNN 输入的工作模式）。
  测试图：斜线 + 棋盘块 + 水平渐变混合纹理（替代单一棋盘，提供高频细节检查缩小后的
  混叠表现，黄金与 RTL 逐位一致故混叠本身即为期望值）。
自检：定点结果 vs 浮点理想值最大绝对误差 <= 2 LSB。
用法：python gen_scaler_ds.py   （输出写到脚本所在目录）
"""
import os

SW, SH = 32, 16
DW, DH = 8, 4
FR = 16
FXH = 8


def gen_gray():
    """混合纹理：斜线族 + 4x4 棋盘 + 水平渐变，加两个极性锚点。"""
    px = []
    for y in range(SH):
        for x in range(SW):
            if (x - y) % 8 == 0:                      # 斜线族（45°，周期 8）
                v = 220
            elif (x // 4 + y // 4) % 2 == 0:          # 4x4 棋盘块
                v = 30 + x * 2
            else:                                      # 水平渐变底
                v = 90 + (x * 5) % 120
            if (x, y) == (0, 0):
                v = 255
            if (x, y) == (SW - 1, SH - 1):
                v = 0
            px.append(min(255, v))
    return [px[y * SW:(y + 1) * SW] for y in range(SH)]


def at(img, x, y):
    return img[min(max(y, 0), SH - 1)][min(max(x, 0), SW - 1)]


def src_coord(d, src_len, dst_len):
    # (2d+1)S/(2D) - 0.5 的 16.16 定点，向零截断，clamp 后取 floor 与小数高 8 位
    acc = (2 * d + 1) * src_len * (1 << FR) // (2 * dst_len) - (1 << (FR - 1))
    c = acc >> FR
    if acc < 0:
        c = 0
        acc = 0
    if c > src_len - 1:
        c = src_len - 1
        acc = (src_len - 1) << FR
    return c, min(acc - (c << FR), (1 << FR) - 1) >> (FR - FXH), acc


def lerp8(a, b, f):
    return ((256 - f) * a + f * b) >> 8


def spec_scale(img, xd, yd):
    x0, fx, _ = src_coord(xd, SW, DW)
    y0, fy, _ = src_coord(yd, SH, DH)
    x1 = min(x0 + 1, SW - 1)
    y1 = min(y0 + 1, SH - 1)
    top = lerp8(at(img, x0, y0), at(img, x1, y0), fx)
    bot = lerp8(at(img, x0, y1), at(img, x1, y1), fx)
    return lerp8(top, bot, fy)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = gen_gray()
    # 自检：定点 vs 浮点理想值（同坐标公式、无定点截断）误差 <= 2 LSB
    def fat(x, y):
        return img[min(max(y, 0), SH - 1)][min(max(x, 0), SW - 1)]
    max_err = 0
    for yd in range(DH):
        for xd in range(DW):
            fx_f = (2 * xd + 1) * SW / (2 * DW) - 0.5
            fy_f = (2 * yd + 1) * SH / (2 * DH) - 0.5
            x0f, y0f = max(0, min(SW - 1, int(fx_f // 1))), max(0, min(SH - 1, int(fy_f // 1)))
            x1f, y1f = min(x0f + 1, SW - 1), min(y0f + 1, SH - 1)
            fxf = max(0.0, fx_f - (int(fx_f) if fx_f >= 0 else 0))
            fyf = max(0.0, fy_f - (int(fy_f) if fy_f >= 0 else 0))
            top = (1 - fxf) * fat(x0f, y0f) + fxf * fat(x1f, y0f)
            bot = (1 - fxf) * fat(x0f, y1f) + fxf * fat(x1f, y1f)
            ideal = (1 - fyf) * top + fyf * bot
            max_err = max(max_err, abs(spec_scale(img, xd, yd) - round(ideal)))
    assert max_err <= 2, f"定点 vs 浮点误差 {max_err} LSB > 2"

    with open(os.path.join(here, "input_gray.hex"), "w") as fi, \
         open(os.path.join(here, "expected_y.hex"), "w") as fe:
        for y in range(SH):
            for x in range(SW):
                fi.write(f"{img[y][x]:02x}\n")
        for yd in range(DH):
            for xd in range(DW):
                fe.write(f"{spec_scale(img, xd, yd):02x}\n")
    print(f"PASS: scaler_ds golden {SW}x{SH}->{DW}x{DH} downscale, "
          f"fixedpoint-vs-float max_err={max_err} LSB (<=2)")


if __name__ == "__main__":
    main()
