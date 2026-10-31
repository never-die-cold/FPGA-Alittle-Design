# -*- coding: utf-8 -*-
"""一次性校验：全文（正文+表格）不得有裸标识符 run——命中模式者必须是 Consolas。"""
import re
from docx import Document

d = Document(r"docs\tech-report\EdgeSight-技术文档-初版.docx")
pat = re.compile(
    r"\b[a-zA-Z][a-zA-Z0-9]*_[a-zA-Z0-9]+\b"
    r"|\b(?:STATUS|ACCEPTED|UNCONSUMED|CONSUME|NO_ACK|HW_TIMEOUT|STALE_RESULT|START)\b"
    r"|\w+\.(?:py|json|jsonl|sha256)(?![A-Za-z0-9])")
bad, mono = [], 0

def scan(runs, where):
    global mono
    for r in runs:
        t = getattr(r, "text", None)
        if not t:
            continue
        hit = pat.search(t)
        if not hit:
            continue
        fname = getattr(getattr(r, "font", None), "name", None) or ""
        if fname.startswith("Consolas"):
            mono += 1
        else:
            bad.append((where, t[:46], fname))

for para in d.paragraphs:
    scan(para.runs, "body")
for ti, tb in enumerate(d.tables):
    for ri, row in enumerate(tb.rows):
        for ci, c in enumerate(row.cells):
            for p in c.paragraphs:
                scan(p.runs, "table t%d r%d c%d" % (ti, ri, ci))
print("mono runs:", mono)
print("bare identifier runs:", len(bad))
for b in bad[:15]:
    print("BAD:", b)
