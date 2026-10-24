"""Reproducible checks for the PROVISIONAL manifest, payload and negative manifests."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_payload_manifest import CHANNELS, NAMES, WEIGHT_GROUPS, load_hex, validate


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--network-dir", type=Path, required=True)
args = parser.parse_args()
manifest = json.loads((args.output / "manifest.json").read_text())
payload = (args.output / manifest["payload_file"]).read_bytes()
validate(manifest)
assert manifest["kind"] == "PROVISIONAL" and len(payload) == 36032
assert hashlib.sha256(payload).hexdigest() == manifest["payload_sha256"]
assert f"0x{zlib.crc32(payload):08x}" == manifest["crc32"]
assert (args.output / "payload.bin.sha256").read_bytes().split()[0].decode() == manifest["payload_sha256"]
manifest_text = (args.output / "manifest.json").read_bytes()
assert b"\r\n" not in manifest_text, "manifest must be LF-only on every platform"
assert (args.output / "manifest.json.sha256").read_bytes().split()[0].decode() == hashlib.sha256(manifest_text).hexdigest()

weights = load_hex(args.network_dir / "weights.hex", 128)
sources = {"bias": load_hex(args.network_dir / "bias.hex", 4),
           "multiplier": load_hex(args.network_dir / "multipliers.hex", 4),
           "shift": load_hex(args.network_dir / "shifts.hex", 1)}
expected, cursor = [], 0
for name, count in zip(NAMES, WEIGHT_GROUPS):
    expected.append((name + ".weight", b"".join(weights[cursor:cursor + count]), cursor))
    cursor += count
for parameter in ("bias", "multiplier", "shift"):
    cursor = 0
    for name, count in zip(NAMES, CHANNELS):
        expected.append((name + "." + parameter,
                         b"".join(sources[parameter][cursor:cursor + count]), cursor))
        cursor += count
for tensor, (name, raw, base) in zip(manifest["tensors"], expected):
    assert tensor["name"] == name and tensor["length"] == len(raw) and tensor["bank"]["base"] == base
    assert payload[tensor["offset"]:tensor["offset"] + tensor["length"]] == raw
for left, right in zip(manifest["tensors"], manifest["tensors"][1:]):
    assert not any(payload[left["offset"] + left["length"]:right["offset"]])
assert not any(payload[manifest["tensors"][-1]["offset"] + manifest["tensors"][-1]["length"]:])
for filename in ("manifest.bad-offset.json", "manifest.bad-length.json"):
    try:
        validate(json.loads((args.output / filename).read_text()))
    except ValueError:
        continue
    raise AssertionError(filename + " was accepted")
print("PASS: manifest_v1 20 tensors preserve J02 bytes; SHA256/CRC/padding valid; offset and OOB negatives rejected")
