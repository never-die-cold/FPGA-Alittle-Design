#!/usr/bin/env python3
"""vision_top sobel 链路黄金参考生成器（模块二，对应 vision_top 级 1b：gauss mux 后串接 sobel）

契约：sobel 语义与 data/golden/vision/sobel/gen_sobel.py 完全一致（Gx/Gy L1 幅值、
8 位饱和、边界复制），此处仅做链路组合：
  expected_gauss_sobel.hex = sobel( gaussian3x3/expected_y.hex )   —— R0 = gauss|sobel 帧
  expected_gray_sobel.hex  = sobel( rgb2gray/expected_y.hex   )   —— R0 = sobel（raw gray）帧
自检：sobel(sobel/input_gray.hex) 必须逐位等于 sobel/expected_y.hex（证明本脚本的
sobel 参考与已归档 golden 同一实现）。
用法：python gen_top_sobel.py   （输出写到脚本所在目录）
"""
import os

W, H = 16, 8
GX = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
GY = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.normpath(os.path.join(HERE, ".."))


def load_hex(path):
    with open(path) as f:
        vals = [int(t, 16) for t in f.read().split()]
    assert len(vals) == W * H, f"{path}: expect {W*H} px, got {len(vals)}"
    return [vals[y * W:(y + 1) * W] for y in range(H)]


def at(img, x, y):
    return img[min(max(y, 0), H - 1)][min(max(x, 0), W - 1)]


def sobel_ref(img):
    out = []
    for y in range(H):
        row = []
        for x in range(W):
            gx = sum(GX[dy + 1][dx + 1] * at(img, x + dx, y + dy)
                     for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            gy = sum(GY[dy + 1][dx + 1] * at(img, x + dx, y + dy)
                     for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            row.append(min(abs(gx) + abs(gy), 255))
        out.append(row)
    return out


def save_hex(name, img):
    with open(os.path.join(HERE, name), "w") as f:
        for y in range(H):
            for x in range(W):
                f.write(f"{img[y][x]:02x}\n")


def main():
    # 自检：本脚本 sobel 参考 vs 已归档 sobel golden（同输入必须同输出）
    ref_in = load_hex(os.path.join(GOLDEN, "sobel", "input_gray.hex"))
    ref_exp = load_hex(os.path.join(GOLDEN, "sobel", "expected_y.hex"))
    assert sobel_ref(ref_in) == ref_exp, "sobel ref mismatch vs archived golden"

    gauss_out = load_hex(os.path.join(GOLDEN, "gaussian3x3", "expected_y.hex"))
    gray_out = load_hex(os.path.join(GOLDEN, "rgb2gray", "expected_y.hex"))
    save_hex("expected_gauss_sobel.hex", sobel_ref(gauss_out))
    save_hex("expected_gray_sobel.hex", sobel_ref(gray_out))
    print(f"PASS: top-sobel golden {W}x{H} x2 (gauss|sobel, gray|sobel), ref self-check OK")


if __name__ == "__main__":
    main()
