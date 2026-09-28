#!/usr/bin/env python3
"""全链黄金参考生成器（模块二）：rgb2gray → gaussian_3x3 → scaler（16x8→32x16）

各级公式与各自单级 golden 生成器逐位一致（单级已分别对拍验证，组合即链期望）：
  gray = (77R+150G+29B)>>8（gen_rgb2gray.py）
  gauss = [1 2 1;2 4 2;1 2 1]/16，边界复制（gen_gaussian3x3.py）
  scaler：源 = gauss 输出，16.16 定点双线性 16x8→32x16（gen_scaler.py）
生成：
  expected_fullchain.hex  全链末端 32x16 = 512 像素期望（tb_fullchain 对拍用）
输入图复用 ../rgb2gray/input_rgb.hex（同一张测试图）。
用法：python gen_fullchain.py
"""
import os

SW, SH = 16, 8      # scaler 源尺寸（= gaussian 输出）
DW, DH = 32, 16
FR, FXH = 16, 8
KERNEL = [[1, 2, 1], [2, 4, 2], [1, 2, 1]]


def at(img, x, y, w, h):
    return img[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]


def spec_gauss(rows, x, y):
    acc = sum(KERNEL[dy + 1][dx + 1] * at(rows, x + dx, y + dy, SW, SH)
              for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return acc >> 4


def src_coord(d, src_len, dst_len):
    step = (src_len << FR) // dst_len
    init = ((src_len - dst_len) << (FR - 1)) // dst_len
    v = max(init + d * step, 0)
    i0 = min(v >> FR, src_len - 1)
    i1 = min(i0 + 1, src_len - 1)
    return i0, i1, (v & 0xFFFF) >> (FR - FXH)


def lerp8(a, b, f):
    return ((256 - f) * a + f * b) >> FXH


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # 读入 rgb 测试图，重算 gray（公式同 gen_rgb2gray.py）
    rgb = [int(line, 16) for line in open(os.path.join(here, "../rgb2gray/input_rgb.hex"))]
    gray_flat = [(77 * ((p >> 16) & 0xFF) + 150 * ((p >> 8) & 0xFF) + 29 * (p & 0xFF)) >> 8
                 for p in rgb]
    rows = [gray_flat[y * SW:(y + 1) * SW] for y in range(SH)]

    gauss = [[spec_gauss(rows, x, y) for x in range(SW)] for y in range(SH)]

    with open(os.path.join(here, "expected_fullchain.hex"), "w") as fe:
        for yd in range(DH):
            for xd in range(DW):
                x0, x1, fx = src_coord(xd, SW, DW)
                y0, y1, fy = src_coord(yd, SH, DH)
                top = lerp8(at(gauss, x0, y0, SW, SH), at(gauss, x1, y0, SW, SH), fx)
                bot = lerp8(at(gauss, x0, y1, SW, SH), at(gauss, x1, y1, SW, SH), fx)
                fe.write(f"{lerp8(top, bot, fy):02x}\n")

    # 自检：链首 gray 与既有 gray golden 一致、高斯行列边界值与 gen_gaussian3x3 一致
    ref_gray = [int(line, 16) for line in open(os.path.join(here, "../rgb2gray/expected_y.hex"))]
    assert gray_flat == ref_gray, "链首 gray 与单级 golden 不一致"
    ref_gauss = [int(line, 16) for line in open(os.path.join(here, "../gaussian3x3/expected_y.hex"))]
    gauss_flat = [gauss[y][x] for y in range(SH) for x in range(SW)]
    assert gauss_flat == ref_gauss, "高斯级与单级 golden 不一致"
    print(f"PASS: fullchain golden gray+gauss 与单级一致, scaler {SW}x{SH}->{DW}x{DH} = {DW*DH} px")


if __name__ == "__main__":
    main()
