# -*- coding: utf-8 -*-
"""一次性：owner 手改稿的硬伤修正（仅 4.2 五段，替换后单段合并为同格式单 run）。"""
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

PATH = r"docs\tech-report\EdgeSight-技术文档-初版.docx"
PAIRS = [
    ("结果 WNS 大于 -8ns，三级流水线宣告失败", "结果 WNS 小于 -8ns，三级流水线宣告失败"),
    ("怀着希望去做仿真验证", "怀着希望去做验证"),
    ("在编写处理器核 RTL的过程中", "在编写处理器核 RTL 的过程中"),
    ("过程中， 128 个乘法阵列", "过程中，128 个乘法阵列"),
    ("然而EXE笨重、容易出现Bug的缺点", "然而 EXE 笨重、容易出现 Bug 的缺点"),
    ("从0到1", "从 0 到 1"),
]

d = Document(PATH)
fixed = []
on = False
for p in d.paragraphs:
    t = p.text
    if t.startswith("4.2"):
        on = True
    if t.startswith("4.3"):
        on = False
    if not (on and t.strip()):
        continue
    new = t
    for a, b in PAIRS:
        new = new.replace(a, b)
    if new != t:
        runs = p.runs
        if runs:
            r0 = runs[0]
            r0.text = new
            r0.font.name = "Times New Roman"
            r0.font.size = Pt(12)
            rPr = r0._element.get_or_add_rPr()
            rf = rPr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rPr.append(rf)
            rf.set(qn("w:ascii"), "Times New Roman")
            rf.set(qn("w:hAnsi"), "Times New Roman")
            rf.set(qn("w:eastAsia"), "宋体")
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        fixed.append(new[:30])

d.save(PATH)
print("fixed paragraphs:", len(fixed))
for f in fixed:
    print(" -", f, "...")
