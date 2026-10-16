"""Lossless software tensor files: uint8 pixels or IEEE754 FP32 words."""
import hashlib
import io
from pathlib import Path
import numpy as np


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def write_tensor(folder, name, value, layout):
    if Path(name).name != name or value.dtype not in (np.uint8, np.float32) or not np.isfinite(value).all():
        raise ValueError("invalid reference tensor")
    dtype, bits = ("uint8", 8) if value.dtype == np.uint8 else ("float32", 32)
    pixels = np.ascontiguousarray(value, dtype="u1" if bits == 8 else "<f4")
    stream = io.BytesIO()
    np.save(stream, pixels, allow_pickle=False)
    words = pixels.view("u1" if bits == 8 else "<u4").ravel()
    raw_hex = "".join(f"{int(word):0{bits // 4}x}\n" for word in words).encode("ascii")
    record = {"name": name, "shape": list(value.shape), "dtype": dtype, "layout": layout,
              "word_bits": bits, "byte_order": "little", "element_order": "C"}
    for suffix, raw in (("npy", stream.getvalue()), ("hex", raw_hex)):
        filename = name + "." + suffix
        (folder / filename).write_bytes(raw)
        record[suffix], record[suffix + "_sha256"] = filename, sha256(raw)
    return record


def read_tensor(folder, record):
    raws = {}
    for suffix in ("npy", "hex"):
        filename = record[suffix]
        path = (folder / filename).resolve()
        if Path(filename).name != filename or not path.is_relative_to(folder.resolve()):
            raise ValueError("reference tensor path escapes package")
        raw = path.read_bytes()
        if sha256(raw) != record[suffix + "_sha256"]:
            raise ValueError("reference tensor hash mismatch")
        raws[suffix] = raw
    value = np.load(io.BytesIO(raws["npy"]), allow_pickle=False)
    dtype = {"uint8": (np.dtype("u1"), 8), "float32": (np.dtype("<f4"), 32)}.get(record["dtype"])
    if (dtype is None or record["word_bits"] != dtype[1] or record["byte_order"] != "little"
            or record["element_order"] != "C" or value.dtype != dtype[0]
            or list(value.shape) != record["shape"] or not np.isfinite(value).all()):
        raise ValueError("reference tensor format mismatch")
    lines = raws["hex"].decode("ascii").splitlines()
    if len(lines) != value.size or any(len(line) != dtype[1] // 4 for line in lines):
        raise ValueError("reference hex extent mismatch")
    words = np.array([int(line, 16) for line in lines], dtype=np.uint64)
    expected = value.view("u1" if dtype[1] == 8 else "<u4").ravel()
    if not np.array_equal(words, expected):
        raise ValueError("reference hex/NPY bits mismatch")
    return value
