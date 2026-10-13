"""Extract explicit imports, local references, and known entry-point membership."""
import ast
import re
from collections import defaultdict
from pathlib import PurePosixPath
from urllib.parse import unquote

from scan import ROOT, logical


def module_refs(text, modules):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    found = set()
    for match in re.finditer(r"\b([A-Za-z_]\w*)\s*(?=#|[A-Za-z_]\w*\s*\()", text):
        name = match.group(1)
        if name not in modules:
            continue
        tail = text[match.end():].lstrip()
        if tail.startswith("#"):
            start = tail.find("(")
            depth, end = 0, start
            for end in range(start, len(tail)):
                depth += (tail[end] == "(") - (tail[end] == ")")
                if depth == 0:
                    break
            tail = tail[end + 1:].lstrip()
        if re.match(r"[A-Za-z_]\w*\s*\(", tail):
            found.add(modules[name])
    return found


def build_relations(paths, texts):
    pathset, byname, bydir = set(paths), defaultdict(list), defaultdict(list)
    for p in paths:
        byname[PurePosixPath(p).name].append(p)
        bydir[str(PurePosixPath(p).parent)].append(p)
    modules = {}
    for p, text in texts.items():
        if p.startswith("src/") and p.endswith(".v"):
            for name in re.findall(r"\bmodule\s+(\w+)", re.sub(r"//[^\n]*", "", text)):
                modules[name] = p
    edges = defaultdict(set)

    def add(origin, target, kind):
        if target in pathset and target != origin:
            edges[origin].add((target, kind))

    def choose(origin, name):
        candidates = byname.get(name, [])
        same = str(PurePosixPath(origin).parent / name)
        active = [p for p in candidates if p.startswith(("src/", "sim/scripts/", "sim/vision/", "data/golden/"))]
        return same if same in candidates else (active[0] if len(active) == 1 else None)

    for p in paths:
        text = "" if p.startswith("docs/file-guide/") and "/tools/" not in p else texts.get(p, "")
        lp = logical(p)
        if lp != p:
            add(p, lp, "对应的当前文件")
        parent = PurePosixPath(p).parent
        if p.startswith(("data/", "results/", "build/reports/", "board/logs/")):
            def family(q):
                return re.sub(r"[._-](?:exit|console|stdout|stderr)$", "", PurePosixPath(q).stem)
            for sibling in bydir[str(parent)]:
                if family(sibling) == family(p):
                    add(p, sibling, "同名配套文件")
                elif PurePosixPath(sibling).name in {"metadata.json", "input.json", "result.json", "manifest.json", "packet.json"}:
                    add(p, sibling, "同目录输入/元数据")
        for ancestor in (parent, *parent.parents):
            readme = str(ancestor / "README.md")
            if readme in pathset and readme != p:
                add(p, readme, "所在目录说明")
                break
        if p.endswith(".py"):
            try:
                for node in ast.walk(ast.parse(text)):
                    names = [node.module] if isinstance(node, ast.ImportFrom) else ([a.name for a in node.names] if isinstance(node, ast.Import) else [])
                    for name in names:
                        target = choose(p, (name or "").split(".")[-1] + ".py")
                        if target:
                            add(p, target, "Python导入")
            except (SyntaxError, ValueError):
                pass
        if p.endswith(".v"):
            for target in module_refs(text, modules):
                add(p, target, "RTL例化")
        for ref in re.findall(r"(?:src|sim|docs|data|build|board|report|models|results|skill)/[\w./-]+\.[A-Za-z0-9]+", text):
            add(p, ref, "文本引用")
        for ref in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text) if p.endswith(".md") else []:
            target = unquote(ref.strip("<>").split("#")[0])
            resolved = (ROOT / p).parent / target
            try:
                add(p, resolved.resolve().relative_to(ROOT).as_posix(), "文档链接")
            except ValueError:
                pass
        if p.startswith("sim/") and PurePosixPath(p).name.startswith(("tb_", "test_")):
            name = PurePosixPath(p).name
            for runner, content in texts.items():
                if runner.startswith("sim/scripts/run_") and (name in content or ("test_$name.py" in content and name[5:-3] in content.split())):
                    add(p, runner, "测试入口引用")
    return {p: [{"path": q, "type": k} for q, k in sorted(edges[p])] for p in paths}
