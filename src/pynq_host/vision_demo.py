#!/usr/bin/env python3
"""vision_demo —— M2 上板演示序列（A1 参数化 + A4 OSD 动效）

依赖：PYNQ 板卡 + vision overlay（axi_regs 映射窗口）。上板当日运行；
PC 上仅可做 import/语法检查（python -c "import vision_demo"）。

分辨率/帧率口径（决策单 D1/D3，2026-09-30 拍板）：源设备输出 1280x720@30 或 @60
决定像素钟（37.125 / 74.25 MHz）——**切 60 = 把源（HDMI 摄像头/笔记本）设成 720p60**，
PL 时序随源自适应（各级自产标记），软件无需干预。

演示序列（对应 10/12 M2 gate 叙事）：
  1) GRAY        —— 灰度直通基线（延迟最小，画面黑白）
  2) GAUSS       —— 高斯柔化（处理前后对比最直观）
  3) GAUSS_SOBEL —— 边缘检测（全分辨率）
  4) OSD 框动效  —— 检测框沿对角线扫动（A4：写 R1-R5，帧边界生效自动量化）
  5) SNAPSHOT    —— 快照分支点亮（cop 窗口有缩放流，显示不变）
"""
import time

from vision_regs import VisionRegs, PRESETS

# AXI_GP0 映射窗口内 axi_regs 基址——overlay 布局定稿后回填（XDC/BD 地址编辑器）
AXI_REGS_BASE = None


def sweep_box(v: VisionRegs, cycles: int = 60, w: int = 1280, h: int = 720,
              box_w: int = 160, box_h: int = 120, fps: float = 30.0):
    """A4 动效：检测框沿对角线往返扫动。写快于帧率无妨（RTL 帧首锁存按帧量化）。"""
    dt = 1.0 / fps
    for i in range(cycles):
        t = i / cycles
        x = int((w - box_w) * (abs((t * 2) % 2 - 1)))
        y = int((h - box_h) * (abs((t * 2) % 2 - 1)))
        v.set_box(x, y, x + box_w, y + box_h, color=0xFF)
        time.sleep(dt)


def main():
    assert AXI_REGS_BASE is not None, "overlay 布局定稿后回填 AXI_REGS_BASE"
    v = VisionRegs(base=AXI_REGS_BASE)
    seq = ["GRAY", "GAUSS", "GAUSS_SOBEL", "GRAY_SOBEL"]
    for name in seq:                       # A1 参数化：逐拓扑停留 5s
        print(f"topology -> {name}")
        v.apply_preset(name)
        time.sleep(5)
    print("OSD box sweep (A4)")
    v.set_enable(osd=1)
    v.set_roi(40, 40, 640, 380, color=0x3C)
    sweep_box(v)
    print("SNAPSHOT on (显示不变，cop 口出 DWxDH 缩放流)")
    v.apply_preset("GAUSS_SNAPSHOT")
    time.sleep(5)
    print("demo done")


if __name__ == "__main__":
    main()
