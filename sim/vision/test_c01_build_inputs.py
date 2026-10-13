"""Check exact evidence recovery and rejection without touching real build inputs."""
import hashlib
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sim/scripts"))
from audit_c01_build_inputs import audit


def rejected(call, error=ValueError):
    try:
        call()
    except error:
        return
    raise AssertionError("invalid evidence accepted")


def main():
    folder = ROOT / "sim/build/c01-input-audit-tests" / uuid.uuid4().hex
    current, archive = folder / "current", folder / "archive"
    current.mkdir(parents=True)
    (archive / "inputs").mkdir(parents=True)
    original = b"first\r\nsecond\r\n"
    saved = archive / "inputs/probe.bin"
    saved.write_bytes(original.replace(b"\r\n", b"\n"))
    (current / "probe.bin").write_bytes(original)
    entry = {"path": "probe.bin", "bytes": len(original),
             "sha256": hashlib.sha256(original).hexdigest()}
    manifest = archive / "manifest.json"
    manifest.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
    rejected(lambda: audit(manifest, current))
    recovery = current / "recovered"
    report = audit(manifest, current, recovery)
    assert report["exact_crlf_recovered"] == ["probe.bin"]
    assert (recovery / "inputs/probe.bin").read_bytes() == original
    assert (recovery / "manifest.json").read_bytes() == manifest.read_bytes()
    strict = audit(recovery / "manifest.json", current)
    assert strict["retained_inputs_verified"] == 1 and strict["exact_crlf_recovered"] == []
    assert strict["current_matches"] == ["probe.bin"]
    rejected(lambda: audit(manifest, current, recovery), FileExistsError)
    saved.write_bytes(b"tampered\n")
    rejected(lambda: audit(manifest, current, current / "tampered-recovery"))
    assert saved.read_bytes() == b"tampered\n", "audit must not rewrite old evidence"
    (current / "probe.bin").write_bytes(b"current changed")
    assert audit(recovery / "manifest.json", current)["current_changed"] == ["probe.bin"]
    for entries in ([{**entry, "path": "../escape.bin"}], [entry, entry]):
        manifest.write_text(json.dumps({"files": entries}), encoding="utf-8")
        saved.write_bytes(original)
        rejected(lambda: audit(manifest, current))
    rejected(lambda: audit(recovery / "manifest.json", current, folder / "outside-current"))
    print("PASS: C01 exact CRLF recovery, strict recheck, tamper/path/duplicate/overwrite rejection and drift")


if __name__ == "__main__":
    main()
