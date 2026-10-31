# -*- coding: utf-8 -*-
"""一次性：统计 4.2 字数（汉字/总字符）并做生成器同步抽查。"""
import re
from docx import Document

d = Document(r"docs\tech-report\EdgeSight-技术文档-初版.docx")
on = False
cn = total = 0
paras = []
for p in d.paragraphs:
    t = p.text
    if t.startswith("4.2"):
        on = True
        continue
    if t.startswith("4.3"):
        on = False
    if on and t.strip():
        paras.append(t)
        cn += len(re.findall(r"[\u4e00-\u9fff]", t))
        total += len(t)
print("paragraphs:", len(paras), "chinese:", cn, "total:", total)

# 生成器同步抽查：py 源码里应能找到各段首句特征串
src = open(r"docs\tech-report\build_tech_report.py", encoding="utf-8").read()
for key in ("每周日开会讨论", "WNS 小于 -8ns", "树莓派相机出现故障", "从 0 到 1 探索", "受益良多"):
    print(("OK  " if key in src else "MISS"), key)
