#!/usr/bin/env python3
"""osd_overlay 黄金参考生成器（模块二，对应 src/vision/design_v0.md §3.1 / osd_overlay.v）

契约：灰度流直通，两个 1px 描边框（检测框 box / ROI）内嵌输出，命中位置以各自
颜色替换；重叠处 box 优先。框参数在帧首 vs 锁存，帧内变更不影响当前帧。
生成（两帧，参数不同，用于锁存语义验证）：
  input_y.hex            灰度输入（复用 rgb2gray golden 同一张测试图）
  expected_osd_f1.hex    帧 1：box=(2,1)-(7,5) 色 FF；roi=(10,3)-(14,7) 色 00
  expected_osd_f2.hex    帧 2：box=(4,2)-(9,6) 色 55；roi 同帧 1
用法：python gen_osd.py
"""
import os
import shutil

W, H = 16, 8
F1 = dict(bx=(2, 1, 7, 5), bc=0xFF, rx=(10, 3, 14, 7), rc=0x00)
F2 = dict(bx=(4, 2, 9, 6), bc=0x55, rx=(10, 3, 14, 7), rc=0x00)


def border_hit(x, y, box):
    x0, y0, x1, y1 = box
    in_x, in_y = x0 <= x <= x1, y0 <= y <= y1
    return in_x and in_y and (x in (x0, x1) or y in (y0, y1))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "../rgb2gray/expected_y.hex")
    shutil.copyfile(src, os.path.join(here, "input_y.hex"))
    px = [int(l, 16) for l in open(src)]

    for name, cfg in (("expected_osd_f1.hex", F1), ("expected_osd_f2.hex", F2)):
        with open(os.path.join(here, name), "w") as f:
            for y in range(H):
                for x in range(W):
                    v = px[y * W + x]
                    if border_hit(x, y, cfg["bx"]):
                        v = cfg["bc"]
                    elif border_hit(x, y, cfg["rx"]):
                        v = cfg["rc"]
                    f.write(f"{v:02x}\n")
    n1 = sum(border_hit(x, y, F1["bx"]) or border_hit(x, y, F1["rx"])
             for y in range(H) for x in range(W))
    assert n1 > 0, "帧 1 无任何框命中，golden 无效"
    print(f"PASS: osd golden 2 frames, {W*H} px each, f1 border px={n1}")


if __name__ == "__main__":
    main()
