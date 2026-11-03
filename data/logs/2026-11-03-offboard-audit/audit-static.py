"""Reproduce repository inventory and Python syntax/complexity observations.

Run from repository root: python data/logs/2026-11-03-offboard-audit/audit-static.py
Counts include existing nonignored untracked sources; exclude this audit itself.
Branch counts are review hints, not cyclomatic complexity or defect proof.
"""
import ast
import collections
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
raw = subprocess.check_output([
    "git", "-c", "core.quotepath=false", "ls-files", "--cached", "--others",
    "--exclude-standard"], cwd=ROOT).decode("utf-8")
paths = sorted({p for p in raw.splitlines()
                if not p.startswith("data/logs/2026-11-03-offboard-audit/")})
counts, errors, sizes, functions = collections.Counter(), [], [], []
parsed = 0
json_errors, encoding_errors = [], []
text_suffixes = {".md", ".tex", ".py", ".v", ".mjs", ".html", ".json", ".jsonl"}
for name in paths:
    path = ROOT / name
    if not path.is_file():
        continue
    counts[path.suffix.lower() or "<none>"] += 1
    if path.suffix in text_suffixes:
        try:
            decoded = path.read_text(encoding="utf-8-sig")
        except UnicodeError as error:
            encoding_errors.append((name, str(error)))
            continue
        if path.suffix in (".json", ".jsonl"):
            lines = decoded.splitlines() if path.suffix == ".jsonl" else [decoded]
            for number, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except ValueError as error:
                    json_errors.append((name, number, str(error)))
    if path.suffix not in (".py", ".v", ".sh", ".tcl", ".html", ".mjs"):
        continue
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if name.startswith(("src/", "sim/", "tools/", "build/", "docs/")):
        sizes.append((len(text.splitlines()), name))
    if path.suffix != ".py":
        continue
    try:
        tree = ast.parse(text, filename=name)
        parsed += 1
    except SyntaxError as error:
        errors.append(str(error))
        continue
    if name.startswith(("src/", "tools/")):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                branches = sum(isinstance(n, (ast.If, ast.For, ast.While,
                    ast.Try, ast.BoolOp, ast.IfExp)) for n in ast.walk(node))
                functions.append((branches, node.end_lineno-node.lineno+1,
                                  name, node.lineno, node.name))
print(json.dumps({"files": len(paths), "extensions": counts,
    "python_parsed": parsed, "python_syntax_errors": errors,
    "json_parse_errors": json_errors, "text_encoding_errors": encoding_errors,
    "largest_code_files": sorted(sizes, reverse=True)[:25],
    "branch_heavy_functions": sorted(functions, reverse=True)[:20]}, indent=2))
raise SystemExit(bool(errors or json_errors or encoding_errors))
