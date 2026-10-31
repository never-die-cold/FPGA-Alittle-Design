# -*- coding: utf-8 -*-
"""一次性对照：同一进程内 直接 dump vs 扫描管线 的结论必须一致。"""
import re
from docx import Document

d = Document(r"docs\tech-report\EdgeSight-技术文档-初版.docx")
t10 = d.tables[10]
print("t10 rows:", len(t10.rows), "cols:", len(t10.columns))
cell = t10.rows[1].cells[1]
print("direct dump t10 r1 c1:")
for p in cell.paragraphs:
    for r in p.runs:
        print("   ", repr(r.text[:40]), "font=", r.font.name)

t0 = d.tables[0]
print("t0 rows:", len(t0.rows))
for ri in range(len(t0.rows)):
    print("  r%d c0:" % ri, t0.rows[ri].cells[0].text[:14], "| c1:", t0.rows[ri].cells[1].text[:30])

pat = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*_[a-zA-Z0-9]+\b")
found = []
for ri in range(len(t0.rows)):
    for ci, c in enumerate(t0.rows[ri].cells):
        for p in c.paragraphs:
            for r in p.runs:
                if pat.search(r.text or ""):
                    found.append((ri, ci, r.text[:30], r.font.name))
print("t0 scan hits:", found)
