"""Package the current source tree and selected filming dependencies, without Git history."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from submission_layout import arrange

ROOT = Path(__file__).resolve().parents[2]
EXTRAS = (
    "sim/build/cnn-r9-live-20261103",
    "sim/build/cnn-r9-board-package",
    "sim/build/cnn-r9-board-vectors",
    "sim/build/cnn-r8-live-20261103/fp32.pt",
    "sim/build/cnn-r8-live-20261103/training.json",
    "sim/build/model-speed-annotations-r8.json",
    "sim/build/model-speed-baseline-r6",
    "sim/build/model-speed-final-r9",
    "sim/build/model-speed-regression-r9-local",
    "sim/build/onboard-final/board-rounds-r1/check-000008/capture.png",
    "sim/build/r9-hardware-golden.json",
    "sim/build/filming-guard-rounds",
    "sim/build/filming-guard-rounds.log",
    "sim/build/filming-after-boot-check",
    "sim/build/filming-after-boot-check.log",
    "sim/build/filming-reboot-resume-r2",
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--layout", choices=("official", "snapshot"), default="official")
    args = parser.parse_args()
    filename = "edgesight-code-20261103.zip" if args.layout == "official" else "FPGA-Alittle-Design-20261103-r9.zip"
    output = (args.output or ROOT / "build/artifacts" / filename).resolve()
    if not output.is_relative_to(ROOT / "build/artifacts"):
        parser.error("output must stay under build/artifacts")
    if output.exists():
        parser.error("output already exists; choose another name")
    names = set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0"))
    names = {p for p in names if p and not p.startswith("docs/tech-report/latex/") and (ROOT / p).is_file()}
    for name in EXTRAS:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(name)
        names.update(p.relative_to(ROOT).as_posix() for p in (path.rglob("*") if path.is_dir() else [path]) if p.is_file())
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": git("rev-parse", "HEAD").decode().strip(),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD").decode().strip(),
        "snapshot": "CURRENT_WORKTREE_INCLUDING_UNCOMMITTED_SOURCE",
        "worktree_status": git("status", "--short").decode("utf-8"),
        "explicit_ignored_dependencies": EXTRAS,
        "excluded": [".git", "caches and unselected ignored build outputs", "others", "docs/tech-report/latex (old draft)", "teammate-local final report and poster (unavailable)"],
        "readme": "docs/runbooks/submission-package-2026-11-03.md",
    }
    entries = {p: (ROOT / p).read_bytes() for p in sorted(names)}
    origins = {p: p for p in entries}
    metadata_root, prefix = "SUBMISSION/", "FPGA-Alittle-Design/"
    if args.layout == "official":
        entries, origins, excluded = arrange(entries)
        metadata.update(layout="AMD_OPEN_TOPIC_3.3.5.4", excluded_files=excluded, readme="README.md")
        metadata_root, prefix = "build/submission/", "edgesight/"
    entries[metadata_root + "worktree.patch"] = git("diff", "--binary", "HEAD", "--")
    metadata["files"] = [{"path": p, "original_path": origins.get(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} for p, b in entries.items()]
    entries[metadata_root + "manifest.json"] = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in entries.items():
            archive.writestr(prefix + name, data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None, "CRC check failed"
        assert len(archive.namelist()) == len(set(archive.namelist())) == len(entries)
        for name, data in entries.items():
            assert hashlib.sha256(archive.read(prefix + name)).digest() == hashlib.sha256(data).digest(), name
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8", newline="\n")
    result = {"zip": str(output), "files": len(entries), "bytes": output.stat().st_size, "sha256": digest, "verification": "PASS: ZIP CRC, unique paths, every entry SHA256"}
    output.with_suffix(".verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
