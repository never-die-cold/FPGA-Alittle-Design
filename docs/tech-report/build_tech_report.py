# -*- coding: utf-8 -*-
"""build_tech_report.py —— 生成《边缘慧眼（EdgeSight）》技术文档初版 DOCX。

用法：py docs/tech-report/build_tech_report.py
输入：docs/tech-report/figures/*.png
输出：docs/tech-report/EdgeSight-技术文档-初版.docx
版式：A4，正文宋体小四 1.3 倍行距，首行缩进 2 字符；标题黑体；表注上图注下。
"""
import os
import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "EdgeSight-技术文档-初版.docx")

SONG = "宋体"
HEI = "黑体"
TNR = "Times New Roman"
BLACK = RGBColor(0, 0, 0)
GRAY = RGBColor(0x59, 0x59, 0x59)
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)


# ------------------------------------------------------------------ 基础工具
def set_run_font(run, east=SONG, ascii_font=TNR, size=12, bold=False,
                 color=BLACK, italic=False):
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), ascii_font)
    rFonts.set(qn("w:hAnsi"), ascii_font)
    rFonts.set(qn("w:eastAsia"), east)


def add_body(doc, text, indent=True, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             space_before=0, space_after=0, bold=False, color=BLACK):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(size * 2) if indent else None
    pf.line_spacing = 1.3
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    p.alignment = align
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, color=color)
    return p


def add_h1(doc, text, page_break=True):
    p = doc.add_paragraph(style="Heading 1")
    pf = p.paragraph_format
    pf.page_break_before = page_break
    pf.space_before = Pt(6)
    pf.space_after = Pt(10)
    pf.line_spacing = 1.2
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, east=HEI, size=16, bold=True)
    return p


def add_h2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.2
    pf.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    set_run_font(r, east=HEI, size=14, bold=True)
    return p


def add_h3(doc, text):
    p = doc.add_paragraph(style="Heading 3")
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.2
    pf.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    set_run_font(r, east=HEI, size=12, bold=True)
    return p


def add_body_rich(doc, segs, indent=True, size=12):
    """富文本正文段：segs = [(text, fmt), ...]，fmt 含 i=斜体、sub=下标、sup=上标、
    mono=等宽；用于公式字符的规范排版（变量斜体 + 真下标，等价 LaTeX 渲染效果）。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(size * 2) if indent else None
    pf.line_spacing = 1.3
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for text, fmt in segs:
        tokens = (fmt or "").split()
        r = p.add_run(text)
        if "mono" in tokens:
            set_run_font(r, ascii_font="Consolas", east=SONG, size=size - 1)
        else:
            set_run_font(r, size=size, italic="i" in tokens)
        if "sub" in tokens:
            r.font.subscript = True
        if "sup" in tokens:
            r.font.superscript = True
    return p


def add_caption(doc, text, above=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = None
    pf.line_spacing = 1.15
    pf.space_before = Pt(4 if above else 3)
    pf.space_after = Pt(3 if above else 8)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if above:
        pf.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, size=10.5, color=BLACK)
    return p


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_cell_margins(table, top=40, bottom=40, left=90, right=90):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for tag, val in (("top", top), ("left", left), ("bottom", bottom),
                     ("right", right)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def add_table(doc, caption, headers, rows, widths_cm, font_size=10.5,
              header_fill="DCE6F1", align_center_cols=None, mono_cols=None):
    add_caption(doc, caption, above=True)
    # 统一缩放到正文宽度（14.4 cm），避免表格越出页边距
    total = sum(widths_cm)
    widths_cm = [w * 14.4 / total for w in widths_cm]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_cell_margins(table)
    align_center_cols = align_center_cols or []

    hdr = table.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    trPr.append(OxmlElement("w:cantSplit"))
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = Cm(widths_cm[i])
        shade(cell, header_fill)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        set_run_font(r, size=font_size, bold=True)

    for row in rows:
        tr = table.add_row()
        tr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, val in enumerate(row):
            cell = tr.cells[i]
            cell.width = Cm(widths_cm[i])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = (WD_ALIGN_PARAGRAPH.CENTER if i in align_center_cols
                           else WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            if mono_cols and i in mono_cols:
                set_run_font(r, ascii_font="Consolas", east=SONG,
                             size=font_size - 0.5)
            else:
                set_run_font(r, size=font_size)
    # 小表尽量不跨页：除最后一行外，其余行与下一行同页
    for ri, row in enumerate(table.rows):
        if ri < len(table.rows) - 1:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
    # 表后空一点
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_figure(doc, filename, caption, width_cm=14.4):
    path = os.path.join(FIG, filename)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = None
    pf.space_before = Pt(6)
    pf.space_after = Pt(0)
    pf.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    add_caption(doc, caption, above=False)


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE \\* arabic "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(txt)
    run._r.append(fld_end)


def bottom_border(paragraph, color="1F3A5F", sz=8):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz))
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def count_cn(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def section_count(title, paragraphs):
    n = sum(count_cn(p) for p in paragraphs)
    print(f"[字数] {title}: {n}")
    return n


# ------------------------------------------------------------------ 文档设置
doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)
sec.left_margin = Cm(3.17)
sec.right_margin = Cm(3.17)
sec.header_distance = Cm(0.9)
sec.footer_distance = Cm(1.0)

normal = doc.styles["Normal"]
normal.font.name = TNR
normal.font.size = Pt(12)
normal.font.color.rgb = BLACK
normal._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.3
normal.paragraph_format.space_after = Pt(0)

for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
    st = doc.styles[name]
    st.font.name = TNR
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = BLACK
    st._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)

props = doc.core_properties
props.title = "边缘慧眼（EdgeSight）技术文档（初版）"
props.subject = "2026 年全国大学生嵌入式芯片与系统设计竞赛 AMD 自主命题赛道"
props.author = "EdgeSight 团队"
props.comments = "修订版 V1.0；按评审意见修订：摘要精简、公式排版、指标口径对齐传统基准、EXE 改 HTML、新增 LLM 协作与 Skills 沉淀。"

# 页眉页脚：每页页眉为竞赛横幅（「芯辰大海 FPGA · 点亮未来」，取自官方参考模板，
# 显示 6.52 cm × 1.19 cm 居中），下沿保留细分隔线
header = sec.header
header.is_linked_to_previous = False
hp = header.paragraphs[0]
hp.text = ""
hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
hp.paragraph_format.space_after = Pt(2)
hr = hp.add_run()
hr.add_picture(os.path.join(FIG, "header_banner.png"), width=Cm(6.52))
bottom_border(hp, color="BFBFBF", sz=4)

footer = sec.footer
footer.is_linked_to_previous = False
fp = footer.paragraphs[0]
fp.text = ""
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_field(fp)
for r in fp.runs:
    set_run_font(r, size=9, color=GRAY)

# ------------------------------------------------------------------ 标题块
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
r = p.add_run("2026 年全国大学生嵌入式芯片与系统设计竞赛")
set_run_font(r, size=11, color=GRAY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("AMD 自主命题赛道（初级组）· 技术文档")
set_run_font(r, size=10.5, color=GRAY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(14)
p.paragraph_format.space_after = Pt(2)
p.paragraph_format.line_spacing = 1.2
r = p.add_run("边缘慧眼（EdgeSight）")
set_run_font(r, east=HEI, size=26, bold=True, color=ACCENT)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("面向桌面紧固件的 RISC-V SoC 与 INT8 CNN 协处理器检查系统")
set_run_font(r, size=13, color=BLACK)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
r = p.add_run("修订版 V1.0　·　2026 年 10 月")
set_run_font(r, size=10.5, color=GRAY)
bottom_border(p, color="1F3A5F", sz=10)

# ------------------------------------------------------------------ 摘要
abstract = (
    "针对多品种、小批量装配工位对紧固件种类与数量复核的需求，本作品在 PYNQ-Z2 上实现了一套桌面紧固件识别与工业检查系统，四条链路均自主设计："
    "自研 RV32IM 三级流水 RISC-V 核（三路转发、64 项可切换 BHT、Radix-4 乘法器）负责调度与工单判定；"
    "HDMI 视觉流水线完成 720p60 采集与彩色直通、灰度分析、224×224 快照三路分流；"
    "128 MAC 的 INT8 CNN 协处理器完成逐目标分类；PS 服务与 HTML 网页端负责工单比较、批次记录与展示。"
    "核通过 44/44 组 arch-test 与 CoreMark 四档消融，CPI 由 1.886 降至 1.606，OOC 86.806 MHz；"
    "视觉流水线 22 个 testbench 双仿真器同判据通过并上板 720p 直通；"
    "协处理器通过全部离板门禁，板上 zero/pattern/roi_001/frame 四例与黄金输出一致；"
    "软件通过 172 条回归与 4 轮异常矩阵，网页端已接入采集卡回传完成轮次联调。"
    "多目标修复包尚未上板，正式模型与整机验收未完成——本文严格区分四级证据，不以前级替代板上结论。"
)
add_h1(doc, "摘要", page_break=False)
section_count("摘要", [abstract])
add_body(doc, abstract)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("关键词：")
set_run_font(r, size=10.5, bold=True)
r = p.add_run("RISC-V；INT8 神经网络；FPGA；边缘视觉；工业检查；CNN 协处理器")
set_run_font(r, size=10.5)

# ================================================================== 第一部分
add_h1(doc, "第一部分　作品概述")

add_h2(doc, "1.1 功能与特性")
p11 = (
    "系统面向桌面工件复核，提供五项功能。其一，自由摆放识别：零件无需固定夹具，传统视觉定位给出外接框，CNN 对每个目标裁剪小图分类为螺栓、螺母或垫圈。"
    "其二，工单检查：将实际类别计数与工单期望比较，输出缺件、多余件、错料及对应数量。"
    "其三，同屏呈现：HDMI 彩色原图经采集卡进入网页端，叠加目标框、类别、置信度与判定结果。"
    "其四，批次记录：每次手动检查生成一条记录，保存截图、结果报文、协处理器 trace 与 ROI，可导出 CSV。"
    "其五，异常防护：超时、重复请求、陈旧结果、运行失败和断联均进入明确错误态，不显示为检查通过。"
)
section_count("1.1 功能与特性", [p11])
add_body(doc, p11)

add_h2(doc, "1.2 应用领域")
p12 = (
    "适用于 3C 与家电装配工位的小件复核、多品种小批量换线后的首件确认、包装计数与来料抽检等场景；"
    "也可作为 RISC-V 微架构、FPGA 视频处理和边缘 INT8 推理的教学与科研平台。"
    "首版支持自由分散且互不遮挡的紧固件，要求受控光照与稳定背景；堆叠、接触遮挡、裂纹和尺寸超差检测不在首版范围。"
    "系统目标以桌面级成本和低功耗完成本地推理，结果不出厂区，适合对数据隐私和实时性有要求的产线边缘部署。"
)
section_count("1.2 应用领域", [p12])
add_body(doc, p12)

add_h2(doc, "1.3 主要技术特点")
p13 = (
    "（1）全栈自研：除 Xilinx dvi2rgb/rgb2dvi IP 外，RISC-V 核、HDMI 视觉流水线、CNN 协处理器、驻留固件、PS 服务和网页端均由团队实现，接口以仓库内契约文档冻结。"
    "（2）显示与分析解耦：彩色原图恒 1 拍直通显示，灰度分析与 224×224 快照独立推进，分析开关和反压不影响上屏。"
    "（3）契约化软硬件协作：寄存器、报文、模型清单和作业时序均有版本化文档与门禁。"
    "（4）全整数推理：INT8 权重与激活、INT32 累加、移位 requant，模型载荷带 SHA256 与 CRC32，双 bank 影子配置原子切换。"
    "（5）结果消费语义：ACCEPTED、UNCONSUMED、CONSUME 与 RESULT_SEQ 构成一次性结果窗口，先持久化后消费，杜绝重复和陈旧结果被当作通过。"
    "（6）证据驱动：每个结论都有仓库内 testbench、脚本和原始日志。"
)
section_count("1.3 主要技术特点", [p13])
add_body(doc, p13)

add_h2(doc, "1.4 主要性能指标")
add_body(doc, "主要指标如表 1-1 所示，均取自仓库内原始日志；仿真、综合和板上结果分别标注。", indent=True)
add_table(doc, "表 1-1　主要性能指标", ["项目", "结果"], [
    ["处理器核 ISA / 流水", "RV32IM；三级；转发；64 项 BHT"],
    ["CoreMark 2K/32", "CPI 1.606；CoreMark/MHz 1.974"],
    ["核 OOC 时序", "86.806 MHz；WNS +0.538 ns"],
    ["视觉链路", "1280×720@60；74.25 MHz；WNS +0.330 ns"],
    ["协处理器", "128 MAC；36,032 B；11.94M MAC/ROI"],
    ["协处理器 40 MHz 全系统", "WNS +2.498；DSP 136/220；BRAM 69/140"],
    ["软件接口", "HTTP/JSON；≤16 目标；≤64 KiB"],
    ["板上验证", "40 MHz；20/20 STATUS=0x1；四例黄金通过"],
], [5.2, 9.2], font_size=9.5)

add_h2(doc, "1.5 主要创新点")
p15 = (
    "① 自研三级 RISC-V 核把转发、可切换 BHT 与 Radix-4 乘法放在同一基线做四档量化对比，CPI 1.606、44/44 签名。"
    "② 显示/分析/快照三路径解耦与整帧原子快照，保证上屏画质与分析带宽互不影响。"
    "③ 以“消费”为核心的 A2 结果语义，把重复、陈旧和未消费结果挡在判定之外。"
    "④ INT8 全整数通路配清单化模型载荷和双 bank 原子切换。"
    "⑤ 证据驱动开发：仿真、软件、板上三级别分别留痕，不以低级别证据替代板上结论。"
)
section_count("1.5 主要创新点", [p15])
add_body(doc, p15)

add_h2(doc, "1.6 设计流程")
p16 = (
    "流程分为八步：需求与验收口径冻结、接口契约（寄存器/报文/清单）、RTL 与模块 testbench、全量回归、综合与时序、板上 bring-up、软件联调、证据归档。"
    "每一步以门禁收口：回归必须零意外失败，时序必须 WNS≥0，板上必须有关键寄存器回读，软件必须有可重放的检查轮次。"
    "仿真、软件和板上证据分别标注，结论不跨级替代。"
)
section_count("1.6 设计流程", [p16])
add_body(doc, p16)

# ================================================================== 第二部分
add_h1(doc, "第二部分　系统组成及功能说明")

add_h2(doc, "2.1 整体介绍")
add_figure(doc, "fig_system.png", "图 2-1　系统总体架构与数据路径")
p21 = (
    "系统总体架构如图 2-1 所示。系统由四部分组成：HDMI 相机、PYNQ-Z2 板卡、USB 采集卡和 Windows PC。相机输出 1280×720@60 彩色图像，经 dvi2rgb 进入 PL。"
    "PL 内三条硬件链路并行工作：视觉流水线把彩色原图恒 1 拍直通到 rgb2dvi，同时把灰度分析流和 224×224 快照送往 CNN 协处理器；"
    "自研 RISC-V SoC 运行驻留固件，负责启动推理、读取结果并执行工单规则；INT8 CNN 协处理器完成逐目标分类。"
    "PS 运行 Linux 与 Python 服务，经 AXI-Lite 配置，模型/ROI 经 AXI DMA 传输（实板由 loader 先行验证，服务侧 DMA 平面待接入），并把结果以 HTTP/JSON 发给网页端。"
    "网页端负责视频预览、目标框叠加、工单比较、计数和批次记录。"
)
add_body(doc, p21)
p21b = (
    "数据分三条路径。视频路径为 HDMI OUT→USB 采集卡→网页端，保证彩色原图不经分析链路；结果路径为 PS→以太网→网页端，携带检查标识、帧号、目标列表和判定；"
    "控制路径为网页端→PS→PL，提交工单配置和检查触发。每条结果都带 session、config、frame 和 RESULT_SEQ，"
    "网页端只接受与当前会话和配置一致、且在有效期内的结果。"
)
add_body(doc, p21b)
p21c = (
    "系统当前进展：视频链路、RISC-V 核与硬件 CNN 单目标推理已在板上验证（zero/pattern/roi_001/frame 四例黄金对拍一致）；"
    "共存位流可同时输出 HDMI、抓取 BGR 原帧并运行硬件 CNN；网页端已接入 USB 采集卡回传与板端服务轮次。"
    "多目标结果槽错位的修复已通过定向仿真，修复包尚未上板；正式模型、识别精度与整机验收仍未完成。"
)
add_body(doc, p21c)
p21d = (
    "当前共存位流保留彩色显示与完整 BGR 原帧捕获；PL 灰度/高斯/缩放分析输出暂无消费者，定位、ROI 与量化由 PS 执行。"
)
add_body(doc, p21d)
section_count("2.1 整体介绍", [p21, p21b, p21c, p21d])

add_h2(doc, "2.2 硬件系统介绍")
add_h3(doc, "2.2.1 硬件整体介绍")
p221 = (
    "硬件采用 PYNQ-Z2 开发板，主器件为 XC7Z020-1CLG400C：PL 含 53,200 个逻辑单元、140 个 BRAM36 和 220 个 DSP48E1；"
    "PS 为双核 ARM Cortex-A9，配 512 MB DDR3。板卡提供 HDMI 输入/输出、千兆以太网、USB Host 和 microSD。"
    "HDMI 视频源由树莓派及其摄像头模组提供 1280×720@60 图像，与 PYNQ-Z2 同装于亚克力支架（图 2-2）；"
    "采集卡把板卡 HDMI OUT 转为 UVC 送入 PC。"
)
add_body(doc, p221)
p221b = (
    "时钟分为三个域：PS FCLK0 为 100 MHz，供 AXI 互连和 PS 外设；FCLK1 为 40 MHz，供 RISC-V 核与协处理器；HDMI 像素时钟为 74.25 MHz。"
    "复位采用异步置位、同步释放；跨域配置用 2FF 同步，模型与 ROI 数据用异步 FIFO。"
)
add_body(doc, p221b)
add_table(doc, "表 2-1　硬件组成", ["模块", "型号 / 规格", "作用"], [
    ["FPGA 板卡", "PYNQ-Z2；XC7Z020-1CLG400C", "PL + PS、DDR3、HDMI、以太网"],
    ["HDMI 相机", "1280×720@60", "采集桌面工件图像"],
    ["USB 采集卡", "HDMI→UVC", "把板卡 HDMI OUT 送入 PC 网页端"],
    ["PC", "Windows 10/11", "网页端、记录与导出"],
    ["时钟", "FCLK0 100 MHz / FCLK1 40 MHz / pclk 74.25 MHz", "AXI / 协处理器 / 像素"],
], [3.2, 6.6, 5.2], font_size=10.5, align_center_cols=[0])
add_figure(doc, "photo_board_pi.jpg", "图 2-2　硬件实物：PYNQ-Z2 与提供 HDMI 视频源的树莓派摄像头模组（同装于亚克力支架）", width_cm=7.5)

add_h3(doc, "2.2.2 机械设计介绍")
p222 = (
    "本项目不设计机械结构。首版采用现成相机支架、板卡铜柱和桌面布置，保证相机光轴垂直桌面、视场覆盖 A4 幅面。"
    "机械自由度由支架的俯仰和高度调节提供，不涉及定制加工件。实物布置照片见第三部分图 3-1。"
)
add_body(doc, p222)

add_h3(doc, "2.2.3 电路各模块介绍")
p223 = (
    "本项目不设计自制 PCB，电路成果体现为 PYNQ-Z2 板级集成、HDMI 输入/输出链路、时钟与复位设计，以及可综合的 PL 工程。"
    "板级电路模块如表 2-2 所示。"
)
add_body(doc, p223)
add_table(doc, "表 2-2　板级电路模块", ["模块", "实现", "关键信号"], [
    ["HDMI 输入", "dvi2rgb IP", "TMDS 差分对→RGB888、vs/hs/de、pclk"],
    ["PL 逻辑", "视频流水线 / RISC-V SoC / CNN 协处理器", "display_*、cop_*、AXI-Lite、AXI-Stream"],
    ["HDMI 输出", "rgb2dvi IP", "RGB888→TMDS 差分对"],
    ["PS 外设", "DDR3、SD、以太网、USB", "AXI HP/GP、MIO"],
    ["时钟与复位", "PS FCLK0/1、MMCM、reset_sync", "100 MHz、40 MHz、74.25 MHz、异步置位同步释放"],
], [3.2, 6.4, 5.4], font_size=10.5, align_center_cols=[0])
add_figure(doc, "fig_video.png", "图 2-3　视觉流水线三路径：显示直通、灰度分析与 224×224 快照")
p223b = (
    "视频流水线如图 2-3。in_align 把 dvi2rgb 的原始 vs/hs/de 归一化为帧首单拍、行尾单拍和像素有效；"
    "显示路径把原始 RGB 恒延迟 1 拍送到 rgb2dvi，分析开关、缩放和消费反压都不影响上屏；"
    "分析路径依次为 rgb2gray、gaussian_3x3、sobel 和 OSD，输出仅用于诊断；"
    "快照路径在 sobel 之后分叉，经 16.16 双线性 scaler 缩到 224×224，写入双 bank cop_buf，整帧原子回放给协处理器。"
    "配置经 axi_regs→config_bridge 跨时钟域，在帧首整组应用，避免半新半旧配置。"
)
add_body(doc, p223b)
p223c = (
    "CNN 协处理器如图 2-4。PS 经 AXI-Lite 写配置寄存器和邮箱，经 AXI DMA 把 36,032 B 模型载荷和 4,096 B ROI 送入 PL；"
    "协处理器域内，驻留固件等待 CFG_VALID、MODEL_VALID、DMA 完成和 ROI 数量匹配，随后置 START；"
    "128 个 INT8 MAC 按 8×16 阵列执行 Conv、GAP 和 FC，结果写入 16×16 B 结果窗口；PS 通过 AXI-Lite 读回 META、LOGITS、SCORE 和 RESULT_SEQ。"
    "模型存储采用双 bank 影子结构，新载荷写入非活动 bank，校验通过后原子切换。"
)
add_body(doc, p223c)
add_figure(doc, "fig_cop.png", "图 2-4　CNN 协处理器数据通路、寄存器与 DMA")
p223d = (
    "RISC-V 核如图 2-5。三级流水为 IF、ID+EX、MEM+WB；三路转发优先级为 EX>MEM>WB；load-use 固定停 1 拍；"
    "taken 分支冲刷 1 个年轻槽；64 项 BHT 支持关闭、1-bit 和 2-bit 三档；乘法器为 Radix-4，16 次迭代，除法为 Radix-2，32 次迭代。"
    "核通过 if_stage 和 mem_wb_stage 两个边界寄存器隔离组合逻辑，所有副作用以 valid 为前提。"
)
add_body(doc, p223d)
add_figure(doc, "fig_core.png", "图 2-5　RISC-V 三级流水、三路转发与 BHT")
p223e = (
    "PS 侧地址分配为：协处理器 AXI-Lite 0x4000_0000–0x4000_0FFF，DMA 0x4001_0000，dma_control 0x4002_0000；"
    "核内局部 MMIO 窗口 0x8001_0000。关键寄存器与地址分配见 2.3.2 节。"
)
add_body(doc, p223e)

add_h2(doc, "2.3 软件系统介绍")
add_h3(doc, "2.3.1 软件整体介绍")
p231 = (
    "软件分三层：网页端、PS 服务、CopDriver 与固件。网页端与服务之间只使用 HTTP/JSON；服务与硬件之间只使用 32 位 MMIO 和 DMA（实板 DMA 平面待接入）。"
    "CopDriver 对上层暴露同一组 read32/write32、DMA 和作业接口，底层可切换 PynqMmio（实板）或 CopSim（仿真），"
    "因此从模拟迁移到实板不需要重写服务和网页端。图 2-6 给出分层与一次检查的作业时序。"
)
add_body(doc, p231)
p231b = (
    "服务端接口为 GET /v1/status、GET /v1/latest、POST /v1/check、POST /v1/config。"
    "所有请求和响应使用严格字段校验，未知字段返回 400；报文上限 64 KiB，目标上限 16。"
)
add_body(doc, p231b)
add_table(doc, "表 2-3　服务端接口", ["方法", "路径", "作用"], [
    ["GET", "/v1/status", "模式、会话、硬件连接、引擎与 prototype 标志"],
    ["GET", "/v1/latest", "最近一次检查；首次请求返回 404"],
    ["POST", "/v1/check", "触发检查，可带 ≤64 字符的 trigger_ref"],
    ["POST", "/v1/config", "应用控制配置，返回 applied_config_id"],
], [2.0, 4.4, 8.6], font_size=10.5, align_center_cols=[0])
add_figure(doc, "fig_sw.png", "图 2-6　软件分层与一次检查的作业时序")

add_h3(doc, "2.3.2 软件各模块介绍")
p232a = (
    "（1）网页端。HTML 单文件实现（HUD v4「应用外壳」），零依赖、无构建步骤，支持亮暗主题与响应式布局。"
    "顶栏显示 LIVE/MOCK、PROTOTYPE、判定摘要、分辨率、帧率、会话和时钟；左侧提供 USB 采集卡选择与断开、自动轮询与年龄窗参数；"
    "右侧识别范围表按类别勾选并显示计数；RUN INSPECTION 按钮有 IDLE、QUEUED/WAITING、RUNNING 三态；"
    "下方为检测目标卡片、系统日志与本页批次记录（CSV EXPORT，UTF-8-BOM）。"
    "判定规则为：无 reason 且 actual==expected 时 CHECK_PASS；数量不一致为 CHECK_FAIL；出现 target_limit、低分、未知类别或触碰边界时 RECHECK。"
    "协议能力 16 个目标，业务策略 10 个；超过策略上限显示“未完整计数”，计数栏显示“--”，不把 0 当作实测。"
    "只有手动触发且有效的轮次写入记录；异常写入异常日志与截图。失败时立即撤下旧 PASS，显示 NO VALID RESULT；"
    "连续 3 次 HTTP 失败显示 SERVICE OFFLINE 并重新握手。数据源三形态互斥：LIVE（采集卡+板端服务）、LOCAL DEMO（合成数据联调）、FILE REPLAY（只读回放）；"
    "10-30 已在 LIVE 形态接入 USB 采集卡回传与板端服务并完成轮次联调。"
)
add_body(doc, p232a)
add_body_rich(doc, [
    ("（2）PS 服务。负责采集、定位裁剪、预处理与量化、作业提交、结果持久化和消费。定位采用背景对比度分割与外接框（联调版），"
     "预处理按 scene-gray-border-padding-v1 输出 64×64 灰度；量化在仿真后端使用 ", ""),
    ("S", "i"), ("in", "sub"), (" = 1/127", "i"),
    ("，实板后端必须从正式清单读取。服务对 trigger_ref 保留 16 条已完成轮次，重试复用同一 ref，不重复采集；会话变更会强制重新握手并丢弃旧结果。", ""),
    ("持久化采用 .pending 写入后 rename，先写 capture.png、capture.sha256、packet.json、cop_trace.json 和 ROI，再调用 CONSUME；"
     "任何一步失败都不消费，保留粘滞证据。round_artifacts.py 校验报文绑定、截图字节、像素哈希、判定一致性和 ROI 数量/哈希。", ""),
    ("10-27 新增 cop_product_service.py：C01 原帧捕获 + COP_HW 硬件引擎 + 前端消费，工单 2/4/4；真机已生成检查记录，"
     "10-30 起手动触发与 CSV 导出在网页端 LIVE 形态下联调通过（见 3.2.3 节）。", ""),
])
p232c = (
    "（3）CopDriver 与协议。作业顺序为：确认 BUSY=0 且 UNCONSUMED=0；写影子配置；CFG_SEQ 加 1 并写 CFG_COMMIT；"
    "等待 CFG_APPLIED==CFG_SEQ（2 s）；固件置 START；等待 ACCEPTED（1 s，超时为 NO_ACK）；等待终态（5 s，超时为 HW_TIMEOUT）；"
    "校验 DONE、RESULT_VALID 和 RESULT_SEQ==上次消费+1；读结果；落盘；最后 CONSUME。"
    "DONE/ERROR/TIMEOUT 互斥，优先级 TIMEOUT>ERROR>DONE；CONSUME 只清终态，不清 RESULT_SEQ；未消费时新作业返回 STALE_RESULT。"
    "ERROR_CODE 为 1 TASK_ERROR、12 ABORTED、13 WATCHDOG。"
)
add_body(doc, p232c)
p232d = (
    "（4）驻留固件。上电后进入等待循环，条件为 CFG_APPLIED≠0、CFG_VALID=1、MODEL_VALID=1、DMA_BUSY=0、ROI_COUNT≠0 且 DMA_BYTES==ROI_COUNT×4096。"
    "满足后写 START，等待 ACCEPTED，再等待终态；DONE 后校验 RESULT_VALID 和 RESULT_SEQ，读取 16 个索引结果，执行工单规则，写 FW_ACTUAL_COUNTS 和 FW_DECISION。"
    "轮询 guard 为 1,000,000 次，超时写 CONFIG 判定。当前固件一次上电只处理一个作业，重复作业需要 SOFT_RESET 或重新加载；这是后续要扩展的限制。"
)
add_body(doc, p232d)
add_body_rich(doc, [
    ("（5）CNN 模型与载荷。模型为 64×64×1 灰度三分类：4 个 3×3 卷积（1→16、16→32、32→32、32→64）、GAP、FC 64→3；"
     "折叠后 32,739 个 FP32 参数，单 ROI 11,944,128 MAC。量化采用对称 INT8：激活 per-tensor、权重 per-output-channel、零点 0、"
     "INT32 累加、int64 乘加移位 requant；", ""),
    ("score", "i"), ("q15", "sub"), (" 是归一化 logit margin，不是概率；", ""),
    ("margin", "i"), ("q", "sub"), (" 低于阈值时为低置信。", ""),
    ("清单 v1 为 PROVISIONAL，20 个张量、36,032 B，CRC32 0x2F760211，SHA256 14a199…；"
     "pattern 与 zero 两个诊断用例的期望输出分别为 class 0、margin 0、score 0，以及 class 2、margin 2、score 258。", ""),
])

add_h2(doc, "2.4 软硬件责任边界")
p24 = (
    "为避免“软件等硬件、硬件等软件”的互相等待，表 2-4 固定每个环节的责任方与交付物。"
    "定位、裁剪、量化与作业调度留在 PS，便于用 Python 快速迭代；卷积、GAP、FC 与结果窗口留在 PL，保证确定性时序；"
    "工单规则由驻留固件和 PS 双重执行，PS 只允许更严格、不允许更宽松；显示与记录由网页端负责，不参与实时控制。"
)
add_body(doc, p24)
add_table(doc, "表 2-4　软硬件责任边界", ["环节", "实现位置", "责任与交付物"], [
    ["采集 / 定位 / 裁剪", "PS（Python）", "取帧、背景分割、外接框、64×64 预处理"],
    ["量化 / 作业提交", "PS CopDriver", "量化、配置、DMA、看门狗、结果校验"],
    ["推理", "PL 协处理器 + 固件", "INT8 MAC、GAP/FC、START/ACCEPTED、工单判定"],
    ["视频显示", "PL + 采集卡 + 网页端", "彩色直通、框/标签叠加、freshness"],
    ["记录 / 追溯", "PS 服务 + 网页端", "packet/trace/截图/ROI、CSV、异常记录"],
], [4.0, 4.2, 6.2], font_size=9.5, align_center_cols=[0])
p24b = (
    "这条边界也是模拟迁移到实板的依据：CopDriver 只依赖 read32/write32 与 DMA 平面，CopSim 与 PynqMmio 实现同一接口；"
    "服务和网页端不感知底层是仿真还是实板，因此切换后端不需要改上层代码。"
)
add_body(doc, p24b)

# ================================================================== 第三部分
add_h1(doc, "第三部分　完成情况及性能参数")

add_h2(doc, "3.1 整体介绍")
p31 = (
    "实物由 PYNQ-Z2、树莓派 HDMI 相机、USB 采集卡和 Windows PC 组成。相机与板卡同装于亚克力支架，相机 HDMI 送入板卡，"
    "板卡 HDMI OUT 送入采集卡，采集卡 USB 接入 PC；板卡以太网与 PC 直连，用于结果报文。整机工位见图 3-1。"
)
add_body(doc, p31)
add_figure(doc, "photo_workstation.jpg", "图 3-1　系统整机工位：亚克力支架上的 PYNQ-Z2 与树莓派相机链路、网页端演示笔记本", width_cm=7.5)
p31b = (
    "板上已完成：直连 40.000000 MHz 包 20/20 首读 STATUS=0x1；MMCM 包输入 142.857143 MHz、协处理器域 40 MHz、10,000 次寄存器读取无错误；"
    "硬件 CNN zero/pattern/roi_001/frame 四例与黄金输出一致（PROVISIONAL）；共存位流 b2690b0a 同时输出 HDMI、抓取 BGR 原帧并运行硬件 CNN。"
    "10-30 网页端接入 USB 采集卡回传与板端服务，完成手动轮次触发、页面批次记录与 CSV 导出的联调（工单 3/3/3，判定 RECHECK）。"
    "多目标结果槽错位已在 RTL 修复并通过定向仿真，修复包未上板；正式 INT8 模型与识别精度未验收。"
)
add_body(doc, p31b)
add_table(doc, "表 3-1　完成度矩阵（√ 完成；△ 部分完成；— 未完成）", ["模块", "仿真 / 离板", "综合 / 时序", "上板", "软件"], [
    ["RISC-V 核", "√ 38 用例 + 44/44 arch + CoreMark", "√ 86.806 MHz", "√ 40 MHz，LED 1101", "—"],
    ["视觉链路", "√ 22 tb，Icarus/XSim", "√ WNS +0.330 ns", "√ 720p 直通 108 帧", "—"],
    ["CNN 协处理器", "√ 6/6 门禁；2×73,795 元素；多目标修复 tb", "√ 40 MHz WNS +2.498；共存 +1.184", "√ 单目标四例；△ 多目标修复未上板", "√ COP_HW / 前端记录"],
    ["前端 / 服务", "√ 全量回归 172；17+20 组", "—", "√ 真机 UVC/HTTP 记录；√ 手动/CSV LIVE 联调（10-30）", "√ 模拟闭环"],
], [3.0, 5.0, 3.4, 4.2, 2.4], font_size=9.0, align_center_cols=[0])

add_h2(doc, "3.2 工程成果")
add_h3(doc, "3.2.1 机械成果")
p321 = (
    "首版无定制机械件。相机支架、板卡铜柱、采集卡和 PC 均为现成件；桌面布置保证相机垂直向下、视场覆盖工作区。"
    "机械成果见图 3-1 中的亚克力支架与桌面布置，不重复配图。"
)
add_body(doc, p321)

add_h3(doc, "3.2.2 电路成果")
p322 = (
    "电路成果为 PYNQ-Z2 板级工程：HDMI 输入经 dvi2rgb 转并行 RGB，PL 完成视频/核/协处理器，rgb2dvi 输出 HDMI；"
    "PS 侧使用 DDR3、SD 卡、以太网和 USB。工程产出 bitstream 与 XSA，DRC 0；40 MHz 全系统门禁 WNS +2.498 ns，"
    "共存位流 b2690b0a 重新分析 WNS +1.184 ns、WHS +0.005 ns、8192 个 IMEM 字匹配。"
    "无自制 PCB 和原理图。板卡特写见图 3-2。"
)
add_body(doc, p322)
add_figure(doc, "photo_board_closeup.jpg", "图 3-2　PYNQ-Z2 板卡特写：HDMI 输入/输出、千兆以太网、USB 与亚克力支架接线", width_cm=8.5)

add_h3(doc, "3.2.3 软件成果")
p323 = (
    "软件成果包括网页端、PS 服务、CopDriver、固件和验证脚本。图 3-3 为网页端 LIVE 形态的实机界面（2026-10-30 联调）："
    "画面来自 USB 采集卡回传，目标框、范围表计数与判定来自板端服务轮次；当前工单 3/3/3、实际 4/2/0，"
    "判定 RECHECK（差额 +bolt×1 -nut×1 -washer×3，原因 low_score），低置信目标不进入通过结论。"
    "界面同时保留 LOCAL DEMO 与 FILE REPLAY 两种离线形态用于联调与回放。"
    "一次检查会生成 session.json、capture.png、capture.sha256、packet.json、cop_trace.json、ROI 和记录截图；页面内可一键导出 CSV。"
)
add_body(doc, p323)
add_figure(doc, "webui_live.png", "图 3-3　HTML 网页端 LIVE 界面：采集卡回传视频与板端轮次叠加（工单 3/3/3，判定 RECHECK）")

add_h2(doc, "3.3 特性成果")
p33a = (
    "表 3-2 为同一工作负载（CoreMark 2K/32）下的特性消融：v0 是追溯的两级基线，v1 各行依次单独叠加转发、Radix-4 乘法与 BHT，"
    "用于把性能提升拆解归因到具体机制，组合收益不能归因单一机制。各行 retired 相同（10,106,386，v0 为 10,106,387）、tohost=34713，对比同口径；"
    "转发使 CPI 下降 10.20%，Radix-4 相对无转发使周期数下降 21.95%，BHT2 相对仅转发再降 5.15%，CoreMark 命中率 91.18%。"
)
add_body(doc, p33a)
add_table(doc, "表 3-2　CoreMark 2K/32 四档消融", ["配置", "cycles", "retired", "CPI", "IPC", "CoreMark/MHz"], [
    ["v0 两级", "21,275,738", "10,106,387", "2.105177", "0.475", "1.506"],
    ["v1 无转发", "19,057,438", "10,106,386", "1.885683", "0.530", "1.681"],
    ["v1 转发", "17,114,141", "10,106,386", "1.693399", "0.591", "1.872"],
    ["v1 转发 + BHT1", "16,335,562", "10,106,386", "1.616360", "0.619", "1.961"],
    ["v1 转发 + BHT2", "16,232,079", "10,106,386", "1.606121", "0.623", "1.974"],
], [3.4, 3.0, 2.8, 2.2, 1.4, 2.6], font_size=9.0, align_center_cols=[0, 1, 2, 3, 4, 5])
p33a2 = (
    "以传统公开口径归纳：最终配置 IPC 0.623、CoreMark/MHz 1.974，均为业界标准指标，可直接与同类 RISC-V 软核的文献值横向比较；"
    "同板卡、同工具链下的第三方软核对照（如 PicoRV32）列入后续工作。CPI 1.606 距理想单发射顺序执行（CPI=1）尚有 0.606 拍，"
    "对应 load-use 停顿、分支冲刷与访存等待之和，即后续优化空间所在。"
)
add_body(doc, p33a2)
p33b = (
    "表 3-3 为时序与资源。核 OOC 在 11.52 ns 约束下 WNS +0.538 ns，对应 86.806 MHz；SoC 在 40 MHz 下 WNS +3.618 ns；"
    "video_pipeline 在 74.25 MHz 下 WNS +0.330 ns；协处理器控制器在 100 MHz 下 WNS +0.317 ns；"
    "40 MHz 全系统门禁 WNS +2.498 ns；共存位流 b2690b0a 重新分析 WNS +1.184 ns、WHS +0.005 ns。"
    "全系统 DSP 136/220、BRAM 69/140、DRC 0。"
)
add_body(doc, p33b)
add_table(doc, "表 3-3　时序与资源（Vivado 2026.1，xc7z020clg400-1）", ["设计", "约束", "WNS", "LUT / FF", "BRAM / DSP"], [
    ["核 OOC（bht2）", "11.52 ns", "+0.538 ns", "2443 / 637", "0 / 0"],
    ["SoC（bht2）", "25 ns（40 MHz）", "+3.618 ns", "6768 / 859", "8 / 0"],
    ["video_pipeline", "13.468 ns（74.25 MHz）", "+0.330 ns", "1985 / 1515", "38 / 0"],
    ["协处理器控制器 OOC", "10 ns（100 MHz）", "+0.317 ns", "4540 / 4037", "— / 136"],
    ["全系统（门禁）", "25 ns（40 MHz）", "+2.498 ns", "—", "69 / 136"],
    ["共存位流 b2690b0a", "25 ns（40 MHz）", "+1.184 ns", "—", "69 / 136"],
], [4.6, 4.4, 2.8, 2.8, 2.4], font_size=9.5, align_center_cols=[0, 1, 2, 3, 4])
p33c = (
    "表 3-4 为软件验证。2026-10-24 Icarus 全量回归 172 条 PASS、9 条预期门禁失败、0 条意外失败；"
    "2026-10-21 Python 19 个检查组和 21 个视觉组退出 0；2026-10-11 XSim 25 个视觉 tb、2 个采集 tb 和 axi_lock 退出 0；"
    "2026-10-21 服务+前端模拟轮次 CHECK_PASS 1/1/1、3 目标/3 ROI、1 条记录；异常矩阵覆盖 4 轮服务和 9 个引擎场景；"
    "2026-10-17 板上 PS 原型 2 轮，16 目标，RECHECK，prototype=true。"
)
add_body(doc, p33c)
add_table(doc, "表 3-4　软件与服务验证", ["项目", "结果"], [
    ["Icarus 全量回归（2026-10-24）", "172 PASS；9 条预期门禁失败；0 意外"],
    ["Python 分组（2026-10-21）", "19 检查 + 21 视觉；退出 0"],
    ["XSim（2026-10-11）", "25 视觉 tb + 2 采集 + 1 axi_lock；退出 0"],
    ["服务 + 前端模拟轮次（2026-10-21）", "CHECK_PASS 1/1/1；3 目标/3 ROI；1 条记录"],
    ["异常矩阵", "4 轮服务异常 + 9 个引擎场景"],
    ["板上 PS 原型（2026-10-17）", "2 轮；16 目标；RECHECK；prototype=true"],
], [6.4, 8.6], font_size=10.0)
p33d = (
    "表 3-5 为板上 bring-up 时间线：从 10-25 的 NO_ACK（定位为 IMEM 初值缺失）及其修复，"
    "到 10-26/27 的四例黄金对拍与共存位流联调；多目标旧包暴露结果槽错位，修复版仅通过定向仿真，未上板。"
)
add_body(doc, p33d)
add_table(doc, "表 3-5　板上 bring-up 结果", ["日期", "时钟", "结果"], [
    ["2026-10-25", "40.000000 MHz", "20/20 STATUS=0x1；DMA 通过；NO_ACK，定位为 IMEM 初值缺失"],
    ["2026-10-26", "40.000000 MHz", "zero/pattern 各 3 轮全匹配；STATUS=0x61；RESULT_SEQ=1；无 UNCONSUMED"],
    ["2026-10-27", "40 MHz（MMCM 输入 142.857）", "四例黄金全匹配、10,000 次寄存器读取无错误；共存位流另完成 roi_001 黄金、HDMI+原帧+CNN 与真机检查记录"],
    ["2026-10-27", "—", "多目标槽错位修复仅定向仿真 PASS，修复包未上板"],
], [2.6, 4.4, 8.0], font_size=9.0, align_center_cols=[0])
p33e = (
    "结果讨论：四档数据分别对应转发、Radix-4 与 BHT 的作用，组合收益不能归因给单一机制；核与视觉链 DSP 为 0，"
    "协处理器仍有 84 DSP、71 BRAM 余量。共存实测又发现旧包第 0 结果槽为空、后续槽等于前一个 ROI 的输出；"
    "原因是 result_write 寄存后槽号同拍提前递增。增加 COMMIT_RESULT 一拍保持槽号到写入完成，三目标用例旧版 FAIL、新版 PASS；"
    "修复包尚未上板，因此多目标识别不作验收结论。"
)
add_body(doc, p33e)
p33f = (
    "复现入口见表 3-6。验收边界：单目标四例是 PROVISIONAL 黄金对拍，不是识别精度；多目标修复包未上板；"
    "板卡 SD/mmc 历史故障未复现，长时/温度稳定性未测；正式 INT8 模型与整机验收仍未完成。"
)
add_body(doc, p33f, align=WD_ALIGN_PARAGRAPH.LEFT)
add_table(doc, "表 3-6　复现入口", ["入口", "命令"], [
    ["RTL 全量回归", "bash sim/scripts/run_iverilog.sh all"],
    ["视觉 XSim 全量", "bash sim/scripts/run_vision_xsim.sh all"],
    ["协处理器板上对拍", "py sim/scripts/cop_board_fast_run.py --package <包> --case <zero|pattern|roi_001|frame>"],
    ["批次记录导出", "py src/pynq_host/export_records.py <记录目录>（或网页端 CSV EXPORT）"],
], [3.6, 11.4], font_size=9.5, mono_cols=[1])


# ================================================================== 第四部分
add_h1(doc, "第四部分　总结")

add_h2(doc, "4.1 可扩展之处")
p41 = (
    "后续可扩展五个方向：一，正式 PTQ/QAT 模型与真实数据精度报告，替换 PROVISIONAL 诊断载荷；"
    "二，多目标修复包上板与逐目标定位，覆盖阴影/反光造成的分裂与合并；三，全帧 DDR/结果 DMA 与连续作业，打通完整帧关联；"
    "四，100/125 MHz 频率提升与长时/温度稳定性测试；五，外壳、光学与产线接口，形成可交付的整机。"
)
section_count("4.1 可扩展之处", [p41])
add_body(doc, p41)

add_h2(doc, "4.2 心得体会")
heart = (
    "回头看这个项目，最值钱的不是某一块模块，而是几次被逼出来的工作方式。"
    "最先撞墙的是接口。三个人的模块各自都能跑，一联调就对不上：寄存器偏移、报文字段、时序边界全靠口头约定，返工两次之后我们才学会把契约写成版本化文档。"
    "RESULT_SEQ 和 CONSUME 这对语义，就是被重复请求和陈旧结果两次事故逼出来的——先把失败路径定义清楚，正常路径反而简单了。"
    "第二个教训来自板上。协处理器在离板门禁里全绿，上了板 ACCEPTED 却迟迟不来；查了两天，最后靠 ROI_COUNT 的活性序列确认 CPU 根本没有执行固件，再一路追到 IMEM 的 readmemh 相对路径在综合时没有命中。"
    "修完这一处，四例黄金对拍全过；共存实测又冒出多目标结果槽错位——“跑通一例”和“整链可信”之间，隔着的就是这类只在真实数据下才暴露的缺陷。"
    "第三是解耦带来的省心。显示、分析、快照三条路径分开之后，彩色原图恒一拍上屏，分析侧怎么折腾都不伤画质；不少当时显得“绕”的设计，后来都省了返工。"
    "AI 在项目里参与很深：写代码、查资料、出测试、陪排查。我们的规矩是每段入库代码都要能讲清意图、每个“已验证”都要有仓库内脚本和原始日志——AI 负责提速，签字的责任始终在人，具体做法和沉淀见 4.3 节。"
    "剩下的是人的部分：三线并行、每周 PR、交叉复验，谁卡住了其他人能接手；板上 IMEM 这个跨层缺陷，最后就是软件、RTL 和验证三方一起挖出来的。"
)
section_count("4.2 心得体会", [heart])
add_body(doc, heart)

add_h2(doc, "4.3 大语言模型协作记录与 Skills 沉淀")
p43a = (
    "本项目全程与大语言模型协作开发，协作过程完整留痕：仓库 report/llm_log/ 累计 220 条记录，覆盖需求拆解、RTL 与验证、"
    "板上抢救、前端迭代与材料整理；每条包含任务目标、prompt 要点、产出与人工复核结论，commit message 同步注明 AI 参与要点。"
    "三条纪律贯穿全程：一是理解门槛——AI 产出的代码入库前必须由使用者讲清设计意图，讲不清就不合入；"
    "二是证据门禁——任何“已验证”都必须有仓库内脚本与原始日志支撑，AI 的口头结论不计数；"
    "三是小步交付——单步改动控制在可审阅规模，先讲解再前进，避免大块不可审阅的产出。"
)
add_body(doc, p43a)
p43b = (
    "在反复踩坑之后，我们把可复用的流程沉淀为 9 个技能包（表 4-1），覆盖编码、契约、时序、板级排障与数据集审计等环节；"
    "它们既约束 AI 的行为边界，也让新成员能够按同样的流程接手对应工作。"
)
add_body(doc, p43b)
add_table(doc, "表 4-1　Skills 沉淀清单", ["技能包", "用途"], [
    ["gufa-programming", "古法编程：小步交付（单步 ≤100 行）、先设计后写码、逐段讲解与理解题"],
    ["understand-gate", "理解门槛：AI 代码入库前必须通过使用者的逐段讲解检查"],
    ["contract-freeze-workflow", "契约冻结：寄存器/报文 schema 编码空间核对、负例校验、缺口只登记不放宽"],
    ["timing-closure-workflow", "时序收敛：WNS/Fmax 口径统一、降深度改写、等价回归"],
    ["sim-board-consistency", "仿真-上板一致性：唯一退休点口径、跨工具对拍、中断回归不拼接"],
    ["pynq-z2-bringup", "PYNQ-Z2 板级排障：JTAG、引脚约束、MMCM 时钟、位流下载"],
    ["big-rewrite-playbook", "大规模重做：性价比子集、冻结后重写、可复现产物评审"],
    ["bug-fix-playbook", "缺陷修复：功能坏/反馈坏区分、弱测试巡检、负例先行、修复必证明"],
    ["dataset-leak-audit", "数据集防泄漏审计：会话级划分、文件字节与解码像素双哈希"],
], [4.4, 10.0], font_size=9.5, mono_cols=[0])
p43c = (
    "效果与边界：技能包把个人经验变成可复用流程——板上 IMEM 缺陷、多目标槽错位等问题的定位路径都已回写成检查项；"
    "但 skills 不改变责任归属，方向、取舍与验收始终由团队成员负责。"
)
add_body(doc, p43c)
section_count("4.3 大语言模型协作记录与 Skills 沉淀", [p43a, p43b, p43c])

# ================================================================== 第五部分
add_h1(doc, "第五部分　参考文献")
refs = [
    "RISC-V International. The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA, Version 20191213.",
    "RISC-V International. The RISC-V Instruction Set Manual, Volume II: Privileged Architecture, Version 20211203.",
    "EEMBC. CoreMark: An Industry-Standard Benchmark for Embedded Processors. https://www.eembc.org/coremark/",
    "Xilinx. Zynq-7000 SoC Technical Reference Manual, UG585.",
    "Digilent. PYNQ-Z2 Reference Manual.",
    "ARM. AMBA AXI and ACE Protocol Specification, ARM IHI 0022.",
    "Umuroglu Y., Fraser N. J., Gambardella G., et al. FINN: A Framework for Fast, Scalable Binarized Neural Network Inference. FPGA 2017.",
    "Xilinx Research Labs. Brevitas: Quantization-aware Training for Neural Networks. https://github.com/Xilinx/brevitas",
    "Jacob B., Kligys S., Chen B., et al. Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference. CVPR 2018.",
    "RISC-V International. riscv-arch-test: RISC-V Architecture Test Suite. https://github.com/riscv-non-isa/riscv-arch-test",
    "YosysHQ. PicoRV32: A Size-Optimized RISC-V CPU. https://github.com/YosysHQ/picorv32",
    "PYNQ. Python Productivity for Zynq. https://www.pynq.io/",
    "Xilinx. Vivado Design Suite User Guide: Synthesis, UG901.",
    "Xilinx. Vivado Design Suite User Guide: Implementation, UG904.",
    "Patterson D. A., Hennessy J. L. Computer Organization and Design: The Hardware/Software Interface, RISC-V Edition. Morgan Kaufmann, 2017.",
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = None
    pf.left_indent = Cm(0.74)
    pf.first_line_indent = Cm(-0.74)
    pf.line_spacing = 1.25
    pf.space_after = Pt(3)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(f"[{i}] {ref}")
    set_run_font(r, size=10.5)

# 文档属性与保存
doc.save(OUT)
print("written:", OUT)
print("figures:", sorted(os.listdir(FIG)))
