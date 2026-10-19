"""Independent checks for guide completeness, portable formats and whitespace."""
import csv
import json
import re
import subprocess

from scan import OUT, ROOT, git_paths


def main():
    document = json.loads((OUT / "files.json").read_text(encoding="utf-8"))
    records = document["files"]
    paths = {r["path"] for r in records}
    with (OUT / "files.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(paths) == len(records) == len(rows)
    assert {r["文件路径"] for r in rows} == paths
    assert all(len(value) <= 32767 for r in rows for value in r.values())
    html = (OUT / "index.html").read_text(encoding="utf-8")
    embedded = re.search(r'<script id="records" type="application/json">(.*?)</script>', html, re.S)
    assert json.loads(embedded.group(1)) == records
    markdown_count = sum(sum(1 for line in p.read_text(encoding="utf-8").splitlines()
                             if line.startswith("| [") and "<br>" in line)
                         for p in (OUT / "sections").glob("*.md"))
    assert markdown_count == len(records)
    assert all(1 <= r["description"].count("。") <= 2 for r in records)
    assert all(r["description"] and "\ufffd" not in r["description"] for r in records)
    current = git_paths("--cached") | git_paths("--others", "--exclude-standard")
    generated = {"docs/file-guide/index.html", "docs/file-guide/files.csv",
                 "docs/file-guide/files.json", "docs/file-guide/validation.json"}
    current = {p for p in current if p not in generated
               and not p.startswith("docs/file-guide/sections/")
               and not p.startswith("build/file-guide/")}
    if document["metadata"].get("scope", "source") == "source":
        current = {p for p in current if not p.startswith(("data/logs/", "data/evidence/", "data/golden/"))}
    assert not current - paths, sorted(current - paths)
    assert all((ROOT / p).is_file() for p in paths)
    assert all(x["path"] in paths for r in records for x in r["relations"])
    for p in OUT.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            assert all(line == line.rstrip(" \t") for line in p.read_text(encoding="utf-8-sig").splitlines()), str(p)
    for arguments in (["diff", "--check"], ["diff", "--cached", "--check"]):
        result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    print(f"PASS: JSON / HTML / CSV / Markdown cover {len(records)} unique files")
    print("PASS: every description is 1–2 sentences; no empty/garbled explanation")
    print("PASS: current Git/nonignored set has no uncovered path; all relation targets exist")
    print("PASS: CSV cells fit Excel limits; guide whitespace and both git diff checks pass")
    print(json.dumps(document["metadata"], ensure_ascii=False))


if __name__ == "__main__":
    main()
