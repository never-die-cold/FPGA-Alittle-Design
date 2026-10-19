"""Regenerate the run index tables in data/logs/README.md and data/evidence/README.md."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = "<!-- RUN-INDEX:START -->"
END = "<!-- RUN-INDEX:END -->"
TARGETS = (
    ("data/logs", "运行"),
    ("data/evidence", "证据主题"),
)


def human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} B"


def first_heading(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "（无法读取）"
    match = re.search(r"^#\s+(.+)$", text, re.M)
    return match.group(1).strip() if match else "（无标题）"


def stats(directory: Path) -> tuple[int, int]:
    count = 0
    size = 0
    for path in directory.rglob("*"):
        if path.is_file():
            count += 1
            try:
                size += path.stat().st_size
            except OSError:
                pass
    return count, size


def shorten(text: str, limit: int = 70) -> str:
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_table(base: str, label: str) -> str:
    directory = ROOT / base
    if not directory.is_dir():
        raise SystemExit(f"missing directory: {directory}")
    rows = []
    for path in sorted(directory.iterdir(), key=lambda p: p.name, reverse=True):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        count, size = stats(path)
        readme = path / "README.md"
        if readme.is_file():
            title = first_heading(readme)
        else:
            title = "⚠ 缺 README（PROVENANCE GAP）"
        date = (re.match(r"^(\d{4}-\d{2}-\d{2})", path.name) or [None, "—"])[1]
        rows.append(
            f"| `{path.name}` | {date} | {count} | {human_size(size)} | {shorten(title)} |"
        )
    return (
        f"## 目录索引（{len(rows)} 个{label}，自动生成）\n\n"
        "| 目录 | 日期 | 文件数 | 大小 | 说明 |\n"
        "|:---|:---:|---:|---:|:---|\n"
        + "\n".join(rows)
    )


def replace_block(text: str, block: str) -> str:
    if START not in text or END not in text:
        raise SystemExit(f"index markers not found ({START} / {END})")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return before + START + "\n" + block.rstrip() + "\n" + END + after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the two README index blocks")
    parser.add_argument("--check", action="store_true", help="fail if an index is stale")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args()
    if not args.write and not args.check and not args.json:
        parser.print_help()
        return 0

    result = {}
    failed = False
    for base, label in TARGETS:
        readme = ROOT / base / "README.md"
        if not readme.is_file():
            raise SystemExit(f"missing README: {readme}")
        current = readme.read_text(encoding="utf-8")
        expected = replace_block(current, render_table(base, label))
        result[base] = {
            "up_to_date": current == expected,
            "runs": len([p for p in (ROOT / base).iterdir() if p.is_dir() and not p.name.startswith("_")]),
        }
        if args.write:
            if current != expected:
                readme.write_text(expected, encoding="utf-8", newline="\n")
                result[base]["written"] = True
        elif args.check and current != expected:
            failed = True
            print(f"STALE: {base}/README.md (run: python sim/scripts/index_runs.py --write)")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not failed:
        print("run index: OK" if not args.write else "run index: updated")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
