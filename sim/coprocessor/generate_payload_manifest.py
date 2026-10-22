"""Package the unchanged J02 diagnostic parameters as a PROVISIONAL v1 payload."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
NAMES = ("conv1", "conv2", "conv3", "conv4", "fc")
CHANNELS = (16, 32, 32, 64, 3)
WEIGHT_GROUPS = (9, 36, 72, 144, 8)
KINDS = {"WEIGHT16", "BIAS32", "MULTIPLIER32", "SHIFT6"}
def load_hex(path, width):
    return [int(line, 16).to_bytes(width, "little")
            for line in path.read_text(encoding="ascii").splitlines() if line]
def validate(manifest):
    required = {"version", "model_id", "kind", "payload_file", "payload_sha256",
                "crc32", "total_bytes", "tensors", "generation_command"}
    if required - manifest.keys() or manifest["version"] != "coprocessor-manifest-v1":
        raise ValueError("manifest header")
    if manifest["kind"] not in ("PROVISIONAL", "RELEASE") or manifest["total_bytes"] != 36032:
        raise ValueError("manifest kind/size")
    previous_end = 0
    for tensor in manifest["tensors"]:
        if set(("name", "offset", "length", "alignment", "bank")) - tensor.keys():
            raise ValueError("tensor fields")
        offset, length = tensor["offset"], tensor["length"]
        if tensor["alignment"] != 64 or offset % 64 or length <= 0:
            raise ValueError("tensor alignment/length")
        if offset < previous_end or offset + length > manifest["total_bytes"]:
            raise ValueError("tensor range")
        if tensor["bank"].get("kind") not in KINDS or tensor["bank"].get("base", -1) < 0:
            raise ValueError("tensor bank")
        previous_end = offset + length
    if len(manifest["tensors"]) != 20: raise ValueError("tensor count")
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--network-dir", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents:
        raise ValueError("output must be in repository")
    output.mkdir(parents=True, exist_ok=True)
    network = args.network_dir.resolve() if args.network_dir else output / "j02-network"
    if args.network_dir is None:
        subprocess.run([sys.executable, str(ROOT / "sim/coprocessor/generate_network_vectors.py"),
                        "--output", str(network)], check=True)
    weights = load_hex(network / "weights.hex", 128)
    sources = {"bias": load_hex(network / "bias.hex", 4),
               "multiplier": load_hex(network / "multipliers.hex", 4),
               "shift": load_hex(network / "shifts.hex", 1)}
    payload, tensors = bytearray(), []
    def add(name, chunks, kind, base):
        while len(payload) % 64:
            payload.append(0)
        offset = len(payload)
        raw = b"".join(chunks)
        payload.extend(raw)
        tensors.append({"name": name, "offset": offset, "length": len(raw), "alignment": 64,
                        "bank": {"kind": kind, "base": base}})
    cursor = 0
    for name, count in zip(NAMES, WEIGHT_GROUPS):
        add(name + ".weight", weights[cursor:cursor + count], "WEIGHT16", cursor)
        cursor += count
    for parameter, kind in (("bias", "BIAS32"), ("multiplier", "MULTIPLIER32"),
                            ("shift", "SHIFT6")):
        cursor = 0
        for name, count in zip(NAMES, CHANNELS):
            add(name + "." + parameter, sources[parameter][cursor:cursor + count], kind, cursor)
            cursor += count
    while len(payload) % 64:
        payload.append(0)
    payload_path = output / "payload.bin"
    payload_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {"version": "coprocessor-manifest-v1", "model_id": 0x4A303250,
                "kind": "PROVISIONAL", "payload_file": payload_path.name,
                "payload_sha256": digest, "crc32": f"0x{zlib.crc32(payload):08x}",
                "total_bytes": len(payload), "tensors": tensors,
                "generation_command": "bash sim/scripts/run_coprocessor_iverilog.sh manifest_v1"}
    validate(manifest)
    text = json.dumps(manifest, indent=2) + "\n"
    (output / "manifest.json").write_text(text, encoding="utf-8")
    (output / "payload.bin.sha256").write_text(f"{digest}  payload.bin\n", encoding="ascii")
    (output / "manifest.json.sha256").write_text(
        f"{hashlib.sha256(text.encode()).hexdigest()}  manifest.json\n", encoding="ascii")
    for filename, mutate in (("manifest.bad-offset.json", lambda m: m["tensors"][1].update(offset=1)),
                             ("manifest.bad-length.json", lambda m: m["tensors"][-1].update(length=36033))):
        bad = copy.deepcopy(manifest); mutate(bad)
        (output / filename).write_text(json.dumps(bad, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: manifest_v1 PROVISIONAL payload bytes={len(payload)} sha256={digest} crc32={manifest['crc32']}")


if __name__ == "__main__":
    main()
