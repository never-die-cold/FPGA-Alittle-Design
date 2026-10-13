"""Write offline HTML, complete machine-readable inventory and Markdown sections."""
import csv
import hashlib
import json
import os
from collections import Counter
from urllib.parse import quote

from scan import OUT, ROOT


def md_link(path):
    return f"[{path}](../../../{quote(path, safe='/')})"


def write_outputs(records, metadata):
    OUT.mkdir(exist_ok=True)
    (OUT / "sections").mkdir(exist_ok=True)
    for group in sorted({r["group"] for r in records}):
        rows = [r for r in records if r["group"] == group]
        lines = [f"# {group}：逐文件说明", "", f"{len(rows)}个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。", "",
                 "| 文件 | 一两句话说明 | 关联文件（最多展示5项） |", "| --- | --- | --- |"]
        previous = None
        for r in rows:
            parent = r["path"].rsplit("/", 1)[0] if "/" in r["path"] else "根目录"
            if parent != previous:
                lines += [f"| **{parent}** | | |"]
                previous = parent
            refs = "<br>".join(x["type"] + "：" + md_link(x["path"]) for x in r["relations"][:5])
            if len(r["relations"]) > 5:
                refs += f"<br>另{len(r['relations']) - 5}项见搜索页"
            lines.append(f"| {md_link(r['path'])}<br>{r['kind']} · {r['state']} | {r['description'].replace('|', '／')} | {refs or '未提取到明确局部关系'} |")
        (OUT / f"sections/{group}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "files.json").write_text(json.dumps({"metadata": metadata, "files": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "files.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["文件路径", "目录组", "类型", "版本状态", "一两句话说明", "说明依据", "关联总数", "关联文件（最多20项，完整关系见JSON）"])
        for r in records:
            writer.writerow([r["path"], r["group"], r["kind"], r["state"], r["description"], r["basis"], len(r["relations"]),
                             "\n".join(x["type"] + "：" + x["path"] for x in r["relations"][:20])])
    template = (OUT / "tools/page.html").read_text(encoding="utf-8")
    data = json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    for key, value in {"__COUNT__": str(len(records)), "__DATE__": metadata["date"], "__REV__": metadata["revision"][:7], "__DATA__": data}.items():
        template = template.replace(key, value)
    (OUT / "index.html").write_text(template, encoding="utf-8")
    intro = (OUT / "tools/README-template.md").read_text(encoding="utf-8")
    directory = "\n".join(f"| [{g}](sections/{g}.md) | {n} |" for g, n in sorted(Counter(r["group"] for r in records).items()))
    replacements = {"__COUNT__": str(len(records)), "__PROJECT_COUNT__": str(metadata["project_count"]),
                    "__REV__": metadata["revision"][:7], "__DATE__": metadata["date"], "__DIRECTORY__": directory}
    for key, value in replacements.items():
        intro = intro.replace(key, value)
    (OUT / "README.md").write_text(intro, encoding="utf-8")


def validate(records, paths, metadata):
    actual = {r["path"] for r in records}
    assert len(actual) == len(records) and actual == set(paths), "missing/duplicate descriptions"
    assert all(r["description"] and "\ufffd" not in r["description"] for r in records), "empty/invalid description"
    assert all((ROOT / p).is_file() for p in paths if p != "docs/file-guide/validation.json"), "missing local file"
    assert all(x["path"] in actual for r in records for x in r["relations"]), "broken relation"
    report = {"date": metadata["date"], "revision": metadata["revision"], "file_count": len(records),
              "missing": 0, "duplicates": 0, "broken_relations": 0,
              "relations": sum(len(r["relations"]) for r in records),
              "description_basis": dict(Counter(r["basis"] for r in records)),
              "boundary": "Git tracked + nonignored untracked; .git and ignored dependencies/build outputs excluded",
              "paths_sha256": hashlib.sha256("\n".join(paths).encode()).hexdigest()}
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
