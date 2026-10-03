# -*- coding: utf-8 -*-
"""make_project_diagrams.py —— 项目总览图一键生成（docs/project-overview.md 配图）。

用法：python docs/img/make_project_diagrams.py
输出：docs/img/fig1_system.png ... fig7_copbuf.png（共 7 幅）
图内容与 src/riscv/*.v、src/vision/*.v 的 2026-10-03 现状一致；RTL 改动后须同步更新。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# 配色：一个语义一种颜色，全文统一（STE100：一个词一个意思）
C = {
    "pl":   ("#DBEAFE", "#1D4ED8"),   # PL 逻辑模块
    "mem":  ("#FEF3C7", "#B45309"),   # 存储 / BRAM
    "disp": ("#DCFCE7", "#15803D"),   # 显示路径
    "cop":  ("#FFE4E6", "#BE123C"),   # 快照 / CNN
    "cfg":  ("#F3E8FF", "#7E22CE"),   # 配置 / PS / AXI
    "gray": ("#F3F4F6", "#6B7280"),   # 中性
    "warn": ("#FFEDD5", "#C2410C"),   # 冒险 / 控制动作
}
INK = "#1F2937"
ARROW = "#374151"
RED = "#DC2626"
FWD = {"EX": "#DC2626", "MEM": "#D97706", "WB": "#7C3AED"}


def fig_new(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, kind="pl", fs=11, ls="-", sub=None, weight="bold"):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                fc=fc, ec=ec, lw=1.5, linestyle=ls, zorder=2))
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + h * 0.18, text, ha="center", va="center",
                fontsize=fs, fontweight=weight, color=INK, zorder=4)
        ax.text(x + w / 2, cy - h * 0.22, sub, ha="center", va="center",
                fontsize=fs - 2.5, color="#4B5563", zorder=4)
    else:
        ax.text(x + w / 2, cy, text, ha="center", va="center",
                fontsize=fs, fontweight=weight, color=INK, zorder=4)


def zone(ax, x, y, w, h, label, kind="gray", fs=10.5, ls="--", lab_dx=0.6,
         lab_dy=None):
    """大容器（时钟域 / 层级）。标签固定在顶边内侧，避免压到自身边框。"""
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                fc=fc, ec=ec, lw=1.3, linestyle=ls,
                                alpha=0.35, zorder=1))
    ax.text(x + lab_dx, (y + h - 3.2) if lab_dy is None else lab_dy, label,
            ha="left", va="top", fontsize=fs, fontweight="bold", color=ec,
            zorder=4)


def arrow(ax, p1, p2, text=None, color=ARROW, ls="-", fs=9, rad=0.0, lw=1.7,
          toff=(0.0, 1.2), ha="center"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=15,
                                 color=color, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=3))
    if text:
        mx, my = (p1[0] + p2[0]) / 2 + toff[0], (p1[1] + p2[1]) / 2 + toff[1]
        ax.text(mx, my, text, fontsize=fs, color=color, ha=ha, va="center",
                zorder=4, bbox=dict(fc="white", ec="none", pad=0.4))


def line(ax, pts, color=ARROW, ls="-", lw=1.7):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, linestyle=ls, zorder=3,
            solid_capstyle="round")


def title(ax, text, sub=None):
    ax.text(50, 98.5, text, ha="center", va="top", fontsize=15,
            fontweight="bold", color=INK)
    if sub:
        ax.text(50, 94.6, sub, ha="center", va="top", fontsize=10, color="#6B7280")


def note(ax, x, y, text, fs=8.8, color="#4B5563", ha="left"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center",
            zorder=4, linespacing=1.45, bbox=dict(fc="white", ec="none", pad=0.3))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("written:", path)


# ---------------------------------------------------------------- 图 1 系统总览
def fig1_system():
    fig, ax = fig_new(18, 10)
    title(ax, "图 1　系统总览：边缘慧眼（EdgeSight）——桌面紧固件识别与工业检查",
          "实线 = 已实现并验证的数据流；虚线 = 已规划但未实现（2026-10-03 口径）")

    box(ax, 1, 46, 10, 12, "HDMI 相机", kind="gray", fs=13,
        sub="720p60 RGB（已购 CM3 相机）")

    zone(ax, 19, 6, 54, 88, "PYNQ-Z2 板卡（Zynq-7020）", kind="gray", fs=12.5)
    zone(ax, 21, 26, 50, 62, "PL —— FPGA 逻辑（本仓库 RTL）", kind="pl", fs=11)
    box(ax, 23, 56, 13, 12, "dvi2rgb IP", sub="TMDS → 并行 RGB")
    box(ax, 40, 54, 16, 16, "视觉流水线", sub="video_pipeline / vision_top\n（模块二 · 14 个文件）", fs=12)
    box(ax, 60, 56, 9, 12, "rgb2dvi", sub="RGB → TMDS", fs=10)
    box(ax, 23, 30, 21, 13, "自研 RISC-V SoC", sub="soc_top · core_top v0\n40 MHz · RV32IM（模块一）", fs=12)
    box(ax, 49, 30, 20, 13, "CNN 协处理器", kind="cop", ls="--",
        sub="cop_top INT8 MAC（模块三）\n未实现", fs=12)
    arrow(ax, (36, 62), (40, 62), "pclk 像素流")
    arrow(ax, (56, 62), (60, 62), "display_*")
    arrow(ax, (50, 54), (55, 43), "cop_* 快照帧\n（DW×DH=224）", ls="--", rad=0.12)
    zone(ax, 21, 9, 50, 14, "PS —— ARM Cortex-A9 + Linux", kind="cfg", fs=11)
    note(ax, 24, 14.5, "定位（PS/PL 分配待冻结）· 结果与工单服务（未实现）· AXI-Lite 配置（已实现）", fs=9.5)
    arrow(ax, (33, 23), (33, 26), None)
    ax.text(34, 24.5, "AXI-Lite（vision_axi，基址 0x4000_0000）", fontsize=9,
            color=ARROW, ha="left")

    box(ax, 77, 56, 10, 12, "USB 采集卡", kind="gray", fs=12)
    box(ax, 88, 44, 10.5, 14, "Windows EXE", kind="disp", fs=12,
        sub="视频叠加 · 工单统计\n（watercopper）")
    arrow(ax, (69, 62), (77, 62), "HDMI OUT")
    arrow(ax, (82, 56), (90, 58), "USB 视频", rad=-0.1)
    arrow(ax, (71, 13), (88, 44), "结果报文", ls="--", rad=-0.15, toff=(3.0, 4.0))
    note(ax, 50, 3, "EXE 不混用不同检查轮次；过期结果不得显示为当前检查通过（同步协议待冻结）", fs=9.5,
         ha="center")

    note(ax, 1, 88, "图例", fs=10, color=INK)
    for i, (k, t) in enumerate([("pl", "PL 处理模块"), ("mem", "存储"),
                                ("disp", "显示 / 前端"), ("cop", "快照 / 推理"),
                                ("cfg", "PS / 配置域")]):
        y = 84 - i * 4.5
        box(ax, 1, y - 1.2, 4, 3.2, "", kind=k)
        note(ax, 6, y + 0.4, t, fs=9)
    save(fig, "fig1_system.png")


# ------------------------------------------------------------- 图 2 RTL 组成树
def fig2_rtl_tree():
    fig, ax = fig_new(18, 12)
    title(ax, "图 2　RTL 代码组成：src/ 下的两棵模块树 + 一处预留",
          "实线框 = 已实现；虚线框 = 未实现（branch_predict 为 Part C 计划模块）")

    zone(ax, 1, 10, 47, 80, "模块一　src/riscv/ —— RV32IM 核（979 行）", kind="pl", fs=12)
    box(ax, 3, 79, 43, 5, "pynq_z2_top　板级顶层：MMCM 125→40 MHz + 复位同步", fs=10.5)
    box(ax, 3, 72, 43, 5, "soc_top　SoC 外壳：核 + imem + dmem + 计时器 MMIO + LED", fs=10.5)
    box(ax, 3, 65, 43, 5, "core_top　v0 两级核：IF / (ID+EX+MEM+WB)　（已收口）", fs=10.5)
    zone(ax, 3, 38, 43, 25, "v1 三级流水（Part B/C）　（完整核未验收）", kind="gray", fs=10)
    for i, (t, s) in enumerate([("if_stage", "IF 级 + IF/ID 边界"),
                                ("id_ex_stage", "ID+EX 级（组合）"),
                                ("mem_wb_stage", "MEM+WB 边界寄存")]):
        box(ax, 4.5 + i * 14, 49, 12.5, 7, t, fs=9.5, sub=s)
    for i, (t, s) in enumerate([("forwarding", "三路旁路选择"),
                                ("hazard", "stall / flush 控制"),
                                ("branch_predict", "BHT 1/2-bit")]):
        box(ax, 4.5 + i * 14, 40.5, 12.5, 6.5, t, fs=9.5, sub=s,
            ls="--" if i == 2 else "-")
    box(ax, 3, 14, 43, 14, "共享单元　pc · decode · regfile · alu · muldiv",
        sub="imem / dmem：32 KB BRAM，哈佛结构，hex 预载", fs=10.5)
    for y1, y2 in [(79, 77.3), (72, 70.3), (65, 63.3)]:
        arrow(ax, (24.5, y1), (24.5, y2), None, lw=1.4)

    zone(ax, 52, 10, 47, 80, "模块二　src/vision/ —— HDMI 视觉链路（1355 行）", kind="pl", fs=12)
    box(ax, 54, 79, 43, 5, "video_pipeline　物理前端边界：in_align + seen_frame 门控 + 显示直通", fs=10)
    box(ax, 54, 72, 43, 5, "vision_top　三线拓扑仲裁：显示 / 灰度分析 / 快照 + 配置", fs=10.5)
    zone(ax, 54, 46, 43, 22, "处理单元（像素流水线）", kind="gray", fs=10)
    for i, (t, s) in enumerate([("rgb2gray", "BT.601 定点，1 拍"),
                                ("gaussian_3x3", "3×3 平滑，2×行缓存"),
                                ("sobel", "L1 幅值，8bit 饱和")]):
        box(ax, 55.5 + i * 14, 54, 12.5, 7, t, fs=9.5, sub=s)
    for i, (t, s) in enumerate([("osd_overlay", "两个 1px 检测框"),
                                ("scaler", "16.16 双线性"),
                                ("cop_buf", "乒乓帧缓冲")]):
        box(ax, 55.5 + i * 14, 47, 12.5, 6.5, t, fs=9.5, sub=s,
            kind="cop" if i == 2 else "pl")
    zone(ax, 54, 20, 43, 20, "接口与基础设施", kind="gray", fs=10)
    for i, (t, s) in enumerate([("in_align", "HDMI 流归一化"),
                                ("config_bridge", "配置跨时钟域"),
                                ("axi_regs", "AXI-Lite 寄存器堆")]):
        box(ax, 55.5 + i * 14, 27.5, 12.5, 7, t, fs=9.5, sub=s,
            kind="cfg" if i else "pl")
    for i, (t, s) in enumerate([("vision_axi", "Vivado AXI 封装"),
                                ("reset_sync", "每域复位同步"),
                                ("line_buffer", "行缓存底层 ×5")]):
        box(ax, 55.5 + i * 14, 20.5, 12.5, 6.5, t, fs=9.5, sub=s)
    box(ax, 54, 11, 43, 7, "src/coprocessor/　模块三 CNN 协处理器",
        sub="仅 README。算子契约未冻结，RTL 未实现", kind="cop", ls="--", fs=10.5)
    for y1, y2 in [(79, 77.3), (72, 70.3)]:
        arrow(ax, (75.5, y1), (75.5, y2), None, lw=1.4)
    save(fig, "fig2_rtl_tree.png")


# ------------------------------------------------------ 图 3 v0 两级核数据通路
def fig3_core_v0():
    fig, ax = fig_new(17, 10.5)
    title(ax, "图 3　v0 两级核数据通路：core_top + soc_top",
          "两级 = IF 取指寄存一拍；译码到写回在同一拍内组合完成。地址空间见 design_v0.md §5.8")

    zone(ax, 1, 4, 98, 86, "soc_top（PL 侧最小 SoC）", kind="gray", fs=11)

    # ---- IF 行（74..84） ----
    box(ax, 3, 74, 10, 10, "pc", sub="pc_sel 选择\n下一条地址", fs=11)
    box(ax, 17, 74, 12, 10, "imem", kind="mem", sub="32KB BRAM\n同步读", fs=11)
    box(ax, 33, 74, 14, 10, "if_stage", sub="IF/ID 边界\nflush 时注入 NOP", fs=11)
    arrow(ax, (13, 79), (17, 79), "imem_addr", fs=8.5)
    arrow(ax, (29, 79), (33, 79), "instr", fs=8.5, toff=(0, 1.6))

    # ---- ID+EX 行（56..68） ----
    box(ax, 3, 56, 12, 12, "decode", sub="译码器\n控制信号 + imm", fs=11)
    box(ax, 19, 56, 12, 12, "regfile", kind="mem", sub="32×32bit\n2 读 1 写", fs=11)
    box(ax, 36, 56, 11, 12, "操作数选择", sub="alu_a / alu_b\nimm / pc / 0", fs=10.5)
    box(ax, 52, 56, 10, 12, "alu", sub="y / zero / lt / ltu", fs=11)
    box(ax, 68, 56, 15, 12, "分支 / 跳转裁决", sub="branch_target = pc_id+imm\nJALR 目标 = alu_y&~1", fs=10.5)
    box(ax, 36, 40, 11, 9, "muldiv", kind="warn", sub="多拍乘除\nstall 等待", fs=10.5)
    arrow(ax, (38, 74), (9, 68.3), "instr", fs=8.5, rad=0.0, toff=(6, 1.8))
    arrow(ax, (15, 62), (19, 62), "读地址", fs=8.5)
    arrow(ax, (31, 62), (36, 62), "rdata1/2", fs=8.5)
    arrow(ax, (47, 62), (52, 62), None)
    arrow(ax, (62, 62), (68, 62), "zero/lt/ltu", fs=8.5)
    arrow(ax, (25, 56), (39.5, 49.3), "rdata1/2", fs=8.5, rad=0.05, toff=(-3.4, -0.6))

    # 分支重定向：走 IF/ID 行之间的走廊回到 pc
    line(ax, [(75.5, 68.3), (75.5, 70.5), (8, 70.5), (8, 73.7)], color=RED)
    arrow(ax, (8, 71.8), (8, 73.7), None, color=RED)
    ax.text(40, 72.2, "pc_sel / flush：taken 则重定向 PC", fontsize=9, color=RED,
            ha="center", va="center", zorder=4,
            bbox=dict(fc="white", ec="none", pad=0.4))

    # ---- MEM+WB 行（18..29） ----
    box(ax, 19, 18, 13, 11, "dmem", kind="mem", sub="32KB RAM\nbyte/half 使能", fs=11)
    box(ax, 37, 18, 13, 11, "load 扩展", sub="byte/half 选道\n符号/零扩展", fs=10.5)
    box(ax, 55, 18, 13, 11, "写回选择", sub="alu_y / load /\npc+4 / muldiv", fs=10.5)
    box(ax, 74, 18, 17, 11, "MMIO", kind="cfg", sub="cycle_cnt @0x8000_8000\nLED @0x8000_3FF0", fs=10.5)

    # alu_y 作访存地址：alu 底部 → 走廊 y=52 → 下行进 dmem 顶部
    line(ax, [(57, 56), (57, 52), (28, 52), (28, 29.3)])
    arrow(ax, (28, 31), (28, 29.3), None)
    ax.text(43, 53.7, "alu_y 作访存地址", fontsize=8.8, color=ARROW, ha="center",
            va="center", zorder=4, bbox=dict(fc="white", ec="none", pad=0.4))
    # store 写数据：regfile 底部直下进 dmem 顶部
    line(ax, [(23, 56), (23, 29.3)])
    arrow(ax, (23, 31), (23, 29.3), None)
    ax.text(9, 44, "rdata2 作写数据\n（store）", fontsize=8.8, color=ARROW, ha="left",
            va="center", zorder=4, linespacing=1.4)
    # muldiv 结果 → 写回选择
    line(ax, [(47, 44.5), (61.5, 44.5), (61.5, 29.3)])
    arrow(ax, (61.5, 31), (61.5, 29.3), None)
    ax.text(54.5, 46.3, "muldiv 结果", fontsize=8.8, color=ARROW, ha="center",
            va="center", zorder=4, bbox=dict(fc="white", ec="none", pad=0.4))
    # 写回 → regfile（绿色回环）
    line(ax, [(66, 29.3), (66, 50), (25, 50), (25, 56.3)], color="#15803D")
    arrow(ax, (25, 54.5), (25, 56.3), None, color="#15803D")
    ax.text(64.8, 40, "写回 regfile（wb_data）", fontsize=9, color="#15803D",
            ha="center", va="center", rotation=90, zorder=4)
    arrow(ax, (32, 23.5), (37, 23.5), None)
    arrow(ax, (50, 23.5), (55, 23.5), None)
    # dmem 总线 → MMIO（底部绕行）
    line(ax, [(30, 18), (30, 14.5), (76, 14.5), (76, 17.7)], color="#7E22CE", lw=1.4)
    arrow(ax, (76, 16.5), (76, 17.7), None, color="#7E22CE")
    ax.text(53, 16.3, "dmem 总线：addr / we / be / rdata", fontsize=8.5, color="#7E22CE",
            ha="center", va="center", zorder=4, bbox=dict(fc="white", ec="none", pad=0.3))

    note(ax, 3, 9.5, "MMIO 读：地址命中计时器时同拍替换 dmem_rdata；写计时器被忽略，不落 DMEM。", fs=9.5)
    note(ax, 3, 6.3, "v0 无转发、无停顿：RAW 相关靠固件调度避免；load 紧跟使用需固件插 nop。", fs=9.5,
         color="#B45309")
    save(fig, "fig3_core_v0.png")


# --------------------------------------------------------- 图 4 v1 三级流水
def fig4_core_v1():
    fig, ax = fig_new(18, 10.5)
    title(ax, "图 4　v1 三级流水与转发：if_stage / id_ex_stage / mem_wb_stage",
          "契约见 design_v1.md。流水充满后每拍一条；三个转发来源共享同一组选择器，优先级 EX>MEM>WB")

    zone(ax, 1, 50, 27, 34, "IF", kind="gray", fs=12)
    zone(ax, 31, 16, 37, 68, "ID+EX（组合级）", kind="gray", fs=12)
    zone(ax, 71, 24, 28, 60, "MEM+WB", kind="gray", fs=12)
    box(ax, 38, 84, 28, 8, "hazard", kind="warn", fs=12,
        sub="load-use → front_stall　·　taken → redirect / if_flush")

    # ---- IF ----
    box(ax, 4, 68, 9, 8, "pc", sub="+hold", fs=11)
    box(ax, 16, 68, 10, 8, "imem", kind="mem", sub="同步读", fs=10.5)
    box(ax, 4, 54, 22, 9, "if_stage", sub="IF/ID 边界：if_valid / if_pc / if_instr", fs=11)
    arrow(ax, (13, 72), (16, 72), "imem_addr", fs=8.5)
    arrow(ax, (8.5, 68), (8.5, 63.3), None)
    arrow(ax, (21, 68), (15, 63.3), None, rad=-0.12)
    # front_stall：hazard → pc
    arrow(ax, (38, 88), (8.5, 76.3), "front_stall → PC 保持", color=RED, rad=-0.08,
          toff=(-1.5, 3.2), fs=9)
    # if_flush：hazard → if_stage（走两面板间走廊）
    line(ax, [(37.7, 85), (29.5, 85), (29.5, 59), (26.3, 59)], color=RED)
    arrow(ax, (28, 59), (26.3, 59), None, color=RED)
    ax.text(28, 72, "if_flush → 注入 NOP", fontsize=8.8, color=RED, ha="center",
            va="center", rotation=90, zorder=4)

    # ---- ID+EX ----
    box(ax, 33, 66, 13, 8, "decode", sub="uses_rs1/2", fs=11)
    box(ax, 50, 66, 13, 8, "regfile", kind="mem", sub="2R1W", fs=11)
    box(ax, 34, 52, 14, 9, "转发选择", sub="rs1_fwd / rs2_fwd\nEX>MEM>WB", fs=11)
    box(ax, 52, 52, 12, 9, "alu", sub="y + 标志", fs=11)
    box(ax, 34, 38, 12, 8, "muldiv", kind="warn", sub="ID+EX 等待", fs=10.5)
    box(ax, 50, 38, 13, 8, "分支 / 跳转裁决", sub="redirect_target", fs=10)
    box(ax, 34, 25, 29, 8, "ID+EX/MEM+WB 边界 → mem_wb_stage", sub="mem_valid + 结果 + 提交控制", fs=10.5)
    arrow(ax, (39.5, 66), (40, 61.3), None)
    arrow(ax, (56, 66), (44, 61.3), "rdata", fs=8.5, rad=-0.1, toff=(3.5, 1.2))
    arrow(ax, (48, 56.5), (52, 56.5), None)
    arrow(ax, (58, 52), (56.5, 46.3), None)
    arrow(ax, (40, 38), (42, 33.3), None)
    arrow(ax, (56.5, 38), (52, 33.3), None)
    # EX→EX：alu 结果旁路回本级的转发选择（供下一条指令使用）
    arrow(ax, (53, 51.7), (48.3, 57), None, color=FWD["EX"], rad=0.35, lw=1.9)
    ax.text(48, 50.2, "EX→EX", fontsize=9.5, color=FWD["EX"], ha="right",
            va="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", pad=0.3))
    # MEM→EX：mem_wb 槽的结果旁路
    arrow(ax, (75.7, 42), (48.3, 54), "MEM→EX", color=FWD["MEM"], lw=1.9,
          toff=(-2.0, -2.2), fs=9.5)
    # WB→EX：写回级的数据旁路（底部绕行）
    line(ax, [(85, 37.7), (85, 21), (67, 21), (67, 49), (44.5, 49), (44.5, 51.7)],
         color=FWD["WB"], lw=1.9)
    arrow(ax, (44.5, 50.4), (44.5, 51.7), None, color=FWD["WB"])
    ax.text(69.5, 30, "WB→EX", fontsize=9.5, color=FWD["WB"], ha="center",
            va="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", pad=0.3))

    # ---- MEM+WB ----
    box(ax, 73, 66, 24, 8, "mem_wb_stage 边界寄存器", sub="store 副作用只在此级提交", fs=10.5)
    box(ax, 73, 52, 9, 9, "dmem", kind="mem", sub="读/写", fs=10.5)
    box(ax, 86, 52, 11, 9, "load 扩展", sub="byte/half", fs=10.5)
    box(ax, 76, 38, 18, 8, "写回 regfile / store 提交", sub="mem_wb.valid 门控", fs=10)
    arrow(ax, (77, 66), (77.5, 61.3), None)
    arrow(ax, (91, 66), (91.5, 61.3), None)
    arrow(ax, (77.5, 52), (82, 46.3), None)
    arrow(ax, (91.5, 52), (87, 46.3), None)

    note(ax, 2, 10,
         "· 转发开关 = 顶层 parameter enable_forwarding（v1 无转发对照档：RAW 一律停顿）\n"
         "· load-use 固定停 1 拍，不做 DMEM→ALU 组合旁路；taken 分支固定冲刷，not-taken 无气泡\n"
         "· 任何寄存器写 / 访存写 / 跳转都必须同时满足所属流水槽 valid=1（NOP 仅为波形可读）",
         fs=9.8)
    save(fig, "fig4_core_v1.png")


# ------------------------------------------------------- 图 5 视觉三线拓扑
def fig5_vision_pipeline():
    fig, ax = fig_new(18, 11)
    title(ax, "图 5　视觉流水线三线拓扑：video_pipeline + vision_top（v0.4）",
          "同 pclk 像素域逐拍推进，无 ready 反压；vs=帧首单拍、hs=行尾单拍、de=像素有效")

    # 输入
    box(ax, 1, 44, 13, 14, "in_align", sub="归一化：vs 边沿单拍化\nhs 重定时为 de 落后 3 拍\n撞拍顺延不丢失")
    ax.text(2.2, 60.5, "dvi2rgb：raw_vs/hs/de + RGB[23:0]", fontsize=9, color=ARROW)
    arrow(ax, (1.5, 58), (7, 58), None, rad=0.0)
    note(ax, 1, 38.5, "video_pipeline 门控：\n首个 vs 之前 seen_frame=0，\n分析路径不放行（防半帧）", fs=9)

    # 显示线
    box(ax, 18, 78, 24, 12, "显示直通寄存", kind="disp",
        sub="原始波形恒 1 拍 + display_frame_id\n分析开关 / 反压均不影响")
    box(ax, 47, 78, 18, 12, "vision_axi → rgb2dvi", kind="disp", sub="HDMI OUT 全分辨率")
    arrow(ax, (10, 58), (22, 78), "raw 波形旁路", rad=0.12, toff=(-4, 2))
    arrow(ax, (42, 84), (47, 84), None)

    # 分析线
    y0 = 48
    box(ax, 18, y0, 9, 9, "rgb2gray", sub="1 拍", fs=10)
    box(ax, 30, y0, 4.5, 9, "M1", sub="mux\n gauss_en", fs=9)
    box(ax, 38, y0, 11, 9, "gaussian_3x3", sub="3×3 移位加\n落后 1 行", fs=10)
    box(ax, 52, y0, 4.5, 9, "M1b", sub="mux\n sobel_en", fs=9)
    box(ax, 60, y0, 9, 9, "sobel", sub="3 拍", fs=10)
    box(ax, 72, y0, 9, 9, "osd_overlay", sub="框坐标来自\nactive_cfg", fs=9.5)
    box(ax, 84, y0, 4.5, 9, "M3", sub="mux\n osd_en", fs=9)
    arrow(ax, (27, y0 + 4.5), (30, y0 + 4.5), None)
    arrow(ax, (34.5, y0 + 4.5), (38, y0 + 4.5), None)
    arrow(ax, (49, y0 + 4.5), (52, y0 + 4.5), None)
    arrow(ax, (56.5, y0 + 4.5), (60, y0 + 4.5), None)
    arrow(ax, (69, y0 + 4.5), (72, y0 + 4.5), None)
    arrow(ax, (81, y0 + 4.5), (84, y0 + 4.5), None)
    arrow(ax, (10, 51), (18, y0 + 4.5), "RGB → Y", rad=0.05, toff=(3.2, 3.2), fs=8.5)
    # 旁路弧线
    arrow(ax, (27, y0 + 7.5), (30, y0 + 7.5), None, rad=0.55)
    arrow(ax, (49, y0 + 7.5), (52, y0 + 7.5), None, rad=0.55)
    arrow(ax, (81, y0 + 7.5), (84, y0 + 7.5), None, rad=0.55)
    arrow(ax, (88.5, y0 + 4.5), (98, y0 + 4.5), "out_* 灰度诊断流\n（不驱动物理 HDMI）", toff=(-3, 6.5))
    note(ax, 33, y0 + 12.3, "旁路 mux：开关取自 active_cfg，帧内恒定", fs=9)

    # 快照线
    ys = 22
    box(ax, 26, ys, 15, 10, "scaler", kind="cop", sub="16.16 双线性\n1 像素 / 2 拍 → 224×224", fs=11)
    box(ax, 45, ys, 8, 10, "t_scaler 门控", kind="cop", sub="R0 bit1", fs=10)
    box(ax, 57, ys, 13, 10, "cop_buf", kind="cop", sub="乒乓帧缓冲\n整帧原子回放", fs=11)
    box(ax, 74, ys, 16, 10, "CNN 协处理器", kind="cop", ls="--",
        sub="模块三（未实现）", fs=11)
    arrow(ax, (56.5, y0 + 1.5), (33.5, ys + 10), "sobel 后分叉（D7：缩放前）",
          rad=0.12, toff=(4.5, -1.5), fs=8.8)
    arrow(ax, (41, ys + 5), (45, ys + 5), None)
    arrow(ax, (53, ys + 5), (57, ys + 5), None)
    arrow(ax, (70, ys + 5), (74, ys + 5), "cop_* 224×224\n+ frame/config id", ls="--",
          toff=(0, 4.6), fs=8.5)
    note(ax, 57, ys - 2.5, "cop_ready=1 才允许启动下一帧回放（整帧许可，帧内不中断）", fs=9)

    # 配置线
    box(ax, 18, 4, 13, 9, "axi_regs", kind="cfg", sub="R0–R10 暂存 · R11 提交\nR12 已应用编号", fs=10)
    box(ax, 36, 4, 14, 9, "config_bridge", kind="cfg", sub="请求/确认跨时钟域\n（图 6）", fs=10)
    arrow(ax, (31, 8.5), (36, 8.5), "regs_flat 352bit", fs=8.5)
    line(ax, [(43, 13), (43, 44), (32, 44), (32, 47.7)], color="#7E22CE", ls="--", lw=1.6)
    arrow(ax, (32, 46.2), (32, 47.7), None, color="#7E22CE", ls="--")
    ax.text(45, 42.5, "active_cfg：链路开关 + OSD 框坐标，帧首整组应用", fontsize=9,
            color="#7E22CE", ha="left", va="center", zorder=4,
            bbox=dict(fc="white", ec="none", pad=0.4))
    note(ax, 53, 6, "active_cfg 352bit → M1/M1b/M3 开关、OSD 框坐标、t_scaler 门控", fs=9,
         color="#7E22CE")
    save(fig, "fig5_vision_pipeline.png")


# ------------------------------------------------------- 图 6 配置跨时钟域
def fig6_config_cdc():
    fig, ax = fig_new(17, 9.5)
    title(ax, "图 6　配置整组原子提交：axi_regs → config_bridge → 帧首应用",
          "问题：PS 配置时钟与像素时钟异步。解法：请求/确认握手 + 确认前数据总线恒定（CDC 契约见 config_cdc.xdc）")

    zone(ax, 1, 6, 44, 82, "AXI 配置域（s_axi_aclk）", kind="cfg", fs=12)
    zone(ax, 55, 6, 44, 82, "像素域（pclk）", kind="pl", fs=12)

    box(ax, 3, 70, 15, 11, "PS Linux", kind="cfg", sub="vision_regs.py\ncommit()/wait_applied()", fs=11)
    box(ax, 24, 62, 18, 19, "axi_regs", kind="cfg",
        sub="R0–R10 暂存区\nR11 commit / 读回 busy\nR12 applied_id 只读\nbusy 期重复提交 → SLVERR", fs=10.5)
    box(ax, 3, 22, 39, 30, "config_bridge　src 侧", kind="cfg",
        sub="src_commit 且 !busy：锁存 hold_data(352bit) / hold_id+1，\nrequest 翻转；ack 经 2FF 回来后 busy 释放、\nsrc_applied ← hold_id（软件读 R12 得到确认编号）", fs=9.5)
    box(ax, 58, 55, 38, 26, "config_bridge　dst 侧", kind="pl",
        sub="request 经 ASYNC_REG 两级同步进入像素域；\n帧首 in_vs 采样：dst_data ← hold_data、dst_id ← hold_id、\nacknowledge ← 同步后的 request（在帧首一次性应用整组）", fs=9.5)
    box(ax, 58, 22, 38, 20, "vision_top：active_cfg 生效", kind="pl",
        sub="各级开关 / OSD 框坐标当帧起使用新配置；\nactive_config_id 回送 AXI 域（R12 读数）", fs=10)

    arrow(ax, (12, 70), (30, 76), "AXI-Lite 写/读", rad=-0.1, toff=(-4, 2))
    arrow(ax, (30, 62), (26, 52), "regs_flat + commit", rad=0.05, toff=(6, 1))
    # 跨域主路径
    arrow(ax, (42, 40), (58, 62), "request（1bit）+ hold_data",
          color="#7E22CE", lw=2.2, rad=-0.12, toff=(-3.5, 6.5), fs=8.8)
    # 回传
    arrow(ax, (77, 55), (20, 33), "acknowledge（2FF 回传）→ busy 释放、R12 递增",
          color="#15803D", rad=-0.12, toff=(-8, -7.5), fs=8.8)
    arrow(ax, (77, 55), (77, 42), None)
    ax.text(51.5, 24, "跨时钟域", fontsize=10, color="#7E22CE", rotation=90,
            ha="center", va="center", fontweight="bold")

    note(ax, 2, 4, "① 确认前 hold 总线必须恒定 → set_max_delay -datapath_only 约束（不用 async clock group 掩盖）\n"
                   "② 原子性：像素域只在帧首取整组，绝不见到半新半旧配置\n"
                   "③ 无新视频帧时 busy 保持：软件必须带超时；锁定丢失（video_locked=0）时 AXI 域不复位，在途响应照常完成",
         fs=9.6)
    save(fig, "fig6_config_cdc.png")


# ------------------------------------------------------- 图 7 cop_buf 乒乓
def fig7_copbuf():
    fig, ax = fig_new(16, 9)
    title(ax, "图 7　cop_buf 快照乒乓帧缓冲：模块二 → 模块三的交接件",
          "接口为占位：cop 契约冻结后仅改读侧封装（valid/de vs AXI-Stream），存储体与写侧不动（design_v0.md §7）")

    box(ax, 1, 55, 16, 14, "scaler 快照流", kind="cop", sub="vs / hs / de / y\n224×224（real 档）", fs=11)
    box(ax, 1, 32, 16, 14, "写控制", kind="cop",
        sub="writing 门控写使能\nin_de 写 {row,col}\n末行提交 = 帧完成", fs=11)
    box(ax, 25, 62, 20, 16, "Bank0　mem0[]", kind="mem",
        sub="DW×DH × 8bit BRAM\nbank_frame / bank_config\nbuf_valid[0]", fs=11)
    box(ax, 25, 30, 20, 16, "Bank1　mem1[]", kind="mem",
        sub="DW×DH × 8bit BRAM\nbank_frame / bank_config\nbuf_valid[1]", fs=11)
    box(ax, 53, 46, 20, 18, "回放引擎", kind="cop",
        sub="整帧原子启动；1 像素/拍\n自产 vs / hs（末 de 后 4 拍）/ de", fs=11)
    box(ax, 79, 46, 19, 18, "cop_* 输出流", kind="cop",
        sub="y + cop_frame_id\ncop_config_id\ndrop_count", fs=11)
    box(ax, 53, 14, 20, 12, "cop_ready", kind="gray",
        sub="消费侧整帧启动许可\n（帧内不中断）", fs=11)

    arrow(ax, (9, 55), (9, 46), None)
    arrow(ax, (17, 62), (25, 68), "写中", color="#BE123C")
    arrow(ax, (17, 39), (25, 36), "等待乒乓翻转", color="#B45309", ls="--", fs=8.5)
    arrow(ax, (45, 68), (45, 44), None, rad=0.35, color="#B45309")
    ax.text(46, 66.5, "乒乓翻转：\n下一帧写另一片", fontsize=8.8, color="#B45309",
            ha="left", va="center", zorder=4, linespacing=1.4,
            bbox=dict(fc="white", ec="none", pad=0.3))
    arrow(ax, (45, 38), (53, 50), "读完整帧", color="#1D4ED8", rad=-0.1, fs=8.5)
    arrow(ax, (63, 46), (63, 26), None, color="#374151")
    arrow(ax, (73, 55), (79, 55), None)
    arrow(ax, (73, 20), (60, 46), "cop_ready=1 → 启动", rad=0.15, toff=(6.5, 2), fs=8.5)
    note(ax, 79, 40, "回放携带该银行的帧号与配置号；\n新帧覆盖未消费帧 → drop_count++", fs=9)

    note(ax, 1, 12,
         "所有权规则（争用修复后口径，tb_cop_buf + tb_cop_buf_stress 双 tb 覆盖）：\n"
         "· 正在回放、或本拍启动回放的银行，禁止成为写银行（读写同拍串帧路径已封死）\n"
         "· 复位后必须先看到完整帧首：半帧不写入、不发布\n"
         "· 读缓冲恒 ≠ 写缓冲（不变式）：同拍读写无冲突，不需要 read-during-write 语义",
         fs=9.6)
    save(fig, "fig7_copbuf.png")


if __name__ == "__main__":
    fig1_system()
    fig2_rtl_tree()
    fig3_core_v0()
    fig4_core_v1()
    fig5_vision_pipeline()
    fig6_config_cdc()
    fig7_copbuf()
    print("all 7 diagrams done ->", OUT)
