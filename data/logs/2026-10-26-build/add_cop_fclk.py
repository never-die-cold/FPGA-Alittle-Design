"""Add the missing board-side cop_fclk.py to existing board packages and refresh hashes."""
from pathlib import Path
import hashlib
import shutil

ROOT = Path(r"E:/Projects/FPGA-Alittle-Design")
source = ROOT / "sim/scripts/cop_fclk.py"
if not source.is_file():
    raise SystemExit(f"missing source: {source}")
packages = [
    ROOT / "build/board-package-j02",
    ROOT / "build/board-package-trained",
    ROOT / "build/board-packages/diagnostic",
    ROOT / "build/board-packages/trained",
]
for package in packages:
    if not package.is_dir():
        print(f"SKIP {package} (missing)")
        continue
    destination = package / "payload/tools/cop_fclk.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    files = sorted(str(path.relative_to(package)).replace("\\", "/")
                   for path in package.rglob("*")
                   if path.is_file() and path.name not in ("FILES.txt", "SHA256SUMS"))
    (package / "FILES.txt").write_text("\n".join(files) + "\n", encoding="utf-8")
    lines = [f"{hashlib.sha256((package / name).read_bytes()).hexdigest()}  {name}" for name in files]
    (package / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PATCHED {package} files={len(files)} cop_fclk={hashlib.sha256(source.read_bytes()).hexdigest()}")
