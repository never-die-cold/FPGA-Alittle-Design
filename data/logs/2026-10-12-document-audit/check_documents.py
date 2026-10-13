"""Check this docs-only diff, local links, and implementation inventory offline."""
import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError("output must be inside repository")
    messages = []

    def git(*arguments):
        result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"git {arguments}: {result.stdout}{result.stderr}")
        return result.stdout

    changed = git("diff", "--name-only").splitlines()
    if any(not name.endswith(".md") for name in changed):
        raise ValueError("unexpected unstaged product-code change")
    targets = set(changed) | {
        "docs/implementation-document-audit-2026-10-12.md",
        "report/llm_log/2026-10-12-implementation-document-audit.md",
        "data/logs/2026-10-12-document-audit/README.md",
    }
    links = 0
    for name in sorted(targets):
        path = ROOT / name
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = target.strip().strip("<>")
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            local = unquote(target.split("#", 1)[0])
            resolved = (path.parent / local).resolve()
            if local and resolved != output and not resolved.exists():
                raise FileNotFoundError(f"{name}: {target}")
            links += 1
    messages.append(f"PASS: {len(targets)} documents, {links} local link targets exist")
    added = sorted(targets - set(changed)) + [str(Path(__file__).resolve().relative_to(ROOT))]
    for name in added:
        for number, line in enumerate((ROOT / name).read_text(encoding="utf-8").splitlines(), 1):
            if line != line.rstrip(" \t"):
                raise ValueError(f"new file trailing whitespace: {name}:{number}")
    messages.append("PASS: new Markdown/checker files have no trailing whitespace")
    rtl = (ROOT / "sim/scripts/run_vision_iverilog.sh").read_text(encoding="utf-8")
    all_lines = "\n".join(line for line in rtl.splitlines()
                          if "all)" in line or 'if [ "$MODE" = all ]' in line)
    count = len(re.findall(r"vision/tb_[\w]+\.v", all_lines))
    if count != 25:
        raise ValueError(f"unexpected vision RTL test count: {count}")
    python = (ROOT / "sim/scripts/run_vision_python.sh").read_text(encoding="utf-8")
    groups = re.search(r"for name in (.+); do", python).group(1).split()
    if len(groups) != 14 or "c01_build_inputs" not in groups:
        raise ValueError(f"unexpected vision Python groups: {groups}")
    messages.append("PASS: current inventory = 25 vision RTL tb / 14 vision Python groups")
    git("diff", "--check")
    git("diff", "--cached", "--check")
    messages.append("PASS: git diff --check and git diff --cached --check (exit 0)")
    messages.append("No RTL/Python functional regressions rerun; use cited original evidence.")
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(messages) + "\n")
    print("\n".join(messages))


if __name__ == "__main__":
    main()
