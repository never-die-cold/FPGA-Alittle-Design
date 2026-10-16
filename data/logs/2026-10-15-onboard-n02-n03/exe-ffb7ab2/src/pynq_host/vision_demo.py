#!/usr/bin/env python3
"""vision_demo —— M2 分析参数调试序列（实际板端运行待验证）

依赖：PYNQ 板卡 + vision overlay（axi_regs 映射窗口）。上板当日运行；
PC 上仅可做 import/语法检查（python -c "import vision_demo"）。

分辨率/帧率口径（决策单 D1/D3，2026-09-30 拍板）：源设备输出 1280x720@30 或 @60
决定像素钟（37.125 / 74.25 MHz）——**切 60 = 把源（HDMI 摄像头/笔记本）设成 720p60**，
PL 时序随源自适应（各级自产标记），软件无需干预。

演示序列（对应 10/12 M2 gate 叙事）：
  1) GRAY / GAUSS / GAUSS_SOBEL —— 灰度诊断口拓扑切换
  2) OSD 框动效 —— 仅灰度诊断口，不能当作 HDMI 上的真实检测框
  5) SNAPSHOT    —— 快照分支点亮（cop 窗口有缩放流，显示不变）
"""
import time

from vision_regs import VisionRegs, PRESETS

# AXI_GP0 映射窗口内 axi_regs 基址——overlay 布局定稿后回填（XDC/BD 地址编辑器）
AXI_REGS_BASE = 0x40000000  # sim/scripts/create_hdmi_bd.tcl 明确分配


def sweep_box(v: VisionRegs, cycles: int = 60, w: int = 1280, h: int = 720,
              box_w: int = 160, box_h: int = 120, fps: float = 30.0):
    """诊断框演练：每组写入后 commit 并等待帧首确认，不代表物体定位。"""
    dt = 1.0 / fps
    for i in range(cycles):
        t = i / cycles
        x = int((w - box_w) * (abs((t * 2) % 2 - 1)))
        y = int((h - box_h) * (abs((t * 2) % 2 - 1)))
        v.set_box(x, y, x + box_w, y + box_h, color=0xFF)
        v.commit()
        time.sleep(dt)


def main():
    v = VisionRegs(base=AXI_REGS_BASE)
    seq = ["GRAY", "GAUSS", "GAUSS_SOBEL", "GRAY_SOBEL"]
    for name in seq:                       # A1 参数化：逐拓扑停留 5s
        print(f"topology -> {name}")
        v.apply_preset(name)
        v.commit()
        time.sleep(5)
    print("OSD box sweep (A4)")
    v.set_enable(osd=1)
    v.set_roi(40, 40, 640, 380, color=0x3C)
    v.commit()
    sweep_box(v)
    print("SNAPSHOT on (显示不变，cop 口出 DWxDH 缩放流)")
    v.apply_preset("GAUSS_SNAPSHOT")
    v.commit()
    time.sleep(5)
    print("demo done")


if __name__ == "__main__":
    main()
