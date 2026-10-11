"""Portable NumPy-only replay, no overwrite and corrupted package rejection."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from reference_package import export_reference
from reference_tensors import sha256, read_tensor, write_tensor
from check_model_reference import check_package


def save_manifest(folder, manifest):
    raw = json.dumps(manifest).encode()
    (folder / "manifest.json").write_bytes(raw)
    (folder / "manifest.sha256").write_text(sha256(raw), encoding="ascii")


def main():
    build = ROOT / "sim/build/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as directory:
        folder = Path(directory) / "package"
        manifest = export_reference(ROOT / "models/cnn-border-fill-best.pt", folder)
        maximum = check_package(folder)
        isolated = subprocess.run([sys.executable, "-I", str(folder / "tools/check_model_reference.py"), str(folder)],
                                  capture_output=True, text=True, timeout=60, cwd=directory)
        assert isolated.returncode == 0, isolated.stdout + isolated.stderr
        print(isolated.stdout.strip())
        try:
            export_reference(ROOT / "models/cnn-border-fill-best.pt", folder)
        except ValueError:
            pass
        else:
            raise AssertionError("existing reference output overwritten")
        source = folder / "tools/numpy_reference.py"
        original = source.read_bytes()
        for change in ("tool", "manifest", "golden"):
            if change == "tool":
                source.write_bytes(original + b"# modified\n")
            elif change == "manifest":
                manifest["audit"]["macs_per_roi"] += 1
                save_manifest(folder, manifest)
            else:
                key = "stripes_logits"
                value = read_tensor(folder, manifest["tensors"][key]).copy()
                value[0] += 1
                manifest["tensors"][key] = write_tensor(folder, key, value, "C")
                save_manifest(folder, manifest)
            try:
                check_package(folder)
            except (ValueError, AssertionError):
                pass
            else:
                raise AssertionError(f"modified {change} accepted")
            source.write_bytes(original)
            if change == "manifest":
                manifest["audit"]["macs_per_roi"] -= 1
            save_manifest(folder, manifest)
    print(f"PASS: reference package isolated replay, overwrite/tool/audit/numerical gates; max_abs_error={maximum:.9g}")


if __name__ == "__main__":
    main()
