"""Check a complete FP32 reference package using NumPy only (no torch)."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve()
SOURCE = HERE.parents[2] / "src/pynq_host"
sys.path.insert(0, str(SOURCE if SOURCE.is_dir() else HERE.parent))
from numpy_reference import reference_trace, RTOL, ATOL
from model_audit import audit_layers
from reference_tensors import read_tensor, sha256


def check_package(folder):
    folder = Path(folder).resolve()
    raw = (folder / "manifest.json").read_bytes()
    if sha256(raw) != (folder / "manifest.sha256").read_text(encoding="ascii").strip():
        raise ValueError("reference manifest hash mismatch")
    manifest = json.loads(raw)
    if (manifest.get("schema_version") != 1 or manifest.get("mode") != "FP32_SOFTWARE_REFERENCE"
            or manifest.get("hardware_connected") is not False or manifest.get("truth_labels") is not None
            or manifest.get("rtol") != RTOL or manifest.get("atol") != ATOL
            or manifest["model"]["precision"] != "FP32"
            or manifest["model"]["classes"] != ["bolt", "nut", "washer"]):
        raise ValueError("invalid software reference metadata")
    required = {"tools/" + name + ".py" for name in ("numpy_reference", "reference_tensors", "model_audit", "check_model_reference")}
    if set(manifest["tools"]) != required:
        raise ValueError("incomplete reference tools")
    for name, expected in manifest["tools"].items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder) or sha256(path.read_bytes()) != expected:
            raise ValueError("reference tool hash/path mismatch")
    tensors = {name: read_tensor(folder, record) for name, record in manifest["tensors"].items()}
    if any(name != record["name"] for name, record in manifest["tensors"].items()):
        raise ValueError("reference tensor identity mismatch")
    layers = [{key: tensors[value] if key in ("weight", "bias") else value
               for key, value in layer.items()} for layer in manifest["layers"]]
    if [layer["name"] for layer in layers] != ["conv1", "conv2", "conv3", "conv4", "gap", "logits"]:
        raise ValueError("invalid reference layer names")
    if audit_layers(layers) != manifest["audit"]:
        raise ValueError("reference audit mismatch")
    maximum = 0.0
    if len(manifest["cases"]) != 3 or {case["name"] for case in manifest["cases"]} != {"zero", "seed2026", "stripes"}:
        raise ValueError("invalid reference cases")
    for case in manifest["cases"]:
        actual = reference_trace(tensors[case["pixels"]], layers)
        if set(actual) != set(case["expected"]):
            raise ValueError("incomplete reference stages")
        for stage, key in case["expected"].items():
            np.testing.assert_allclose(actual[stage], tensors[key], rtol=RTOL, atol=ATOL)
            maximum = max(maximum, float(np.max(np.abs(actual[stage] - tensors[key]))))
        predicted = manifest["model"]["classes"][int(actual["logits"].argmax())]
        if predicted != case["predicted_class"]:
            raise ValueError("reference class mismatch")
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        maximum = check_package(args.package)
    except (OSError, ValueError, KeyError, AssertionError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    assert "torch" not in sys.modules, "portable checker imported torch"
    print(f"PASS: NumPy-only FP32 reference: 3 cases x 7 tensors; max_abs_error={maximum:.9g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
