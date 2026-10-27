from pathlib import Path
import hashlib
ROOT = Path(r"E:/Projects/FPGA-Alittle-Design")
for rel in ["build/board-package-j02", "build/board-package-trained", "build/board-packages/diagnostic", "build/board-packages/trained", "build/board-package-edge-fix", "build/board-package-edge-fix-trained"]:
    pkg = ROOT / rel
    if not pkg.is_dir():
        print("SKIP", rel); continue
    bad = []
    count = 0
    for line in (pkg / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, name = line.split("  ", 1)
        count += 1
        actual = hashlib.sha256((pkg / name).read_bytes()).hexdigest()
        if actual != digest: bad.append(name)
    print(f"{rel}: {count - len(bad)}/{count} OK" + (f" BAD={bad}" if bad else ""))
