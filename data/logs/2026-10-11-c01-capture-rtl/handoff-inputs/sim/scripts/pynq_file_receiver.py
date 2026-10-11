"""Receive one gzip/base64 file over a raw UART; never overwrite a board file."""
import base64
import gzip
import hashlib
import sys
from pathlib import Path


def receive(encoded_size, raw_size, sha256, destination, token, stream=None):
    if not 0 < encoded_size <= 16 * 1024 * 1024 or not 0 <= raw_size <= 16 * 1024 * 1024:
        raise ValueError("transfer size out of range")
    stream = sys.stdin.buffer if stream is None else stream
    print(token + "_READY", flush=True)
    chunks = []
    remaining = encoded_size
    while remaining:
        chunk = stream.read(min(65536, remaining))
        if not chunk:
            raise ValueError("short UART payload")
        chunks.append(chunk)
        remaining -= len(chunk)
    encoded = b"".join(chunks)
    data = gzip.decompress(base64.b64decode(encoded, validate=True))
    if len(data) != raw_size or hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("file length/SHA256 mismatch")
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        if output.write(data) != len(data):
            raise OSError("short file write")
    if hashlib.sha256(target.read_bytes()).hexdigest() != sha256:
        raise OSError("saved file SHA256 mismatch")
    print("PASS: UART file", target, len(data), sha256, flush=True)
