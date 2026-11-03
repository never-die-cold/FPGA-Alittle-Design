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
    _emit_rich(p, rich_segs(text), size, bold=bold, color=color)
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
    mono=等宽；普通段再过一遍标识符扫描，保证公式字符全文口径一致。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(size * 2) if indent else None
    pf.line_spacing = 1.3
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for text, fmt in segs:
        tokens = (fmt or "").split()
        if "mono" in tokens:
            _emit_rich(p, [(text, "mono")], size)
            continue
        for t2, f2 in rich_segs(text):
            merged = " ".join(x for x in (fmt or "", "mono" if f2 == "mono" else "") if x)
            _emit_rich(p, [(t2, merged)], size)
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
            if mono_cols and i in mono_cols:
                _emit_rich(p, [(str(val), "mono")], font_size)
            else:
                _emit_rich(p, rich_segs(str(val)), font_size)
    # 小表（≤6 行）保持整块；大表允许跨页，表头会随页重复，避免留下半页空白
    if len(table.rows) <= 6:
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


# ------------------------------------------------------------------ 标识符排版
# 全文统一口径：snake_case 标识符、寄存器/协议 UPPER_SNAKE 名、文件名与指定
# 协议常量一律等宽字体（Consolas），等效 LaTeX \texttt{}；正文其余部分不改动。
MONO_PAT = re.compile(
    r"(\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b"                                  # snake_case
    r"|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b"                                  # UPPER_SNAKE
    r"|\b[a-z][a-z0-9]*_\*"                                                # display_* / cop_*
    r"|\b\w[\w\-]*\.(?:py|json|jsonl|png|sha256|md|sh|bat|csv|v|tcl)(?![A-Za-z0-9])"  # 文件名
    r"|\b(?:STATUS|START|ACCEPTED|UNCONSUMED|CONSUME|BUSY|DONE|ERROR_CODE"
    r"|WATCHDOG|HW_TIMEOUT|NO_ACK|STALE_RESULT|TASK_ERROR|ABORTED)\b"
    r"|scene-gray-border-padding-v1|\.pending|readmemh)")


def rich_segs(text):
    """把字符串切成 [(text, fmt)] 段；命中的标识符段标 mono，其余为普通段。"""
    segs, pos = [], 0
    for m in MONO_PAT.finditer(text):
        if m.start() > pos:
            segs.append((text[pos:m.start()], ""))
        segs.append((m.group(0), "mono"))
        pos = m.end()
    if pos < len(text) or not segs:
        segs.append((text[pos:], ""))
    return segs


def _emit_rich(p, segs, size, bold=False, color=BLACK):
    for text, fmt in segs:
        tokens = (fmt or "").split()
        r = p.add_run(text)
        if "mono" in tokens:
            set_run_font(r, ascii_font="Consolas", east=SONG,
                         size=size - 1, bold=bold, color=color)
        else:
            set_run_font(r, size=size, bold=bold, color=color,
                         italic="i" in tokens)
        if "sub" in tokens:
            r.font.subscript = True
        if "sup" in tokens:
            r.font.superscript = True


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
    "针对多品种、小批量装配工位对紧固件种类与数量复核的需求，本作品在 PYNQ-Z2 上实现了一套桌面紧固件识别与工业检查系统。"
    "四条链路均自主设计：三级流水 RISC-V 核负责调度与工单判定，视觉流水线完成 720p60 采集与显示、分析、快照三路分流，"
    "128 乘加单元的 INT8 CNN 协处理器完成逐目标分类，板端服务与 HTML 网页端负责工单比较、批次记录与展示。"
    "核通过 44/44 组体系结构测试，CPI 1.606、每兆赫 1.974 个 CoreMark，布线后时序 86.806 MHz；"
    "视觉链路 22 个测试平台通过并上板 720p 直通；协处理器板上四例黄金对照一致；"
    "网页端已接入真实采集卡与板端服务，完成工单下发、手动检查与 CSV 导出。"
    "多目标修复包尚未上板，正式模型与整机验收未完成。"
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
    "系统提供五项功能。一是自由摆放识别：零件无需夹具，视觉定位给出外接框，CNN 将每个目标分类为螺栓、螺母或垫圈。"
    "二是工单检查：在网页端填写三类期望数量（合计 1–10 件），板端确认后生效，检查时输出缺件、多余件、错料及数量。"
    "三是同屏呈现：彩色原图经采集卡进入网页端，叠加目标框、类别与置信度。"
    "四是批次记录：每次手动检查生成一条记录，保存截图与结果，可导出 CSV。"
    "五是异常防护：超时、陈旧结果、运行失败与断联都进入明确错误态，不显示为检查通过。"
)
section_count("1.1 功能与特性", [p11])
add_body(doc, p11)

add_h2(doc, "1.2 应用领域")
p12 = (
    "适用于 3C 与家电装配工位的小件复核、多品种小批量换线后的首件确认、包装计数与来料抽检等场景。"
    "首版支持自由分散且互不遮挡的紧固件，要求受控光照与稳定背景；堆叠、接触遮挡、裂纹与尺寸超差检测不在首版范围。"
    "系统以桌面级成本完成本地推理，结果不出厂区，适合对数据隐私与实时性有要求的产线边缘部署。"
)
section_count("1.2 应用领域", [p12])
add_body(doc, p12)

add_h2(doc, "1.3 主要技术特点")
p13 = (
    "（1）全栈自研：除 Xilinx 的 HDMI 收发 IP 外，处理器核、视觉流水线、CNN 协处理器、固件、板端服务与网页端均由团队实现。"
    "（2）显示与分析解耦：彩色原图恒定一拍直通显示，分析与快照独立推进，不影响上屏。"
    "（3）全整数推理：INT8 权重与激活、INT32 累加、移位重新量化，模型双缓冲、校验后原子切换。"
    "（4）结果一次性消费：结果先落盘再消费，重复或过期结果不进入判定。"
    "（5）证据驱动：每个结论都有可复现的测试与原始记录。"
)
section_count("1.3 主要技术特点", [p13])
add_body(doc, p13)

add_h2(doc, "1.4 主要性能指标")
add_body(doc, "主要指标如表 1-1 所示；仿真、综合与板上结果分别标注。", indent=True)
add_table(doc, "表 1-1　主要性能指标", ["项目", "结果"], [
    ["处理器核 ISA / 流水", "RV32IM；三级；转发；64 项 BHT"],
    ["CoreMark 2K/32", "CPI 1.606；CoreMark/MHz 1.974"],
    ["核布线后时序", "86.806 MHz；WNS +0.538 ns"],
    ["视觉链路", "1280×720@60；74.25 MHz；WNS +0.330 ns"],
    ["协处理器", "128 MAC；36,032 B；11.94M MAC/ROI"],
    ["协处理器全系统", "40 MHz；WNS +2.498 ns；DSP 136/220；BRAM 69/140"],
    ["软件接口", "HTTP/JSON；≤16 目标；≤64 KiB"],
    ["板上验证", "40 MHz 时钟门禁通过；四例黄金对照一致"],
], [5.2, 9.2], font_size=9.5)

add_h2(doc, "1.5 主要创新点")
p15 = (
    "① 自研三级核把转发、可切换分支预测与快速乘法放在同一基线做四档对比，量化到 CPI 1.606。"
    "② 显示、分析、快照三路解耦与整帧原子快照，上屏画质不受分析负载影响。"
    "③ 结果一次性消费，把重复与过期结果挡在判定之外。"
    "④ INT8 全整数通路配双缓冲模型与原子切换。"
    "⑤ 证据分级：仿真、软件、板上分别留痕，不以低级别证据替代板上结论。"
)
section_count("1.5 主要创新点", [p15])
add_body(doc, p15)

add_h2(doc, "1.6 设计流程")
p16 = (
    "流程分为六步：需求与验收口径、接口约定、RTL 与模块测试、全量回归、综合与时序、板上联调与归档。"
    "每一步以门禁收口：回归零意外失败，时序满足约束，板上有关键回读，软件有可重放的检查轮次。"
    "仿真、软件与板上证据分别标注，结论不跨级替代。"
)
section_count("1.6 设计流程", [p16])
add_body(doc, p16)

# ================================================================== 第二部分
add_h1(doc, "第二部分　系统组成及功能说明")

add_h2(doc, "2.1 整体介绍")
add_figure(doc, "fig_system.png", "图 2-1　系统总体架构与数据路径")
p21 = (
    "系统由 HDMI 相机、PYNQ-Z2 板卡、USB 采集卡与 PC 组成（图 2-1）。相机输出 1280×720@60 彩色图像进入 PL；"
    "视觉流水线把彩色原图直通输出到 HDMI，同时产生分析与快照数据；CNN 协处理器完成逐目标分类，"
    "RISC-V 核运行固件执行调度与工单判定；板端服务把检查结果经网络送到网页端，网页端负责展示、交互与记录。"
)
add_body(doc, p21)
p21b = (
    "数据分三路：视频经板卡 HDMI 输出、采集卡进入网页端，不经过分析链路；结果从板端服务经网络送到网页端；"
    "控制从网页端下发到板端，包括工单与检查触发。网页端只接受与当前会话、配置一致且在有效期内的结果。"
)
add_body(doc, p21b)
p21c = (
    "当前进展：视频链路、处理器核与硬件 CNN 单目标推理已在板上验证；网页端已接入真实采集卡与板端服务。"
    "多目标修复包尚未上板，正式模型、识别精度与整机验收仍未完成。"
)
add_body(doc, p21c)
section_count("2.1 整体介绍", [p21, p21b, p21c])

add_h2(doc, "2.2 硬件系统介绍")
add_h3(doc, "2.2.1 硬件整体介绍")
p221 = (
    "硬件采用 PYNQ-Z2 开发板，主器件为 XC7Z020-1CLG400C：PL 含 53,200 个逻辑单元、140 个 Block RAM 和 220 个 DSP；"
    "PS 为双核 ARM Cortex-A9，配 512 MB DDR3。板卡提供 HDMI 输入/输出、千兆以太网与 USB。"
    "视频源由树莓派及其摄像头模组提供 1280×720@60 图像，与板卡同装于亚克力支架（图 2-2）；采集卡把 HDMI 输出转为 USB 视频送入 PC。"
)
add_body(doc, p221)
p221b = (
    "时序分三个时钟域：PS 侧 100 MHz 供总线与外设，40 MHz 供处理器核与协处理器，HDMI 像素时钟 74.25 MHz；"
    "复位采用异步置位、同步释放，跨域信号与数据传输分别做同步和异步缓冲。"
)
add_body(doc, p221b)
add_table(doc, "表 2-1　硬件组成", ["模块", "型号 / 规格", "作用"], [
    ["FPGA 板卡", "PYNQ-Z2；XC7Z020-1CLG400C", "PL + PS、DDR3、HDMI、以太网"],
    ["HDMI 相机", "1280×720@60", "采集桌面工件图像"],
    ["USB 采集卡", "HDMI→UVC", "把板卡 HDMI OUT 送入 PC 网页端"],
    ["PC", "Windows 10/11", "网页端、记录与导出"],
    ["时钟", "FCLK0 100 MHz / FCLK1 40 MHz / pclk 74.25 MHz", "AXI / 协处理器 / 像素"],
], [3.2, 6.6, 5.2], font_size=10.5, align_center_cols=[0])
add_figure(doc, "photo_board_pi2.jpg", "图 2-2　硬件实物：PYNQ-Z2 与提供 HDMI 视频源的树莓派摄像头模组（同装于亚克力支架）", width_cm=9.5)

add_h3(doc, "2.2.2 机械设计介绍")
p222 = (
    "本项目不设计机械结构。首版采用现成亚克力支架、板卡铜柱和桌面布置：摄像头模组固定在工作区正上方，"
    "光轴垂直桌面、视场覆盖 A4 幅面（图 2-3）。机械自由度由支架的俯仰与高度调节提供，不涉及定制加工件；"
    "视频源与板卡同装于支架，缩短 HDMI 走线。整机布置照片见第三部分图 3-1。"
)
add_body(doc, p222)
add_figure(doc, "photo_camera.jpg", "图 2-3　摄像头安装：树莓派摄像头模组（CSI 排线连接）固定于工作区正上方，向下拍摄台面", width_cm=11.5)

add_h3(doc, "2.2.3 电路各模块介绍")
p223 = (
    "本项目不设计自制 PCB，电路成果体现为 PYNQ-Z2 板级集成、HDMI 输入/输出链路、时钟与复位设计，以及可综合的 PL 工程。"
    "板级电路模块如表 2-2 所示。"
)
add_body(doc, p223)
add_table(doc, "表 2-2　板级电路模块", ["模块", "实现", "作用"], [
    ["HDMI 输入", "Xilinx 接收 IP", "TMDS 转为并行像素与时序信号"],
    ["PL 逻辑", "视频流水线 / RISC-V 核 / CNN 协处理器", "图像处理、推理与判定"],
    ["HDMI 输出", "Xilinx 发送 IP", "并行像素转回 TMDS"],
    ["PS 外设", "DDR3、SD、以太网、USB", "内存、存储与网络"],
    ["时钟与复位", "PS 时钟、MMCM、复位同步", "100 / 40 / 74.25 MHz，异步置位同步释放"],
], [3.2, 6.4, 5.4], font_size=10.5, align_center_cols=[0])
add_figure(doc, "fig_video.png", "图 2-4　视觉流水线三路径：显示直通、灰度分析与 224×224 快照")
p223b = (
    "视频流水线如图 2-4。输入时序先对齐为帧首、行首与像素有效；显示路径把彩色原图延迟一拍直送 HDMI，"
    "分析开关、缩放与反压都不影响上屏；分析路径依次做灰度、平滑与边缘增强，仅作诊断；"
    "快照路径把整帧缩放到 224×224，整帧写入双缓冲后回放给协处理器，避免半帧。"
    "配置在帧首整组生效，不会出现半新半旧。"
)
add_body(doc, p223b)
p223c = (
    "CNN 协处理器如图 2-5。板端把模型与单目标 ROI 经 DMA 送入，协处理器在配置、模型与数据都就绪后启动，"
    "128 个 INT8 乘加单元按阵列执行卷积、全局平均池化与全连接，结果写入结果窗口供板端读回；"
    "模型采用双缓冲，新载荷校验通过后原子切换。"
)
add_body(doc, p223c)
add_figure(doc, "fig_cop.png", "图 2-5　CNN 协处理器数据通路、寄存器与 DMA")
p223d = (
    "RISC-V 核如图 2-6。三级流水为取指、执行与访存回写；三路转发优先取最新结果，load-use 停一拍；"
    "分支命中时冲刷一个年轻槽，64 项分支历史表可关闭或切换 1 位、2 位两种模式；乘法用 Radix-4、除法用 Radix-2 迭代实现。"
)
add_body(doc, p223d)
add_figure(doc, "fig_core.png", "图 2-6　RISC-V 三级流水、三路转发与 BHT")

add_h2(doc, "2.3 软件系统介绍")
add_h3(doc, "2.3.1 软件整体介绍")
p231 = (
    "软件分三层：网页端、板端服务、驱动与固件。网页端与服务之间用 HTTP/JSON；服务与硬件之间用寄存器访问与 DMA。"
    "驱动层对上层提供统一接口，可在仿真与实板之间切换，迁移时不需要改上层。图 2-7 给出分层与一次检查的时序。"
)
add_body(doc, p231)
p231b = (
    "服务端提供状态查询、结果读取、检查触发与配置下发四类接口；报文严格校验，未知字段返回 400，报文上限 64 KiB、目标上限 16。"
)
add_body(doc, p231b)
add_table(doc, "表 2-3　服务端接口", ["方法", "路径", "作用"], [
    ["GET", "/v1/status", "服务模式、会话、当前工单与运行状态"],
    ["GET", "/v1/latest", "最近一次检查结果；首次请求返回 404"],
    ["POST", "/v1/check", "触发一轮检查；未设置工单时拒绝"],
    ["POST", "/v1/config", "下发工单与控制配置，返回确认后的配置号与工单"],
], [2.0, 4.4, 8.6], font_size=10.5, align_center_cols=[0])
add_figure(doc, "fig_sw.png", "图 2-7　软件分层与一次检查的作业时序")

add_h3(doc, "2.3.2 软件各模块介绍")
p232a = (
    "（1）网页端。HTML/JavaScript 界面，经本机服务访问板端，页面不直接接触硬件。"
    "界面分三栏：左栏为服务状态、检查工单、采集卡与数据源，中栏为视频与系统日志，右栏为识别范围表、检测对象与服务信息。"
    "工单在页面内填写三类数量（合计 1–10 件），下发并经板端确认后生效，未应用时不能开始检查。"
    "判定分三档：数量与工单一致且无异常为通过，数量不符为失败，出现计数上限、低置信、未知类别或边界目标时判为复检。"
    "结果按接收时刻计时，4.5 秒后自动撤框；断联、配置变化或非法报文同样撤框。"
    "手动检查成功才计入批次；记录可一键导出，Excel 可直接打开。数据源有实时、本地演示与离线回放三种，本地演示为合成场景并明确标注。"
)
add_body(doc, p232a)
p232b = (
    "（2）板端服务。负责取帧、定位裁剪、预处理与量化、提交推理、读取并落盘结果。"
    "定位采用背景对比分割与外接框，裁剪后缩放到 64×64 灰度；量化参数由正式模型清单给出。"
    "重试不重复取帧；失败轮次不标记为已消费，保留现场供排查。"
)
add_body(doc, p232b)
p232c = (
    "（3）驱动与协议。作业顺序为：确认空闲、写配置并等待生效、启动、等待结束、校验结果序号、读取结果、落盘、标记已消费。"
    "超时与错误分级返回，未消费时拒绝新作业。DMA 模式下提交前先让旧模型失效，再装载新数据。"
)
add_body(doc, p232c)
p232d = (
    "（4）驻留固件。上电后等待配置、模型、数据与目标数量就绪后启动推理；结束后校验并读出各目标，"
    "执行工单判定并写回计数与结论。当前一次上电只处理一个作业。"
)
add_body(doc, p232d)
p232e = (
    "（5）模型与量化。64×64 灰度三分类，四层 3×3 卷积接全局平均池化与全连接，折叠后 32,739 个参数。"
    "采用对称 INT8 量化与 INT32 累加；输出分数是归一化的类别间隔而非概率，低于阈值即判为低置信。"
)
add_body(doc, p232e)

add_h2(doc, "2.4 软硬件责任边界")
p24 = (
    "为避免“软件等硬件、硬件等软件”的互相等待，表 2-4 固定每个环节的责任方与交付物。"
    "定位、裁剪、量化与作业调度留在 PS，便于用 Python 快速迭代；卷积、GAP、FC 与结果窗口留在 PL，保证确定性时序；"
    "工单规则由驻留固件和 PS 双重执行，PS 只允许更严格、不允许更宽松；显示与记录由网页端负责，不参与实时控制。"
)
add_body(doc, p24)
add_table(doc, "表 2-4　软硬件责任边界", ["环节", "实现位置", "责任与交付物"], [
    ["工单 / 配置", "网页端 → 板端服务", "填写、下发、板端确认后生效"],
    ["采集 / 定位 / 裁剪", "板端 PS", "取帧、分割、外接框、64×64 预处理"],
    ["量化 / 作业提交", "板端驱动", "量化、配置、数据传输、超时保护、结果校验"],
    ["推理", "PL 协处理器 + 固件", "INT8 乘加、池化与全连接、工单判定"],
    ["视频显示", "PL + 采集卡 + 网页端", "彩色直通、框与标签叠加"],
    ["记录 / 追溯", "板端服务 + 网页端", "截图与结果留档、CSV、异常记录"],
], [4.0, 4.2, 6.2], font_size=9.5, align_center_cols=[0])
# 去掉表后空段，避免与下一章的强制分页产生空白页
_last = doc.paragraphs[-1]
if not _last.text.strip():
    _last._element.getparent().remove(_last._element)

# ================================================================== 第三部分
add_h1(doc, "第三部分　完成情况及性能参数")

add_h2(doc, "3.1 整体介绍")
p31 = (
    "实物由 PYNQ-Z2、树莓派 HDMI 相机、USB 采集卡和 Windows PC 组成。相机与板卡同装于亚克力支架，相机 HDMI 送入板卡，"
    "板卡 HDMI OUT 送入采集卡，采集卡 USB 接入 PC；板卡以太网与 PC 直连，用于结果报文。整机工位见图 3-1（实验室布置）。"
)
add_body(doc, p31)
add_figure(doc, "photo_workstation2.jpg", "图 3-1　系统整机工位：亚克力支架上的 PYNQ-Z2 与树莓派相机链路、网页端演示笔记本", width_cm=13.2)
p31b = (
    "板上已完成：40 MHz 时钟门禁通过，寄存器连续读取无错误；硬件 CNN 四例与黄金输出一致；"
    "共存位流可同时输出 HDMI、抓取原帧并运行硬件 CNN。网页端自 10-30 起接入采集卡与板端服务，"
    "11-03 复测完成工单下发、手动轮次、批次记录与 CSV 导出。连续多轮稳定性尚未验收"
    "（第 5 轮出现任务错误与数据传输超时，根因未定位）；多目标修复包未上板，正式模型与识别精度未验收。"
)
add_body(doc, p31b)
add_table(doc, "表 3-1　完成度矩阵（√ 完成；△ 部分完成；— 未完成）", ["模块", "仿真 / 离板", "综合 / 时序", "上板", "软件"], [
    ["RISC-V 核", "√ 38 用例 + 44/44 体系结构测试 + CoreMark", "√ 86.806 MHz", "√ 40 MHz 运行", "—"],
    ["视觉链路", "√ 22 个测试平台，双仿真器", "√ WNS +0.330 ns", "√ 720p 直通上板", "—"],
    ["CNN 协处理器", "√ 门禁与定点参考测试", "√ 40 MHz WNS +2.498", "√ 单目标四例；△ 多目标未上板", "√ 硬件推理与记录"],
    ["前端 / 服务", "√ 全量回归与分组测试", "—", "√ 真机联调（11-03）；△ 连续多轮稳定性", "√ 联调闭环"],
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
    "电路成果为 PYNQ-Z2 板级工程：HDMI 输入转为并行像素，PL 完成视频、处理器核与协处理器，再输出 HDMI；"
    "PS 侧使用 DDR3、SD 卡、以太网与 USB。工程产出位流与硬件描述文件，设计规则检查无错误；"
    "40 MHz 全系统时序余量 2.498 ns，共存位流余量 1.184 ns。板卡与接线见图 3-2。"
)
add_body(doc, p322)
add_figure(doc, "photo_board_closeup2.jpg", "图 3-2　PYNQ-Z2 板卡特写：HDMI 输入/输出、千兆以太网、USB 与亚克力支架接线", width_cm=8.5)

add_h3(doc, "3.2.3 软件成果")
p323 = (
    "软件成果包括网页端、板端服务、驱动与固件。图 3-3 为网页端在实验室的实机界面（2026-11-03 复测）："
    "画面来自采集卡，目标框、计数与判定来自板端；本轮应用工单 2/3/2，检出 7 个目标、实际计数 4/1/2，"
    "判定为复检——所有目标分数低于阈值，低置信结果不进入通过结论。"
    "每次检查会把截图、目标与结果留档，页面可一键导出 CSV；界面另有本地演示与离线回放两种形态用于联调。"
)
add_body(doc, p323)
add_figure(doc, "webui_live2.png", "图 3-3　HTML 网页端 LIVE 界面：采集卡回传视频与板端轮次叠加（应用工单 2/3/2，7 目标，判定 RECHECK）")

add_h2(doc, "3.3 特性成果")
p33a = (
    "表 3-2 为同一负载（CoreMark 2K/32）下的特性消融：v0 为追溯的两级基线，v1 各行依次单独叠加转发、快速乘法与分支预测，"
    "用于把性能提升归因到具体机制。转发使 CPI 下降 10.20%，快速乘法使周期数再降 21.95%，两位分支预测再降 5.15%。"
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
    "表 3-2 的 CPI、IPC 与 CoreMark/MHz 均为公开标准口径：CoreMark 是 EEMBC 的行业基准 [3]，CPI 与 IPC 是体系结构通用指标 [15]。"
    "表 3-3 据此与公开报告的同类软核对比：Ibex 官方给出三档流水配置的 CoreMark/MHz [16]，"
    "PicoRV32 官方给出 Dhrystone 0.516 DMIPS/MHz、平均 CPI 4.100 [11]。"
    "本设计每兆赫 1.974 个 CoreMark，介于 Ibex 二周期配置与两级流水之间；CPI 1.606 约为 PicoRV32 报告值的四成。"
    "两者设计目标不同，编译器与运行条件也有差异，数值作量级参照而非精确排名。"
)
add_body(doc, p33a2)
add_table(doc, "表 3-3　与公开报告口径的同类 RISC-V 软核对比", ["核 / 配置", "流水结构", "基准", "公开数值", "来源"], [
    ["本设计 v1 转发 + BHT2", "三级 + 转发 + 64 项 BHT", "CoreMark 2K/32", "1.974 CoreMark/MHz（CPI 1.606）", "本文"],
    ["Ibex 基础配置", "二周期 RV32EC", "CoreMark", "0.904 CoreMark/MHz", "[16]"],
    ["Ibex 两级流水", "2-stage", "CoreMark", "2.47 CoreMark/MHz", "[16]"],
    ["Ibex 三级流水", "3-stage（高性能档）", "CoreMark", "3.13 CoreMark/MHz", "[16]"],
    ["PicoRV32", "多周期（快速乘除/桶形移位）", "Dhrystone", "0.516 DMIPS/MHz（CPI 4.100）", "[11]"],
], [3.8, 4.0, 2.4, 3.6, 1.2], font_size=9.0, align_center_cols=[2, 4])
p33b = (
    "表 3-4 为时序与资源。核单独综合后对应 86.806 MHz；全系统在 40 MHz 下余量 2.498 ns，共存位流余量 1.184 ns；"
    "视频流水线在 74.25 MHz 下余量 0.330 ns。全系统使用 136 个 DSP（共 220）与 69 个 Block RAM（共 140），设计规则检查无错误。"
)
add_body(doc, p33b)
add_table(doc, "表 3-4　时序与资源（Vivado 2026.1，xc7z020clg400-1）", ["设计", "约束", "WNS", "LUT / FF", "BRAM / DSP"], [
    ["处理器核（单独综合）", "11.52 ns", "+0.538 ns", "2443 / 637", "0 / 0"],
    ["核与总线系统", "25 ns（40 MHz）", "+3.618 ns", "6768 / 859", "8 / 0"],
    ["视频流水线", "13.468 ns（74.25 MHz）", "+0.330 ns", "1985 / 1515", "38 / 0"],
    ["协处理器控制器", "10 ns（100 MHz）", "+0.317 ns", "4540 / 4037", "— / 136"],
    ["全系统", "25 ns（40 MHz）", "+2.498 ns", "—", "69 / 136"],
    ["共存位流", "25 ns（40 MHz）", "+1.184 ns", "—", "69 / 136"],
], [4.6, 4.4, 2.8, 2.8, 2.4], font_size=9.5, align_center_cols=[0, 1, 2, 3, 4])
p33c = (
    "表 3-5 为软件验证：全量回归 172 条通过、9 条为预期门禁失败、0 条意外；Python 与硬件仿真分组全部通过；"
    "服务与前端模拟闭环 1 轮通过；异常矩阵覆盖 4 轮服务与 9 个引擎场景。"
)
add_body(doc, p33c)
add_table(doc, "表 3-5　软件与服务验证", ["项目", "结果"], [
    ["RTL 全量回归", "172 条通过；9 条预期门禁失败；0 条意外"],
    ["Python 分组", "检查 19 组 + 视觉 21 组，全部通过"],
    ["硬件仿真分组", "视觉 25 组 + 采集 2 组，全部通过"],
    ["服务与前端模拟轮次", "1 轮通过；3 目标 / 3 ROI；1 条记录"],
    ["异常矩阵", "4 轮服务异常 + 9 个引擎场景"],
], [6.4, 8.6], font_size=10.0)
p33d = (
    "表 3-6 为板上时间线：从首次上电未响应（固件初值缺失）到修复后四例黄金对照，再到共存位流联调；"
    "多目标旧包暴露结果错位，修复版仅通过仿真，尚未上板。"
)
add_body(doc, p33d)
add_table(doc, "表 3-6　板上验证时间线", ["日期", "结果"], [
    ["10-25", "时钟与数据传输通过，但推理未启动，定位为固件初值缺失"],
    ["10-26", "初值修复后，零输入与固定图形各 3 轮全部匹配"],
    ["10-27", "四例黄金对照全部匹配，寄存器连续读取无错误；共存位流同时输出 HDMI、抓取原帧并运行硬件 CNN"],
    ["10-27", "多目标结果错位在仿真中修复，修复包未上板"],
], [2.6, 11.8], font_size=9.5, align_center_cols=[0])
p33e = (
    "结果讨论：四档数据分别对应转发、快速乘法与分支预测的作用，组合收益不归因单一机制；核与视觉流水线未占用 DSP，"
    "协处理器仍余 84 个 DSP、71 个 Block RAM。共存实测发现旧包结果错位——首个结果槽为空、后续槽滞后一个目标；"
    "修复后在仿真中通过，修复包尚未上板，因此多目标识别不作验收结论。"
)
add_body(doc, p33e)
p33f = (
    "验收边界：单目标四例是临时的黄金对照，不代表识别精度；多目标修复包未上板；板卡历史故障未复现，长时与温度稳定性未测；"
    "正式模型与整机验收仍未完成。全部数据可由项目归档的测试与日志复现。"
)
add_body(doc, p33f, align=WD_ALIGN_PARAGRAPH.LEFT)


# ================================================================== 第四部分
add_h1(doc, "第四部分　总结")

add_h2(doc, "4.1 可扩展之处")
p41 = (
    "后续可扩展五个方向：正式的量化模型与真实数据精度报告；多目标修复包上板与逐目标定位，覆盖阴影和反光造成的分裂与合并；"
    "全帧数据传输与连续作业；把频率提高到 100/125 MHz 并做长时与温度稳定性测试；外壳、光学与产线接口，形成可交付的整机。"
)
section_count("4.1 可扩展之处", [p41])
add_body(doc, p41)

add_h2(doc, "4.2 心得体会")
# 心得体会：owner 手改定稿（2026-10-31），生成器按段落逐字同步；
# 与 DOCX 唯一差异为 PASS 等标识符在重建时自动应用等宽排版。
hearts = [
    (
        "回顾此次持续两月有余的项目经历，我们三个大二的学生从零开始，在学中做，在做中学，遭遇许多未曾设想的障碍："
        "Vivado 许可证的申请遇到阻塞、开发环境的配置出现错误、固件种类不知如何选择、代码出现未知问题，等等。"
        "我们曾在深夜对照着技术文档一步一步跑仿真，也曾不止一次地将结果推倒重来。"
        "我们审慎使用 agent，小步推进，不嫌繁琐；三个人每周日开会讨论，互相审核成果。"
    ),
    (
        "在编写处理器核 RTL 的过程中，我们最初的理想目标是完成三级流水线，我们知道难度很大，也预料到结果可能会失败，"
        "但我们还是花了大功夫做完，怀着希望去做验证，结果 WNS 小于 -8ns，三级流水线宣告失败。"
        "尽管大家都感到很挫败，但收拾心情之后仍然重新开始推进项目：先退回两级流水线稳住基础，再一点点修改，"
        "加上转发、乘法器优化和分支预测，最终 86.806 MHz 的时序和 44/44 的指令集测试总算成功通过。"
        "在编写协处理器的过程中，128 个乘法阵列、模型量化、训练数据整理等难题，也是我们一个坎一个坎迈过来的。"
    ),
    (
        "十月下旬树莓派相机出现故障不能使用，板卡也一度罢工，面对这些棘手的难题我们没有退缩，"
        "先订购新的树莓派配件保证硬件可以正常运转，然后我们逐一排查启动流程、时钟、固件初值，"
        "连着几天泡在串口日志里，终于揪出了错误，让位流重新跑了起来；"
        "之后又把 HDMI 显示、原帧捕获和硬件 CNN 集成进同一个位流，搭起真实相机加采集卡的联调环境。"
        "板上每一个 PASS，背后都是我们一次次烧写、回读、核对换来的。"
    ),
    (
        "在前端设计与实现的过程中，我们也是“摸着石头过河”的。一开始我们选择的是 EXE 形式，从基础功能做起，"
        "一步一步调整，从页面布局到交互设计，再到美观需求，前后打磨了好几版。"
        "然而 EXE 笨重、容易出现 Bug 的缺点让我们犹豫要不要寻找新的形式。"
        "最后，我们决定还是要尽最大努力把产出做到最好，哪怕需要一次又一次的推倒重来。"
        "于是我们改向 HTML 网页版，把功能做得更丰富，界面做得更简洁。"
    ),
    (
        "参与这场比赛的过程不仅让我们学到很多开发板的知识，熟悉了 Vivado 等工具的使用并从 0 到 1 探索了处理器核的架构，"
        "更让我们学会了如何把一个复杂的问题拆解成一个小问题、如何分工、如何进行团队协作。"
        "我们最深的体会是：在工程中，失败是常态，也正因为这一点，失败并不可怕，因为办法总比困难多。"
        "每一次对问题的修正都是一次成长——无论对于项目来说，还是对于人来说。"
        "我们深知我们的作品仍存在不完美、不成熟之处，但我们已经尽力做到自己的极限。回顾这两个月，我们受益良多。"
    ),
]
section_count("4.2 心得体会", hearts)
for h in hearts:
    add_body(doc, h)

add_h2(doc, "4.3 大语言模型协作记录与 Skills 沉淀")
p43a = (
    "本项目全程与大语言模型协作开发，并完整留痕，协作记录累计 220 条。三条纪律贯穿全程："
    "一是理解门槛——AI 产出的代码入库前必须由使用者讲清设计意图；"
    "二是证据门禁——任何“已验证”都要有可复现的脚本与原始记录支撑；"
    "三是小步交付——单步改动控制在可审阅的规模。"
)
add_body(doc, p43a)
p43b = (
    "我们把可复用的流程沉淀为 9 个技能包（表 4-1），覆盖编码、接口约定、时序、板级排障与数据集审计，"
    "既约束 AI 的行为边界，也便于新成员按同样流程接手。责任归属不变，方向、取舍与验收始终由团队负责。"
)
add_body(doc, p43b)
add_table(doc, "表 4-1　Skills 沉淀清单", ["技能包", "用途"], [
    ["古法编程", "小步交付、先设计后写码、逐段讲解"],
    ["理解门槛", "AI 代码入库前必须讲清设计意图"],
    ["契约冻结", "接口编码空间核对、负例校验、缺口只登记"],
    ["时序收敛", "时序口径统一、降深度改写、等价回归"],
    ["仿真与上板一致性", "指令计数口径、跨工具对拍"],
    ["板级排障", "JTAG、引脚约束、时钟配置、位流下载"],
    ["大规模重做", "性价比子集、冻结后重写"],
    ["缺陷修复", "功能坏与反馈坏的区分、修复必证明"],
    ["数据集防泄漏", "会话级划分、文件与像素双哈希"],
], [4.4, 10.0], font_size=9.5)
section_count("4.3 大语言模型协作记录与 Skills 沉淀", [p43a, p43b])

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
    "lowRISC. Ibex: A 32-bit RISC-V CPU Core（官方性能文档：各配置 CoreMark/MHz）. https://github.com/lowRISC/ibex",
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
