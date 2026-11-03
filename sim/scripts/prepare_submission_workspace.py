"""Restore original dependency paths in an extracted official-layout code package."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = json.loads((ROOT / "build/submission/manifest.json").read_text(encoding="utf-8"))
    pending = []
    for row in manifest["files"]:
        old = row.get("original_path")
        if not old or old == row["path"] or old == "README.md":
            continue
        source, target = (ROOT / row["path"]).resolve(), (ROOT / old).resolve()
        if not source.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
            raise ValueError("dependency path escapes extracted package")
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("packaged dependency changed: " + row["path"])
        if target.exists():
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("refusing to replace changed file: " + old)
        else:
            pending.append((source, target))
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print(f"PASS: original dependency paths ready; copied {len(pending)} files; source unchanged")


if __name__ == "__main__":
    main()
