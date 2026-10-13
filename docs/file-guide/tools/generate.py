"""Rebuild the per-file Chinese guide using only repository files and static reads."""
import argparse
import json
import subprocess
from pathlib import PurePosixPath

from describe import describe
from relations import build_relations
from render import validate, write_outputs
from scan import OUT, ROOT, collect, group, load_roles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="User-facing snapshot date, YYYY-MM-DD")
    args = parser.parse_args()
    paths, tracked, texts, groups, project_count = collect()
    exact, names = load_roles()
    relations = build_relations(paths, texts)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    records = []
    for p in paths:
        kind, description, basis = describe(p, texts.get(p, ""), relations[p], exact, names)
        records.append({"path": p, "group": group(p), "kind": kind,
                        "state": "索引自身" if p.startswith("docs/file-guide/") else "已纳入Git（含暂存）" if p in tracked else "未忽略的新文件",
                        "description": description, "basis": basis, "relations": relations[p]})
    metadata = {"date": args.date, "revision": revision, "project_count": project_count,
                "count": len(records), "note": "Includes current working-tree content; not an exact committed-tree guide."}
    write_outputs(records, metadata)
    report = validate(records, paths, metadata)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
