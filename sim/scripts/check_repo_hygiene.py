"""Read-only repository hygiene checks for the EdgeSight repo."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import index_runs  # noqa: E402

ROOT_ALLOWED_FILES = {
    "README.md",
    "plan.md",
    "AGENTS.md",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
}
ROOT_ALLOWED_DIRS = {
    ".git",
    ".github",
    "src",
    "sim",
    "build",
    "board",
    "data",
    "docs",
    "report",
    "skill",
    "models",
    "results",
}
GENERATED_PATTERNS = (
    re.compile(r"(^|/)\.vvp$"),
    re.compile(r"(^|/)__pycache__/"),
    re.compile(r"\.pyc$"),
    re.compile(r"^sim/build/"),
    re.compile(r"^sim/xsim\.dir/"),
    re.compile(r"^\.Xil/"),
    re.compile(r"^NA/"),
    re.compile(r"^build/file-guide/"),
    re.compile(r"^docs/file-guide/(index\.html|files\.csv|files\.json|validation\.json|sections/)"),
)
# Historical snapshots are intentionally excluded from the current-link gate.
LINK_EXCLUDE_PREFIXES = (
    "data/logs/",
    "data/evidence/",
    "report/llm_log/",
    "docs/file-guide/tools/",
    "docs/outsource/fastener-vision-2026-10-07/",
    "src/riscv/done/",
    "src/riscv_fw/coremark/vendor/",
)
BIG_FILE_LIMIT = 5 * 1024 * 1024
BIG_FILE_ALLOW = {
    "models/hog-svm-train-only.yml",
    "data/logs/2026-10-12-pr-review/pr69-full-diff-check.txt",
    "data/logs/2026-10-15-onboard-n02-n03/exe-ffb7ab2.zip",
}


def git_paths(*args: str) -> list[str]:
    raw = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files", *args], cwd=ROOT
    )
    return [p for p in raw.decode("utf-8", "replace").splitlines() if p]


def check_root() -> list[str]:
    errors = []
    for entry in ROOT.iterdir():
        if entry.name in {".git"}:
            continue
        if entry.is_dir() and entry.name not in ROOT_ALLOWED_DIRS:
            errors.append(f"root: unexpected directory {entry.name}/")
        if entry.is_file() and entry.name not in ROOT_ALLOWED_FILES:
            errors.append(f"root: unexpected file {entry.name}")
    return errors


def check_generated(tracked: list[str]) -> list[str]:
    errors = []
    for path in tracked:
        for pattern in GENERATED_PATTERNS:
            if pattern.search(path):
                errors.append(f"generated tracked: {path}")
                break
    return errors


def check_run_readmes() -> list[str]:
    errors = []
    for base in ("data/logs", "data/evidence"):
        directory = ROOT / base
        for path in sorted(directory.iterdir()):
            if path.is_dir() and not path.name.startswith("_") and not (path / "README.md").is_file():
                errors.append(f"missing README: {base}/{path.name}/README.md")
    return errors


def check_indexes() -> list[str]:
    errors = []
    for base, label in index_runs.TARGETS:
        readme = ROOT / base / "README.md"
        if not readme.is_file():
            errors.append(f"missing index: {readme.relative_to(ROOT)}")
            continue
        current = readme.read_text(encoding="utf-8")
        expected = index_runs.replace_block(current, index_runs.render_table(base, label))
        if current != expected:
            errors.append(f"stale index: {base}/README.md (run python sim/scripts/index_runs.py --write)")
    return errors


def check_metrics() -> list[str]:
    import csv

    errors = []
    metrics = ROOT / "data/metrics.csv"
    if not metrics.is_file():
        return ["missing data/metrics.csv"]
    with metrics.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        field = "证据文件"
        if field not in (reader.fieldnames or []):
            return ["metrics.csv: missing 证据文件 column"]
        for row in reader:
            cell = (row.get(field) or "").strip()
            if not cell:
                continue
            candidates = re.split(r"[；;]", cell)
            for candidate in candidates:
                candidate = candidate.strip().strip("`").strip()
                if not candidate or " " in candidate:
                    continue
                if not re.search(r"\.(log|rpt|json|jsonl|csv|md|txt|png|pgm|hex|bin|xsa|hwh|bit|out)$", candidate):
                    continue
                if not (ROOT / candidate).exists():
                    errors.append(f"metrics evidence missing: {candidate}")
    return sorted(set(errors))


def check_links(tracked: list[str]) -> list[str]:
    errors = []
    link_re = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
    for rel in tracked:
        if not rel.endswith(".md"):
            continue
        if rel.startswith(LINK_EXCLUDE_PREFIXES):
            continue
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        for match in link_re.finditer(text):
            target = match.group(1)
            if re.match(r"^(https?:|mailto:|#|data:)", target):
                continue
            target = target.split("#", 1)[0]
            if not target or "*" in target or "__" in target:
                continue
            resolved = (path.parent / unquote(target)).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                errors.append(f"broken link: {rel} -> {target}")
    return sorted(set(errors))


def check_big_files(tracked: list[str]) -> list[str]:
    warnings = []
    for rel in tracked:
        path = ROOT / rel
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > BIG_FILE_LIMIT and rel not in BIG_FILE_ALLOW:
            warnings.append(f"large tracked file: {rel} ({size / 1048576:.1f} MB)")
    return warnings


def check_duplicates(tracked: list[str]) -> list[str]:
    raw = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files", "-s"], cwd=ROOT
    ).decode("utf-8", "replace")
    groups = defaultdict(list)
    for line in raw.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) < 2:
            continue
        groups[parts[1]].append(path)
    warnings = []
    for paths in groups.values():
        if len(paths) < 2:
            continue
        path = ROOT / paths[0]
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= 100 * 1024:
            warnings.append(f"duplicate blob ({len(paths)}x, {size / 1024:.0f} KB): {paths[0]} ...")
    return sorted(warnings, key=lambda x: -int(re.search(r"(\d+) KB", x).group(1)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable result")
    args = parser.parse_args()
    tracked = git_paths()
    errors = []
    warnings = []
    errors += check_root()
    errors += check_generated(tracked)
    errors += check_run_readmes()
    errors += check_indexes()
    errors += check_metrics()
    errors += check_links(tracked)
    warnings += check_big_files(tracked)
    warnings += check_duplicates(tracked)
    result = {
        "tracked": len(tracked),
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"tracked files: {len(tracked)}")
        print(f"errors: {len(errors)}")
        for item in errors:
            print(f"  ERROR {item}")
        print(f"warnings: {len(warnings)}")
        for item in warnings[:20]:
            print(f"  WARN  {item}")
        if len(warnings) > 20:
            print(f"  ... {len(warnings) - 20} more warnings")
        print("repo hygiene: " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
