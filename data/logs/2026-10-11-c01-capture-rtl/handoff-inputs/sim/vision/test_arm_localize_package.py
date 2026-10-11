"""便携隔离执行、缺文件/篡改门禁、原始性能样本；所有产物留在仓库 sim/build。"""
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sim/scripts"))
from make_arm_localize_pkg import build

archive = ROOT / "sim/build/arm-localize-package-test.tar.gz"
folder = build(archive)
with tarfile.open(archive) as bundle:
    assert len(bundle.getnames()) == 7
    assert all(name.startswith("arm_localize/") for name in bundle.getnames())
    assert not any("id_ed25519" in name for name in bundle.getnames())
command = [sys.executable, "-I", "-B", str(folder / "arm_localize_selftest.py")]
process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
assert process.returncode == 0 and process.stdout.startswith("PASS:"), process.stderr
cli = subprocess.run([sys.executable, "-I", "-B", str(folder / "arm_localize.py"),
                      "two_targets.json", "cli.json"], cwd=folder, capture_output=True, text=True)
assert cli.returncode == 0 and cli.stdout.startswith("PASS:"), cli.stderr
reference = folder / "reference.py"
hidden = folder / "reference.hidden"
reference.rename(hidden)
try:
    rejected = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert rejected.returncode == 1 and "missing or changed: reference.py" in rejected.stderr
finally:
    hidden.rename(reference)
fixture = folder / "two_targets.json"
original = fixture.read_bytes()
fixture.write_bytes(original + b" ")
try:
    rejected = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert rejected.returncode == 1 and "missing or changed: two_targets.json" in rejected.stderr
finally:
    fixture.write_bytes(original)
process = subprocess.run([sys.executable, "-I", "-B", str(folder / "arm_localize_bench.py"),
                          "--out", str((folder / "benchmark-test").relative_to(ROOT)), "--cases", "tiny",
                          "--warmup", "1", "--repeats", "2"], cwd=ROOT, capture_output=True, text=True)
assert process.returncode == 0 and "PASS: synthetic benchmark" in process.stdout, process.stderr
report = json.loads((folder / "benchmark-test/summary.json").read_text())
case = report["cases"][0]
assert report["warmup"] == 1 and report["repeats"] == 2 and case["targets"] == 2
assert len(case["samples"]) == 2 and case["stats_ms"]["total_call"]["median"] > 0
assert all((folder / "benchmark-test" / s["result"]).is_file() for s in case["samples"])
print("PASS: isolated portable package, missing/tampered file gate and retained benchmark samples")
