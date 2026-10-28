# -*- coding: utf-8 -*-
"""make_tech_report_figures.py —— 技术文档配图一键生成。

用法：py docs/tech-report/make_tech_report_figures.py
输出：docs/tech-report/figures/fig_*.png（6 幅）
口径：2026-10-26。实线=已实现/已验证；虚线=未打通或规划中。
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)

INK = "#1F2937"
ARROW = "#374151"
MUTED = "#6B7280"
C = {
    "pl":   ("#DBEAFE", "#1D4ED8"),
    "mem":  ("#FEF3C7", "#B45309"),
    "disp": ("#DCFCE7", "#15803D"),
    "cop":  ("#FFE4E6", "#BE123C"),
    "cfg":  ("#F3E8FF", "#7E22CE"),
    "gray": ("#F3F4F6", "#6B7280"),
    "warn": ("#FFEDD5", "#C2410C"),
    "ok":   ("#DCFCE7", "#15803D"),
    "part": ("#FEF9C3", "#A16207"),
    "none": ("#FEE2E2", "#B91C1C"),
}


def fig_new(w=12.6, h=7.0, ymax=100):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, kind="pl", fs=9.5, ls="-", sub=None, weight="bold",
        tc=INK):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25",
                                fc=fc, ec=ec, lw=1.4, linestyle=ls, zorder=2))
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + h * 0.16, text, ha="center", va="center",
                fontsize=fs, fontweight=weight, color=tc, zorder=4)
        ax.text(x + w / 2, cy - h * 0.22, sub, ha="center", va="center",
                fontsize=fs - 1.5, color="#4B5563", zorder=4, linespacing=1.35)
    else:
        ax.text(x + w / 2, cy, text, ha="center", va="center",
                fontsize=fs, fontweight=weight, color=tc, zorder=4)


def zone(ax, x, y, w, h, label, kind="gray", fs=9.5, ls="--", alpha=0.30,
         lab_y=None):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25",
                                fc=fc, ec=ec, lw=1.2, linestyle=ls,
                                alpha=alpha, zorder=1))
    if label:
        ax.text(x + 1.0, (y + h - 1.4) if lab_y is None else lab_y, label,
                ha="left", va="top", fontsize=fs, fontweight="bold", color=ec,
                zorder=5)


def arrow(ax, p1, p2, text=None, color=ARROW, ls="-", fs=7.6, rad=0.0, lw=1.4,
          toff=(0.0, 1.2), ha="center", zorder=3):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=12,
                                 color=color, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=zorder))
    if text:
        mx, my = (p1[0] + p2[0]) / 2 + toff[0], (p1[1] + p2[1]) / 2 + toff[1]
        ax.text(mx, my, text, fontsize=fs, color=color, ha=ha, va="center",
                zorder=6, bbox=dict(fc="white", ec="none", pad=0.25))


def line(ax, pts, color=ARROW, ls="-", lw=1.4):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw,
            linestyle=ls, zorder=3, solid_capstyle="round")


def note(ax, x, y, text, fs=7.8, color="#4B5563", ha="left", weight="normal"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center",
            zorder=6, linespacing=1.4, fontweight=weight,
            bbox=dict(fc="white", ec="none", pad=0.2))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("written:", path)


def legend(ax, x, y, items, fs=7.6):
    for i, (kind, label, ls) in enumerate(items):
        yy = y - i * 3.6
        fc, ec = C[kind]
        ax.add_patch(Rectangle((x, yy - 1.1), 3.4, 2.2, fc=fc, ec=ec,
                               lw=1.1, ls=ls, zorder=4))
        ax.text(x + 4.2, yy, label, fontsize=fs, color=MUTED, va="center",
                zorder=4)


# ---------------------------------------------------------------- 图 2-1 系统
def fig_system():
    fig, ax = fig_new(13.0, 7.4)

    box(ax, 1.0, 56.0, 10.5, 14.0, "HDMI 相机", kind="gray", fs=9.5,
        sub="1280×720@60\nRGB 8:8:8")
    zone(ax, 13.5, 5.0, 58.0, 89.5, "PYNQ-Z2（XC7Z020）", kind="gray", fs=10.5,
         lab_y=93.2)
    zone(ax, 15.0, 30.0, 55.0, 62.5, "PL 逻辑", kind="pl", fs=9.0,
         alpha=0.16, lab_y=90.6)
    zone(ax, 15.0, 7.0, 55.0, 20.5, "PS：ARM Cortex-A9 + Linux", kind="cfg",
         fs=9.0, alpha=0.16, lab_y=26.4)

    box(ax, 16.5, 73.0, 12.0, 12.0, "dvi2rgb", fs=9,
        sub="TMDS→RGB\n74.25MHz")
    box(ax, 32.0, 70.0, 19.0, 18.0, "视觉流水线", fs=9.5,
        sub="display 直通\n灰度分析 / 224² 快照\n22 tb · 720p 上板")
    box(ax, 54.5, 73.0, 11.5, 12.0, "rgb2dvi", fs=9, sub="RGB→TMDS")
    box(ax, 16.5, 41.0, 16.5, 16.0, "自研 RISC-V SoC", fs=9.5,
        sub="RV32IM 三级 + 转发 + BHT\n86.8MHz OOC / 40MHz 上板")
    box(ax, 37.0, 38.0, 29.0, 19.0, "INT8 CNN 协处理器", kind="cop", fs=9.5,
        sub="128 MAC · 双 bank 模型 · DMA\n单目标四例板上通过；多目标待上板")
    box(ax, 16.5, 31.5, 49.5, 5.5, "AXI-Lite 配置 · AXI-Stream DMA · 跨时钟域 CDC",
        kind="cfg", fs=8.4)

    note(ax, 17.0, 22.5, "任务提交 · 结果读取 · 持久化 · 消费（ACCEPTED / RESULT_SEQ / CONSUME）", fs=7.4)
    note(ax, 17.0, 18.0, "CopDriver：PynqMmio（实板）/ CopSim（仿真）同一接口；引擎可切换", fs=7.4)
    note(ax, 17.0, 13.5, "FCLK0 100MHz（AXI）· FCLK1 40MHz（协处理器域）· 像素时钟 74.25MHz", fs=7.4,
         color="#7E22CE")

    box(ax, 75.0, 73.0, 9.0, 12.0, "USB 采集卡", kind="gray", fs=8.8,
        sub="HDMI→UVC")
    box(ax, 87.0, 59.0, 12.0, 26.0, "HTML 网页端", kind="disp", fs=9.5,
        sub="Python + OpenCV\n视频叠加 · 工单判定\n记录 / 截图 / 导出", tc="#14532D")

    arrow(ax, (11.5, 63), (16.5, 76), "HDMI IN", rad=-0.12, fs=7.4,
          toff=(-1.5, 3.0))
    arrow(ax, (28.5, 79), (32.0, 79), "pclk", fs=7.4, toff=(0, 1.1))
    arrow(ax, (51.0, 79), (54.5, 79), "display_*", fs=7.4, toff=(0, 1.1))
    arrow(ax, (66.0, 79), (75.0, 79), "HDMI OUT", fs=7.4, toff=(0, 1.3))
    arrow(ax, (84.0, 77.5), (87.0, 76.0), "USB", fs=7.2, toff=(0, 1.2))
    arrow(ax, (43.5, 70.0), (43.5, 57.0), "224² 快照", color="#BE123C", ls="--",
          fs=7.2, toff=(4.0, 0.0))
    arrow(ax, (33.0, 48.0), (37.0, 48.0), "AXI-Lite", fs=7.0, toff=(0, 1.3))
    line(ax, [(25.0, 37.0), (25.0, 41.0)], lw=1.2)
    line(ax, [(52.0, 37.0), (52.0, 38.0)], lw=1.2)
    arrow(ax, (42.5, 27.5), (42.5, 31.5), "MMIO / DMA", fs=7.0, toff=(-2.0, 0.8),
          ha="right")
    arrow(ax, (70.0, 17.0), (87.0, 59.0), "结果 JSON（HTTP/JSON）", ls="--",
          rad=-0.12, fs=7.0, toff=(3.0, 1.5))

    items = []
    note(ax, 48.0, 4.2,
         "结果与画面按检查轮次绑定；过期结果不得显示为当前检查通过（A2 消费语义）",
         fs=7.6, ha="center", color="#7E22CE")
    save(fig, "fig_system.png")


# ------------------------------------------------------------ 图 2-2 RISC-V 核
def fig_core():
    fig, ax = fig_new(13.0, 7.2)

    zone(ax, 1.0, 9.0, 23.0, 69.0, "IF 取指", kind="gray", fs=9.5)
    zone(ax, 27.0, 9.0, 36.0, 69.0, "ID + EX（组合级）", kind="gray", fs=9.5)
    zone(ax, 66.0, 9.0, 33.0, 69.0, "MEM + WB", kind="gray", fs=9.5)

    box(ax, 3.5, 64.0, 8.0, 8.0, "pc", fs=9.0, sub="+hold")
    box(ax, 15.0, 64.0, 7.5, 8.0, "imem", kind="mem", fs=8.8, sub="32KB")
    box(ax, 3.5, 48.0, 19.0, 10.0, "if_stage", fs=9.0,
        sub="IF/ID：valid / pc / instr")
    arrow(ax, (11.5, 68.0), (15.0, 68.0), None)
    arrow(ax, (7.5, 64.0), (7.5, 58.0), None)
    arrow(ax, (19.0, 64.0), (15.0, 58.0), None, rad=-0.12)

    box(ax, 29.0, 64.0, 9.0, 8.0, "decode", fs=8.8, sub="控制 + imm")
    box(ax, 42.0, 64.0, 9.0, 8.0, "regfile", kind="mem", fs=8.8, sub="2R1W")
    box(ax, 29.0, 49.0, 12.0, 9.0, "转发选择", kind="warn", fs=8.6,
        sub="EX > MEM > WB")
    box(ax, 45.0, 49.0, 9.0, 9.0, "alu", fs=9.0, sub="y + 标志")
    box(ax, 29.0, 35.0, 11.0, 8.0, "muldiv", kind="warn", fs=8.6,
        sub="Radix-4 乘 16 拍")
    box(ax, 45.0, 35.0, 11.0, 8.0, "分支裁决", fs=8.6, sub="target / taken")
    box(ax, 29.0, 22.0, 32.0, 7.0, "边界 → mem_wb_stage", fs=8.4,
        sub="store / 寄存器写只在此级提交")
    arrow(ax, (33.5, 64.0), (35.0, 58.0), None)
    arrow(ax, (46.5, 64.0), (37.0, 58.0), "rdata", fs=7.2, rad=-0.1,
          toff=(3.0, 1.0))
    arrow(ax, (41.0, 53.5), (45.0, 53.5), None)
    arrow(ax, (49.5, 49.0), (50.0, 43.0), None)
    arrow(ax, (34.5, 35.0), (36.0, 29.0), None)
    arrow(ax, (50.5, 35.0), (47.0, 29.0), None)

    box(ax, 68.0, 64.0, 29.0, 8.0, "mem_wb_stage 边界", fs=8.8,
        sub="valid / pc / 结果 / 提交控制")
    box(ax, 68.0, 49.0, 9.0, 9.0, "dmem", kind="mem", fs=8.8, sub="32KB")
    box(ax, 80.0, 49.0, 10.0, 9.0, "load 扩展", fs=8.6, sub="byte / half")
    box(ax, 72.0, 35.0, 22.0, 8.0, "写回 / store 提交", fs=8.8,
        sub="mem_wb.valid 门控")
    arrow(ax, (73.0, 64.0), (72.5, 58.0), None)
    arrow(ax, (92.0, 64.0), (85.0, 58.0), None)
    arrow(ax, (72.5, 49.0), (78.0, 43.0), None)
    arrow(ax, (85.0, 49.0), (88.0, 43.0), None)

    # 三路转发
    arrow(ax, (45.0, 52.5), (41.0, 55.0), "EX→EX", color="#DC2626", lw=1.7,
          rad=0.3, fs=7.2, toff=(-0.5, 2.8))
    line(ax, [(68.0, 68.0), (64.0, 68.0), (64.0, 44.0), (39.5, 44.0),
              (39.5, 49.0)], color="#D97706", lw=1.7)
    arrow(ax, (39.5, 47.5), (39.5, 49.0), None, color="#D97706")
    ax.text(52.0, 45.2, "MEM→EX", fontsize=7.4, color="#D97706", ha="center",
            va="center", fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.2))
    line(ax, [(83.0, 35.0), (83.0, 31.5), (31.5, 31.5), (31.5, 49.0)],
         color="#7C3AED", lw=1.7)
    arrow(ax, (31.5, 47.5), (31.5, 49.0), None, color="#7C3AED")
    ax.text(57.0, 32.8, "WB→EX", fontsize=7.4, color="#7C3AED", ha="center",
            va="center", fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.2))

    # 顶层控制
    box(ax, 28.0, 82.0, 34.0, 10.0, "hazard", kind="warn", fs=9.0,
        sub="load-use 停 1 拍 · taken 冲刷 1 槽 · 命中零气泡")
    box(ax, 2.0, 82.0, 22.0, 10.0, "BHT 分支预测", kind="cfg", fs=9.0,
        sub="64 项 · 1/2-bit · pc[7:2]")
    arrow(ax, (13.0, 82.0), (13.0, 78.0), "预测方向", color="#7E22CE", fs=7.2,
          toff=(4.0, 0.0))
    arrow(ax, (40.0, 82.0), (20.0, 78.0), "stall / flush", color="#DC2626",
          fs=7.0, rad=0.08, toff=(0.0, -1.6))

    note(ax, 2.0, 4.6,
         "RV32IM · 三级流水 · 三路转发 · 64 项 BHT · Radix-4 乘法（16 拍）/ Radix-2 除法（32 拍）",
         fs=7.8)
    note(ax, 2.0, 1.4,
         "CoreMark 2K/32：CPI 1.606（bht2）· 相对原始无转发基线周期降 32.0% · OOC 86.806MHz（WNS +0.538）",
         fs=7.8, color="#1D4ED8")
    save(fig, "fig_core.png")


# --------------------------------------------------------- 图 2-3 视觉流水线
def fig_video():
    fig, ax = fig_new(13.0, 6.2)

    box(ax, 1.0, 40.0, 11.0, 16.0, "in_align", fs=9.2,
        sub="vs/hs/de 归一化\n撞拍顺延不丢失")
    box(ax, 16.0, 76.0, 27.0, 12.0, "显示直通", kind="disp", fs=9.5,
        sub="原始 RGB 恒 1 拍 + frame_id\n分析开关/反压均不影响", tc="#14532D")
    box(ax, 47.0, 76.0, 16.0, 12.0, "rgb2dvi", kind="disp", fs=9.2,
        sub="HDMI OUT 1280×720@60", tc="#14532D")
    box(ax, 67.0, 76.0, 31.0, 12.0, "USB 采集卡 → 网页端", kind="gray", fs=9.2,
        sub="彩色原图预览 + 框/标签叠加")
    arrow(ax, (12.0, 54.0), (20.0, 76.0), "raw 旁路", rad=0.1, fs=7.4,
          toff=(-2.0, 1.5))
    arrow(ax, (43.0, 82.0), (47.0, 82.0), None)
    arrow(ax, (63.0, 82.0), (67.0, 82.0), None)

    box(ax, 16.0, 46.0, 9.0, 10.0, "rgb2gray", fs=7.8, sub="BT.601\n1 拍")
    box(ax, 28.0, 46.0, 10.5, 10.0, "gaussian", fs=7.8, sub="3×3 移位加\n落后 1 行")
    box(ax, 41.5, 46.0, 8.5, 10.0, "sobel", fs=7.8, sub="L1 幅值\n3 拍")
    box(ax, 53.0, 46.0, 10.5, 10.0, "OSD 叠加", fs=7.8, sub="框坐标来自\nactive_cfg")
    box(ax, 66.5, 46.0, 31.5, 10.0, "out_* 灰度诊断流", kind="gray", fs=8.2,
        sub="不驱动物理 HDMI · 仅用于诊断与边界检查")
    arrow(ax, (12.0, 47.0), (16.0, 49.0), None)
    note(ax, 13.2, 43.6, "RGB→Y", fs=6.6)
    arrow(ax, (25.0, 51.0), (28.0, 51.0), None)
    arrow(ax, (38.5, 51.0), (41.5, 51.0), None)
    arrow(ax, (50.0, 51.0), (53.0, 51.0), None)
    arrow(ax, (63.5, 51.0), (66.5, 51.0), None)
    note(ax, 30.0, 60.0, "active_cfg：旁路开关帧首整组应用，帧内恒定", fs=7.2, color="#7E22CE")

    box(ax, 27.0, 20.0, 12.0, 11.0, "scaler", kind="cop", fs=8.8,
        sub="16.16 双线性\n→224×224")
    box(ax, 41.5, 20.0, 10.0, 11.0, "t_scaler", kind="cop", fs=8.2, sub="R0 bit1")
    box(ax, 54.0, 20.0, 14.0, 11.0, "cop_buf", kind="cop", fs=8.8,
        sub="双 bank 224²×8b\n整帧原子回放")
    box(ax, 71.0, 20.0, 27.0, 11.0, "CNN 协处理器 / PS 引擎", kind="cop", fs=8.6,
        sub="帧号+配置号随帧交付\n未消费帧被覆盖 → drop_count++", ls="--")
    arrow(ax, (45.0, 46.0), (33.0, 31.0), "sobel 后分叉", rad=0.1, fs=7.2,
          toff=(4.0, -1.0))
    arrow(ax, (39.0, 25.5), (41.5, 25.5), None)
    arrow(ax, (51.5, 25.5), (54.0, 25.5), None)
    arrow(ax, (68.0, 25.5), (71.0, 25.5), None)
    note(ax, 68.8, 28.2, "cop_*", fs=6.6)

    box(ax, 16.0, 5.0, 12.0, 9.0, "axi_regs", kind="cfg", fs=8.2,
        sub="R0–R10 暂存\nR11 提交 / R12 回执")
    box(ax, 32.0, 5.0, 15.0, 9.0, "config_bridge", kind="cfg", fs=8.2,
        sub="请求/确认跨时钟域\n帧首整组应用")
    arrow(ax, (28.0, 9.5), (32.0, 9.5), "regs_flat", fs=6.6, toff=(0, 1.4))
    line(ax, [(39.5, 14.0), (39.5, 17.0), (14.0, 17.0), (14.0, 58.0),
              (18.0, 58.0), (18.0, 56.0)], color="#7E22CE", ls="--", lw=1.2)
    arrow(ax, (18.0, 58.0), (18.0, 56.0), None, color="#7E22CE")

    note(ax, 1.0, 1.2,
         "720p60 · 像素时钟 74.25MHz · video_pipeline OOC WNS +0.330ns · 物理 HDMI 上板直通 108 帧",
         fs=7.4)
    save(fig, "fig_video.png")


# ------------------------------------------------------- 图 2-4 CNN 协处理器
def fig_cop():
    fig, ax = fig_new(13.0, 6.8)

    zone(ax, 1.0, 8.0, 22.0, 82.0, "PS（100MHz）", kind="cfg", fs=9.5)
    zone(ax, 25.5, 8.0, 8.0, 82.0, "CDC", kind="warn", fs=8.8)
    zone(ax, 36.0, 8.0, 63.0, 82.0, "协处理器域（40MHz）", kind="cop", fs=9.5,
         alpha=0.13)

    box(ax, 2.5, 73.0, 19.0, 11.0, "PS 服务 / CopDriver", fs=8.6,
        sub="配置 · 提交 · 读结果 · 消费")
    box(ax, 2.5, 54.0, 19.0, 11.0, "AXI DMA", fs=8.6,
        sub="MM2S 单包 ≤65,535B\npayload 36,032B / ROI 4,096B")
    box(ax, 2.5, 35.0, 19.0, 11.0, "AXI-Lite 主机", fs=8.6,
        sub="0x4000_0000\n读 META/LOGITS/SCORE")

    box(ax, 26.5, 70.0, 6.0, 15.0, "2FF\n同步", fs=7.6)
    box(ax, 26.5, 48.0, 6.0, 12.0, "异步\nFIFO", fs=7.6)

    box(ax, 38.0, 72.0, 25.0, 12.0, "配置寄存器 + 邮箱", fs=8.6,
        sub="CFG_SEQ/APPLIED · STATUS\nERROR_CODE · RESULT_SEQ · DMA_BYTES")
    box(ax, 38.0, 54.0, 25.0, 12.0, "驻留固件（RISC-V）", kind="pl", fs=8.6,
        sub="等 GO → START → ACCEPTED\n判定 → FW_COUNTS/FW_DECISION")
    box(ax, 38.0, 36.0, 25.0, 12.0, "模型存储（双 bank）", kind="mem", fs=8.6,
        sub="34,432B 权重 ×2 影子\n清单 SHA256 / CRC32")
    box(ax, 38.0, 18.0, 25.0, 12.0, "ROI 缓冲", kind="mem", fs=8.6,
        sub="16 槽 ×4,096B\n对齐 / 长度检查")

    box(ax, 68.0, 54.0, 29.0, 26.0, "MAC 阵列 8×16 = 128", kind="cop", fs=9.5,
        sub="INT8×INT8 → INT32 累加\nConv + bias + ReLU + requant\nGAP / FC")
    box(ax, 68.0, 34.0, 29.0, 14.0, "激活 / 结果缓冲", kind="mem", fs=8.8,
        sub="32KiB ping + 16KiB pong + GAP\n结果窗口 16×16B")
    box(ax, 68.0, 16.0, 29.0, 12.0, "结果回读", fs=8.8,
        sub="META / LOGITS / SCORE / RESULT_SEQ")

    arrow(ax, (21.5, 78.5), (26.5, 78.5), "配置/状态", fs=6.8, toff=(0, 1.0))
    arrow(ax, (32.5, 78.5), (38.0, 78.5), None, color="#7E22CE")
    arrow(ax, (21.5, 59.5), (26.5, 59.5), "DMA", fs=6.8, toff=(0, 1.0))
    line(ax, [(32.5, 57.0), (35.0, 57.0), (35.0, 42.0), (38.0, 42.0)],
         color="#BE123C", lw=1.3)
    arrow(ax, (35.0, 42.0), (38.0, 42.0), None, color="#BE123C")
    ax.text(35.8, 50.0, "payload", fontsize=6.4, color="#BE123C", rotation=90,
            ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))
    line(ax, [(29.5, 48.0), (29.5, 24.0), (38.0, 24.0)], color="#BE123C", lw=1.3)
    arrow(ax, (29.5, 24.0), (38.0, 24.0), None, color="#BE123C")
    ax.text(30.8, 32.0, "ROI", fontsize=6.4, color="#BE123C", rotation=90,
            ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))
    arrow(ax, (50.5, 72.0), (50.5, 66.0), "GO / 状态", fs=6.4, toff=(0.5, 0.0))
    arrow(ax, (63.0, 60.0), (68.0, 64.0), "START", fs=6.4, toff=(0.8, 2.6))
    line(ax, [(63.0, 46.0), (65.2, 46.0), (65.2, 70.0), (68.0, 70.0)],
         color="#B45309", lw=1.3)
    arrow(ax, (65.2, 70.0), (68.0, 70.0), None, color="#B45309")
    ax.text(64.2, 57.0, "权重", fontsize=6.4, color="#B45309", rotation=90,
            ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))
    line(ax, [(63.0, 24.0), (66.8, 24.0), (66.8, 56.0), (68.0, 56.0)],
         color="#BE123C", lw=1.3)
    arrow(ax, (66.8, 56.0), (68.0, 56.0), None, color="#BE123C")
    ax.text(67.8, 38.0, "ROI", fontsize=6.4, color="#BE123C", rotation=90,
            ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))
    arrow(ax, (82.5, 54.0), (82.5, 48.0), None)
    arrow(ax, (82.5, 34.0), (82.5, 28.0), None)
    line(ax, [(82.5, 16.0), (82.5, 8.5), (12.0, 8.5), (12.0, 35.0)],
         color="#B45309", lw=1.3)
    arrow(ax, (12.0, 33.5), (12.0, 35.0), None, color="#B45309")
    ax.text(45.0, 9.7, "结果回读（AXI-Lite）", fontsize=6.4, color="#B45309",
            ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))

    note(ax, 1.2, 4.4,
         "清单 v1 PROVISIONAL：20 张量 / 36,032B / CRC32 0x2F760211 / SHA256 14a199…；单 ROI 11,944,128 MAC",
         fs=7.2)
    note(ax, 1.2, 1.4,
         "板上实测：2026-10-26 zero/pattern 3+3 全匹配；2026-10-27 四例黄金通过；"
         "多目标槽错位，COMMIT_RESULT 修复仅仿真 PASS、未上板",
         fs=7.2, color="#B91C1C")
    save(fig, "fig_cop.png")


# --------------------------------------------------------- 图 2-5 软件架构
def fig_sw():
    fig, ax = fig_new(13.0, 7.2)

    zone(ax, 1.0, 8.0, 44.0, 84.0, "软件分层", kind="gray", fs=9.5)
    box(ax, 2.5, 76.0, 41.0, 12.0, "HTML 网页端（单文件）", kind="disp", fs=9.0,
        sub="HUD 1600×900 · 识别范围表 · RUN 三态\n记录 / 截图 / CSV 导出 / 异常提示", tc="#14532D")
    box(ax, 2.5, 58.0, 41.0, 12.0, "HTTP/JSON 协议 v1.2", kind="cfg", fs=9.0,
        sub="GET /v1/status · /v1/latest\nPOST /v1/check · /v1/config")
    box(ax, 2.5, 40.0, 41.0, 12.0, "PS 服务", kind="pl", fs=9.0,
        sub="采集 · 定位裁剪 · 预处理/量化 · 去重 · 持久化")
    box(ax, 2.5, 22.0, 41.0, 12.0, "CopDriver + A2 语义", kind="cop", fs=9.0,
        sub="CFG_SEQ/APPLIED · ACCEPTED · 终态独占\nRESULT_SEQ+1 · 先持久化后 CONSUME")
    box(ax, 2.5, 13.0, 41.0, 6.0, "传输层：PynqMmio（实板）/ CopSim（仿真）", kind="gray",
        fs=7.8)

    arrow(ax, (12.0, 76.0), (12.0, 70.0), None)
    ax.text(13.2, 73.0, "JSON", fontsize=6.8, color=MUTED, va="center")
    arrow(ax, (12.0, 58.0), (12.0, 52.0), None)
    ax.text(13.2, 55.0, "提交 / 查询", fontsize=6.8, color=MUTED, va="center")
    arrow(ax, (12.0, 40.0), (12.0, 34.0), None)
    ax.text(13.2, 37.0, "job", fontsize=6.8, color=MUTED, va="center")
    arrow(ax, (12.0, 22.0), (12.0, 19.0), None)
    arrow(ax, (36.0, 34.0), (36.0, 40.0), None, ls="--")
    ax.text(37.2, 37.0, "trace / 截图", fontsize=6.8, color=MUTED, va="center")
    arrow(ax, (40.0, 52.0), (40.0, 58.0), None, ls="--")
    ax.text(41.2, 55.0, "结果", fontsize=6.8, color=MUTED, va="center")

    zone(ax, 48.0, 8.0, 51.0, 84.0, "一次检查的作业时序", kind="gray", fs=9.5)
    steps = [
        ("IDLE", "BUSY=0 且 UNCONSUMED=0", "pl"),
        ("CONFIG", "写影子配置 + CFG_SEQ++ + COMMIT", "cfg"),
        ("APPLIED", "等 CFG_APPLIED==CFG_SEQ（2s）", "cfg"),
        ("START", "固件置 START，PS 等 ACCEPTED（1s）", "pl"),
        ("RUN", "推理；等 DONE/ERROR/TIMEOUT（5s）", "cop"),
        ("RESULT", "RESULT_SEQ==上次+1；读 META/LOGITS/SCORE", "mem"),
        ("PERSIST", "packet / trace / 截图原子落盘", "disp"),
        ("CONSUME", "CTRL[6]=1；只清终态，不清 RESULT_SEQ", "ok"),
    ]
    for i, (name, desc, kind) in enumerate(steps):
        yy = 84.0 - i * 8.6
        box(ax, 49.5, yy - 5.6, 11.5, 6.4, name, kind=kind, fs=7.6)
        ax.text(62.5, yy - 2.4, desc, fontsize=6.9, color="#374151",
                va="center", ha="left", zorder=4)
        if i < len(steps) - 1:
            arrow(ax, (55.2, yy - 5.6), (55.2, yy - 8.6), None, lw=1.0)
    ax.text(62.5, 12.0,
            "异常分支：NO_ACK（ACCEPTED 超时）\nHW_TIMEOUT（终态超时）\nSTALE_RESULT（未消费）",
            fontsize=6.8, color="#B91C1C", va="center", ha="left", zorder=5,
            linespacing=1.5, bbox=dict(fc="#FEF2F2", ec="#FCA5A5", pad=2.5))

    note(ax, 1.2, 4.0,
         "同一 trigger_ref 重试不重复采集；服务缓存 16 条已完成轮次；会话变更强制重新握手；失败轮次不生成 packet.json",
         fs=6.9)
    save(fig, "fig_sw.png")


# ------------------------------------------------------------ 图 1-1 设计流程
def fig_flow():
    fig, ax = fig_new(13.0, 2.3, ymax=30)
    labels = [
        ("需求与验收", "工单/计数/记录"),
        ("接口契约", "寄存器/报文/清单"),
        ("RTL 与模块 tb", "核/视觉/协处理器"),
        ("全量回归", "Icarus + XSim"),
        ("综合与时序", "WNS/资源/DRC"),
        ("上板 bring-up", "时钟/预检/DMA"),
        ("软件联调", "服务 + 网页端"),
        ("证据归档", "日志/哈希/复现"),
    ]
    n = len(labels)
    w, gap = 10.4, 2.0
    for i, (t, s) in enumerate(labels):
        x = 1.0 + i * (w + gap)
        box(ax, x, 8.0, w, 14.0, t, kind="pl" if i % 2 == 0 else "cfg", fs=7.4,
            sub=s)
        if i < n - 1:
            arrow(ax, (x + w, 15.0), (x + w + gap, 15.0), None, lw=1.1)
    note(ax, 1.0, 2.5,
         "每阶段以门禁 + 仓库内脚本收口；仿真 / 软件 / 板上三级别分别标注，不用低级别证据替代高级别结论。",
         fs=7.2)
    save(fig, "fig_flow.png")


if __name__ == "__main__":
    fig_system()
    fig_core()
    fig_video()
    fig_cop()
    fig_sw()
    fig_flow()
    print("all figures ->", OUT)
