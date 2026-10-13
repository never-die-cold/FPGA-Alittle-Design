"""Collect Git project files and bounded text metadata, without executing them."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/file-guide"
TEXT = {".md", ".py", ".v", ".vhd", ".c", ".h", ".s", ".sh", ".ps1", ".tcl", ".xdc",
        ".json", ".jsonl", ".txt", ".log", ".rpt", ".xml", ".yml", ".yaml", ".csv",
        ".dat", ".data", ".output", ".patch", ".service", ".ld", ".include", ".bat"}


def git_paths(*args):
    raw = subprocess.check_output(["git", "ls-files", "-z", *args], cwd=ROOT)
    return {p.decode("utf-8") for p in raw.split(b"\0") if p}


def text_of(path):
    if path.suffix.lower() not in TEXT and path.name not in {"Makefile", "LICENSE", ".gitattributes", ".gitignore"}:
        return ""
    with path.open("rb") as handle:
        raw = handle.read(512 * 1024)
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    if b"\0" in raw[:1024]:
        return ""
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def group(path):
    parts = path.split("/")
    if len(parts) == 1 or parts[0] == ".github":
        return "root"
    if parts[0] == "data":
        return "data-" + parts[1]
    return parts[0]


def logical(path):
    for marker in ("/final-inputs/", "/inputs/", "/settled-script-archive/", "/final-src/", "/source-snapshot/"):
        if marker in path:
            return path.split(marker, 1)[1]
    return path


def collect():
    tracked = git_paths("--cached")
    paths = tracked | git_paths("--others", "--exclude-standard")
    paths = {p for p in paths if not p.startswith("docs/file-guide/")}
    guide_inputs = {p.relative_to(ROOT).as_posix() for p in (OUT / "tools").glob("*") if p.is_file()}
    groups = {group(p) for p in paths} | {"docs"}
    outputs = {"docs/file-guide/" + p for p in ("README.md", "index.html", "files.csv", "files.json", "validation.json")}
    outputs |= {f"docs/file-guide/sections/{g}.md" for g in groups}
    all_paths = sorted(paths | guide_inputs | outputs)
    texts = {p: text_of(ROOT / p) for p in all_paths if (ROOT / p).is_file()}
    return all_paths, tracked, texts, groups, len(paths)


def clean_title(text):
    match = re.search(r"^#\s+(.+)$", text, re.M)
    return re.sub(r"[*`<>]", "", match.group(1)).strip()[:110] if match else ""


def load_roles():
    exact = json.loads((OUT / "tools/roles.json").read_text(encoding="utf-8"))
    exact.update(json.loads((OUT / "tools/roles-extra.json").read_text(encoding="utf-8")))
    names = json.loads((OUT / "tools/script-roles.json").read_text(encoding="utf-8"))
    return exact, names
