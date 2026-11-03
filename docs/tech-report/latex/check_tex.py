#!/usr/bin/env python3
"""docs/tech-report/latex 源码静态检查（无 TeX 环境时的替代门禁）。

检查项：花括号平衡、环境配对、\\code{} 内禁用 \\_、\\code{} 外裸下划线、
$ 配对、\\input 与 \\includegraphics 目标存在、\\ref 有 \\label、
\\label 唯一且被引用（未引用仅提示）。
用法：python docs/tech-report/latex/check_tex.py  （退出码非 0 即有 ERROR）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEC = ROOT / "sections"
MAIN = ROOT / "main.tex"

errors, warns = [], []


def strip_comments(text):
    out = []
    for line in text.splitlines():
        i = line.find("%")
        while i != -1 and i > 0 and line[i - 1] == "\\":
            i = line.find("%", i + 1)
        out.append(line if i == -1 else line[:i])
    return "\n".join(out)


files = [MAIN] + sorted(SEC.glob("*.tex"))
all_text = ""
label_count = {}
for path in files:
    s = strip_comments(path.read_text(encoding="utf-8"))
    all_text += s + "\n"

    bal = 0
    for ch in s:
        if ch == "{":
            bal += 1
        elif ch == "}":
            bal -= 1
    if bal != 0:
        errors.append(f"{path.name}: 花括号不平衡（差 {bal}）")

    envs = {}
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", s):
        name = m.group(2)
        envs[name] = envs.get(name, 0) + (1 if m.group(1) == "begin" else -1)
    for name, n in envs.items():
        if n != 0:
            errors.append(f"{path.name}: 环境 {name} begin/end 配对差 {n}")

    for m in re.finditer(r"\\code\{([^{}]*)\}", s):
        if "\\_" in m.group(1):
            errors.append(f"{path.name}: \\code 内出现 \\_（会印出反斜杠）：{m.group(1)[:40]}")

    no_code = re.sub(r"\\code\{[^{}]*\}", "", s)
    # \sourcepath 第一参数是 \href 的 URL，hyperref 按原样读取，允许裸下划线
    no_code = re.sub(r"\\sourcepath\{[^{}]*\}", "", no_code)
    # \includegraphics 文件名由 graphics 宏包 detokenize（2019 年起），允许裸下划线
    no_code = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^{}]*\}", "", no_code)
    for ln, line in enumerate(no_code.splitlines(), 1):
        if re.search(r"(?<!\\)_", line):
            errors.append(f"{path.name}:{ln}: \\code 外疑似裸下划线")

    if no_code.count("$") % 2:
        errors.append(f"{path.name}: $ 数量为奇数")

    for m in re.finditer(r"\\label\{([^}]+)\}", s):
        if "#" in m.group(1):
            continue  # 宏定义里的形参，如 \figplaceholder 的 \label{#2}
        label_count[m.group(1)] = label_count.get(m.group(1), 0) + 1

for name, n in label_count.items():
    if n > 1:
        errors.append(f"重复 \\label：{name}（{n} 次）")

for m in re.finditer(r"\\input\{([^}]+)\}", all_text):
    if not (ROOT / (m.group(1) + ".tex")).exists():
        errors.append(f"\\input 缺文件：{m.group(1)}")

for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", all_text):
    if not (ROOT.parent / "figures" / m.group(1)).exists():
        errors.append(f"图缺失：{m.group(1)}")

labels = set(label_count)
refs = set(re.findall(r"\\ref\{([^}]+)\}", all_text))
for r in refs - labels:
    errors.append(f"\\ref 无对应 \\label：{r}")
for l in labels - refs:
    warns.append(f"\\label 未被引用（仅提示）：{l}")

print(f"检查文件数：{len(files)}")
print(f"ERROR {len(errors)} 项")
for e in errors:
    print("  ERROR", e)
print(f"WARN {len(warns)} 项")
for w in warns:
    print("  WARN ", w)
sys.exit(1 if errors else 0)
