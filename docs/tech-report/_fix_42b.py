# -*- coding: utf-8 -*-
"""一次性：修正 4.2 末段「从 0 到 1探索」缺空格。"""
from docx import Document

PATH = r"docs\tech-report\EdgeSight-技术文档-初版.docx"
d = Document(PATH)
n = 0
for p in d.paragraphs:
    if "1探索" in (p.text or ""):
        for r in p.runs:
            if "1探索" in r.text:
                r.text = r.text.replace("1探索", "1 探索")
                n += 1
d.save(PATH)
print("fixed runs:", n)
