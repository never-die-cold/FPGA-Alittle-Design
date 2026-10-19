"""Regenerate diagnostic goldens and verify every manifest SHA256."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "sim/build/coprocessor/manifest-check"
REQUIRED_CONV = {"input.hex", "weights.hex", "expected.hex", "bias.hex",
                 "multipliers.hex", "shifts.hex"}
REQUIRED_NETWORK = {"input.hex", "conv1.hex", "conv2.hex", "conv3.hex",
                    "conv4.hex", "gap.hex", "logits.hex", "result.txt"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(script, name):
    output = BUILD / name
    subprocess.run([sys.executable, str(ROOT / "sim/coprocessor" / script),
                    "--output", str(output)], check=True)
    return output, json.loads((output / "manifest.json").read_text(encoding="utf-8"))


def check_hashes(folder, fingerprints):
    for name, expected in fingerprints.items():
        assert digest(folder / name) == expected, f"SHA256 mismatch: {folder / name}"


def main():
    arithmetic, manifest = generate("generate_arithmetic_vectors.py", "arithmetic")
    assert manifest["kind"] == "C02_DIAGNOSTIC_ARITHMETIC"
    assert set(manifest["files"]) == {"requant", "gap", "logits"}
    for name, record in manifest["files"].items():
        path = arithmetic / f"{name}.txt"
        assert sum(1 for _ in path.open(encoding="ascii")) == record["vectors"]
        check_hashes(arithmetic, {path.name: record["sha256"]})
    assert digest(ROOT / "src/coprocessor/int8_reference.py") == manifest["reference_sha256"]

    convolution, manifest = generate("generate_conv_vectors.py", "convolution")
    assert manifest["kind"] == "C02_OPERATOR_DIAGNOSTIC"
    assert list(manifest["cases"]) == ["padding_tail", "conv1", "conv2", "conv3", "conv4", "fc"]
    for name, record in manifest["cases"].items():
        assert set(record["files_sha256"]) == REQUIRED_CONV
        check_hashes(convolution / name, record["files_sha256"])

    network, manifest = generate("generate_network_vectors.py", "network")
    assert manifest["kind"] == "DIAGNOSTIC_INTEGER_NETWORK_NOT_TRAINED"
    assert set(manifest["model_files_sha256"]) == {"weights.hex", "bias.hex", "multipliers.hex", "shifts.hex"}
    check_hashes(network, manifest["model_files_sha256"])
    for name, record in manifest["cases"].items():
        assert set(record["files_sha256"]) == REQUIRED_NETWORK
        check_hashes(network / name, record["files_sha256"])
    for name, expected in manifest["source_sha256"].items():
        assert digest(ROOT / name) == expected, f"source SHA256 mismatch: {name}"

    target = network / "zero/result.txt"
    original = target.read_bytes()
    target.write_bytes(original + b"tamper")
    assert digest(target) != manifest["cases"]["zero"]["files_sha256"]["result.txt"]
    target.write_bytes(original)
    check_hashes(network / "zero", {"result.txt": manifest["cases"]["zero"]["files_sha256"]["result.txt"]})
    print("PASS: diagnostic manifests cover required files, sources and tamper detection")


if __name__ == "__main__":
    main()
