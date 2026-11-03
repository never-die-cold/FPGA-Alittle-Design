"""Independent signed J-immediate and process exit checks; no external temp files."""
import ast
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "sim/tools/verify_rv32i.py"
text = path.read_text(encoding="utf-8")
tree = ast.parse(text)
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ASM_CASES"
                                             for t in node.targets):
        break
    nodes.append(node)
scope = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
for word, offset in [(0x800000ef, -1048576), (0x800800ef, -524288),
                     (0xffdff0ef, -4), (0x000000ef, 0),
                     (0x000800ef, 524288), (0x7ffff0ef, 1048574)]:
    assert scope["decode"](word) == f"jal x1, {offset}"
    assert scope["asm_to_int"](f"jal x1, {offset}") == word
for content, code in [(text, 0), (text.replace('"007302b3"', '"00000000"', 1), 1)]:
    result = subprocess.run([sys.executable, "-c", content], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == code, result.stdout
    assert (b"ALL OK" if code == 0 else b"HAS MISMATCH") in result.stdout
print("PASS: JAL signed limits/large positive offsets; self-check mismatch exits 1")
