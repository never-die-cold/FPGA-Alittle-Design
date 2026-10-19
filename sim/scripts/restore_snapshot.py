"""Restore or verify files listed in data/logs/<run>/SNAPSHOT-MANIFEST.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_path(run: str) -> Path:
    return ROOT / "data/logs" / run / "SNAPSHOT-MANIFEST.json"


def read_manifest(run: str) -> dict:
    path = manifest_path(run)
    if not path.is_file():
        raise SystemExit(f"missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob(blob: str) -> bytes:
    try:
        return subprocess.check_output(["git", "cat-file", "-p", blob], cwd=ROOT)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"git blob not found: {blob}") from exc


def source_bytes(rec: dict) -> bytes:
    canonical = rec.get("canonical")
    if canonical:
        path = ROOT / canonical
        if path.is_file():
            return path.read_bytes()
    return git_blob(rec["git_blob"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="run directory name under data/logs")
    parser.add_argument("--check", action="store_true", help="verify present files and restore sources")
    parser.add_argument("--restore", action="store_true", help="write missing files")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.restore:
        parser.error("choose --check or --restore")

    manifest = read_manifest(args.run)
    problems = []
    missing = 0
    restored = 0
    for rec in manifest["files"]:
        target = ROOT / rec["path"]
        if target.is_file():
            actual = sha256(target.read_bytes())
            if actual != rec["sha256"]:
                problems.append(f"sha256 mismatch: {rec['path']}")
            continue
        missing += 1
        try:
            data = source_bytes(rec)
        except SystemExit as exc:
            problems.append(f"{rec['path']}: {exc}")
            continue
        if sha256(data) != rec["sha256"]:
            problems.append(f"restore source hash mismatch: {rec['path']}")
            continue
        if args.restore:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            restored += 1

    result = {
        "run": args.run,
        "files": len(manifest["files"]),
        "missing": missing,
        "restored": restored,
        "problems": problems,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"run={args.run} files={len(manifest['files'])} missing={missing} restored={restored}")
        for problem in problems:
            print(f"  ERROR {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
