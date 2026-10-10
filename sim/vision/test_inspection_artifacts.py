"""Persistent reuse rejects altered evidence and conflicting request content."""
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from inspection_artifacts import digest, save_bytes, load_existing


def main():
    build = ROOT / "sim/build/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as directory:
        folder = Path(directory)
        artifact = save_bytes(folder, "source.bin", b"frame")
        result = {"mode": "FILE_REPLAY", "request_fingerprint": "same", "artifacts": [artifact]}
        raw = json.dumps(result).encode()
        (folder / "result.json").write_bytes(raw)
        (folder / "result.sha256").write_text(digest(raw), encoding="ascii")
        assert load_existing(folder, "same") == result
        for fingerprint, content in (("different", b"frame"), ("same", b"tampered")):
            (folder / "source.bin").write_bytes(content)
            try:
                load_existing(folder, fingerprint)
            except ValueError:
                continue
            raise AssertionError("conflicting request or tampered artifact accepted")
    print("PASS: persistent replay reuse and input/artifact conflict rejection")


if __name__ == "__main__":
    main()
