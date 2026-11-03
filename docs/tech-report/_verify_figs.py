# -*- coding: utf-8 -*-
"""一次性：校验图号顺序与正文引用一致性。"""
import re
from docx import Document

d = Document(r"docs\tech-report\EdgeSight-技术文档-初版.docx")
caps = []
body_refs = []
for p in d.paragraphs:
    t = p.text.strip()
    m = re.match(r"^图 (\d+-\d+)\u3000", t)
    if m:
        caps.append(m.group(1))
    for r in re.findall(r"图 (\d+-\d+)", t):
        if not m:
            body_refs.append((r, t[:40]))

print("captions:", caps)
print("caption count:", len(caps))
dup = [c for c in set(caps) if caps.count(c) > 1]
print("duplicate captions:", dup)
missing = sorted({r for r, _ in body_refs} - set(caps))
print("refs without caption:", missing)
print("body refs:", sorted({r for r, _ in body_refs}))
# 表格编号
tabs = []
for p in d.paragraphs:
    t = p.text.strip()
    m = re.match(r"^表 (\d+-\d+)\u3000", t)
    if m:
        tabs.append(m.group(1))
print("tables:", tabs, "dup:", [c for c in set(tabs) if tabs.count(c) > 1])
