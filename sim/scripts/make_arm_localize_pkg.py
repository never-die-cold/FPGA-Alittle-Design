#!/usr/bin/env python3
"""在仓库 sim/build 内组装标准库便携包，显式白名单不包含 SSH 私钥或构建产物。"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build(archive):
    archive = Path(archive).resolve()
    if not archive.is_relative_to(ROOT / "sim/build"):
        raise ValueError("package archive must stay inside repository sim/build")
    files = {name: ROOT / "src/pynq_host" / name for name in
             ("arm_localize.py", "arm_localize_selftest.py", "arm_localize_bench.py")}
    files.update({"reference.py": ROOT / "data/golden/vision/localize/reference.py",
                  "two_targets.json": ROOT / "data/evidence/2026-10-03-arm-localize-baseline/two_targets.json",
                  "README.md": ROOT / "docs/arm-localize-runbook.md"})
    for source in files.values():
        if not source.is_file():
            raise ValueError(f"missing package source: {source}")
    archive.parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="arm-localize-package-", dir=archive.parent))
    for name, source in files.items():
        shutil.copyfile(source, folder / name)
    manifest = {"schema_version": 1, "base_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in files}}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with tarfile.open(archive, "w:gz") as bundle:
        for name in (*files, "manifest.json"):
            info = bundle.gettarinfo(str(folder / name), arcname="arm_localize/" + name)
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
            info.pax_headers = {}
            with (folder / name).open("rb") as stream:
                bundle.addfile(info, stream)
    print(f"PASS: ARM portable package {archive}")
    return folder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "sim/build/arm-localize-package.tar.gz")
    try:
        build(parser.parse_args().archive)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: package {exc}", file=sys.stderr)
        sys.exit(1)
