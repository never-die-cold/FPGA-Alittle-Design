#!/usr/bin/env python3
"""make_replay_scene —— 回放源素材生成器（纯标准库：PGM 帧 + ffmpeg concat 清单）

用途：Pi 经 HDMI 循环播放 → PYNQ HDMI IN。服务 M2 换源/EDID/断连测试与 M3 验收
用例（重复帧不重复计数、缺件、多余件、空场景）。合成灰底矩形场景仅覆盖链路与
验收动作，不代表识别精度；数据集像素必须经 PYNQ readframe 采集
（fastener-data-collection-protocol.md §1），本工具产物不用于训练。

输出 <out>/：
  scene_XX_<名>.pgm   720p 灰度帧，每场景一文件（相同场景复用同文件=逐像素相同的重复帧段）
  concat.txt          ffmpeg concat demuxer 清单（含 duration）
组装（在有 ffmpeg 的机器上，Pi 侧 sudo apt install ffmpeg）：
  ffmpeg -f concat -safe 0 -i <out>/concat.txt -vf fps=60 -pix_fmt yuv420p replay.mp4
"""
import argparse
from pathlib import Path

W, H = 1280, 720
BG = 240

def scene(parts):
    """背景 240 + 每件零件确定性纹理（与 arm_localize_bench 同视觉语言）。"""
    image = [[BG] * W for _ in range(H)]
    for index, (x0, y0, width, height) in enumerate(parts):
        for y in range(y0, y0 + height):
            for x in range(x0, x0 + width):
                image[y][x] = 20 + index * 7 + ((x - x0) + 2 * (y - y0)) % 13
    return image

# 场景表：自由分散互不遮挡；名称对应 M3 验收用例
SCENES = {
    "empty":   [],
    "normal":  [(120, 120, 48, 32), (560, 200, 64, 40), (950, 420, 72, 52)],
    "extra":   [(120, 120, 48, 32), (560, 200, 64, 40), (950, 420, 72, 52), (300, 500, 40, 28)],
    "missing": [(120, 120, 48, 32), (950, 420, 72, 52)],
}
# 播放序列：normal 连续两段=同像素重复帧段（验"重复不双计"），随后多余/正常/缺件/空
SEQUENCE = ["normal", "normal", "extra", "normal", "missing", "empty"]

def write_pgm(path, image):
    body = bytearray()
    for row in image:
        body.extend(row)
    path.write_bytes(f"P5\n{W} {H}\n255\n".encode("ascii") + bytes(body))

def main():
    parser = argparse.ArgumentParser(description="生成 Pi 回放源 PGM 场景与 ffmpeg concat 清单")
    parser.add_argument("--out", default="sim/build/replay_scene")
    parser.add_argument("--hold", type=int, default=60, help="每场景持续帧数 @60fps（默认 60=1s）")
    args = parser.parse_args()
    if args.hold < 1:
        raise SystemExit("hold must be >= 1")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rendered = {}
    lines = ["# ffmpeg concat demuxer 清单（duration 单位秒）"]
    for name in SEQUENCE:
        if name not in rendered:
            path = out / f"scene_{len(rendered):02d}_{name}.pgm"
            write_pgm(path, scene(SCENES[name]))
            rendered[name] = path.name
        lines.append(f"file '{rendered[name]}'")
        lines.append(f"duration {args.hold / 60.0:.6f}")
    # concat 规范：末条 file 需重复一次，最后一个 duration 才生效
    lines.append(f"file '{rendered[SEQUENCE[-1]]}'")
    (out / "concat.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: {len(rendered)} scenes -> {out}")
    print(f"assemble: ffmpeg -f concat -safe 0 -i {out}/concat.txt "
          f"-vf fps=60 -pix_fmt yuv420p {out}/replay.mp4")

if __name__ == "__main__":
    main()
