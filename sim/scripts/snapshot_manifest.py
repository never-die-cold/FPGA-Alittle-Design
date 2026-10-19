"""Build snapshot manifests for data/logs input copies and optionally prune duplicates.

Policy:
- A file whose git blob also exists outside data/ is restorable from git -> delete the copy.
- A file that only duplicates another data/ copy keeps one canonical copy -> delete the rest.
- A file with no duplicate is unique -> keep.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP_NAMES = {"inputs", "final-inputs", "handoff-inputs", "source-snapshot", "settled-script-archive"}
EXE_RE = re.compile(r"^exe-[0-9a-f]{6,}$")
MANIFEST = "SNAPSHOT-MANIFEST.json"
GUIDE = "SNAPSHOT.md"


def git_tracked() -> dict[str, list[str]]:
    raw = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files", "-s"], cwd=ROOT
    ).decode("utf-8", "replace")
    by_blob: dict[str, list[str]] = defaultdict(list)
    for line in raw.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 2:
            by_blob[parts[1]].append(path)
    return by_blob


def blob_hash(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def snapshot_roots(only_run: str | None = None):
    base = ROOT / "data/logs"
    for run in sorted(p for p in base.iterdir() if p.is_dir()):
        if only_run and run.name != only_run:
            continue
        roots = [p for p in sorted(run.iterdir()) if p.is_dir() and
                 (p.name in SNAP_NAMES or EXE_RE.match(p.name))]
        if roots:
            yield run, roots


def build_manifest(run: Path, roots: list[Path], tracked: dict[str, list[str]]) -> dict:
    records = []
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            blob = blob_hash(data)
            others = [p for p in tracked.get(blob, []) if p != rel]
            external = [p for p in others if not p.startswith("data/")]
            data_others = [p for p in others if p.startswith("data/")]
            if external:
                action = "restore"
                canonical = None
            elif data_others:
                canonical = sorted(data_others)[0]
                action = "keep" if rel <= canonical else "drop"
            else:
                action = "unique"
                canonical = None
            records.append({
                "path": rel,
                "size": len(data),
                "sha256": sha,
                "git_blob": blob,
                "action": action,
                "canonical": canonical,
            })
    # If a blob has several data copies, choose exactly one keeper.
    by_blob: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_blob[rec["git_blob"]].append(rec)
    for blob, group in by_blob.items():
        if any(r["action"] == "restore" for r in group):
            for rec in group:
                rec["action"] = "restore"
                rec["canonical"] = None
        elif any(r["action"] == "keep" for r in group):
            keeper = sorted(group, key=lambda r: r["path"])[0]
            for rec in group:
                if rec is keeper:
                    rec["action"] = "keep"
                    rec["canonical"] = None
                else:
                    rec["action"] = "drop"
                    rec["canonical"] = keeper["path"]
        else:
            for rec in group:
                rec["action"] = "unique"
                rec["canonical"] = None
    summary = {
        "total": len(records),
        "restore": sum(1 for r in records if r["action"] == "restore"),
        "keep": sum(1 for r in records if r["action"] == "keep"),
        "drop": sum(1 for r in records if r["action"] == "drop"),
        "unique": sum(1 for r in records if r["action"] == "unique"),
    }
    return {
        "run": run.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "restore=git blob; drop=canonical copy; keep/unique=stay",
        "roots": [r.relative_to(run).as_posix() + "/" for r in roots],
        "summary": summary,
        "files": records,
    }


def guide_text(manifest: dict) -> str:
    s = manifest["summary"]
    run = manifest["run"]
    return f"""# 快照输入清单（{run}）

> 本目录的 `inputs/`/`final-inputs/` 等源码/输入副本已按 `SNAPSHOT-MANIFEST.json` 去重。
> 这不是删除证据：可由 Git blob 恢复的副本已删除；唯一内容仍保留；恢复入口如下。

## 汇总

- 快照根：{', '.join(manifest['roots'])}
- 文件：{s['total']}
- 可恢复（Git blob）：{s['restore']}
- 保留（canonical/unique）：{s['keep'] + s['unique']}
- 删除的重复副本：{s['drop']}

## 恢复

```powershell
python sim/scripts/restore_snapshot.py --run {run} --check
python sim/scripts/restore_snapshot.py --run {run} --restore
```

`--check` 只检查当前文件和恢复源是否存在；`--restore` 把缺失的副本写回原路径并校验 sha256。
清单里的每条记录包含 `path`、`sha256`、`git_blob`、`action`、`canonical`。
"""


def write_manifests(prune: bool, only_run: str | None = None) -> dict:
    tracked = git_tracked()
    report = {"runs": 0, "files": 0, "deleted": 0, "bytes_deleted": 0, "manifests": []}
    for run, roots in snapshot_roots(only_run):
        manifest = build_manifest(run, roots, tracked)
        (run / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (run / GUIDE).write_text(guide_text(manifest), encoding="utf-8", newline="\n")
        report["runs"] += 1
        report["files"] += manifest["summary"]["total"]
        report["manifests"].append({"run": run.name, **manifest["summary"]})
        if prune:
            for rec in manifest["files"]:
                if rec["action"] not in {"restore", "drop"}:
                    continue
                path = ROOT / rec["path"]
                if path.exists():
                    report["bytes_deleted"] += path.stat().st_size
                    path.unlink()
                    report["deleted"] += 1
            # remove empty dirs under the run (never the run itself)
            for root in roots:
                for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifests", action="store_true")
    parser.add_argument("--prune", action="store_true")
    parser.add_argument("--run", help="only process one run directory")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.write_manifests and not args.prune:
        tracked = git_tracked()
        rows = []
        total = {"total": 0, "restore": 0, "keep": 0, "drop": 0, "unique": 0}
        for run, roots in snapshot_roots(args.run):
            manifest = build_manifest(run, roots, tracked)
            rows.append({"run": run.name, **manifest["summary"]})
            for key in total:
                total[key] += manifest["summary"][key]
        result = {"runs": len(rows), "total": total, "runs_detail": rows}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
              f"runs={len(rows)} total={total['total']} restore={total['restore']} "
              f"keep={total['keep']} drop={total['drop']} unique={total['unique']}")
        return 0
    report = write_manifests(args.prune, args.run)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else
          f"runs={report['runs']} files={report['files']} deleted={report['deleted']} "
          f"bytes_deleted={report['bytes_deleted']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
