"""Verify and recover a board PNG from recorded serial base64 output."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

import cv2
import numpy as np


def field(text, name):
    match = re.search(r"(?m)^" + re.escape(name) + r": (.+)\r?$", text)
    if not match:
        raise ValueError("missing board field: " + name)
    return match.group(1).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board-log", type=Path, required=True)
    parser.add_argument("--transfer-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if root not in output.parents or output.exists():
        raise ValueError("output must be a new file inside the repository")
    board = args.board_log.read_text(encoding="utf-8")
    transfer = args.transfer_log.read_text(encoding="utf-8")
    for record in (board, transfer):
        if not re.search(r"(?m)^HOST_EXIT_CODE=0\r?$", record):
            raise ValueError("recorded command did not complete successfully")
    match = re.search(r"(?m)^__N03_PNG_BEGIN__\r?\n([A-Za-z0-9+/=\r\n]+)^__N03_PNG_END__\r?$", transfer)
    if not match:
        raise ValueError("missing complete base64 transfer markers")
    encoded = "".join(match.group(1).split())
    png = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(png).hexdigest()
    if len(png) != int(field(board, "PNG_BYTES")) or digest != field(board, "PNG_SHA256"):
        raise ValueError("transferred PNG differs from board bytes/hash")
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None or image.shape != (720, 1280, 3) or image.dtype != np.uint8:
        raise ValueError("unexpected decoded frame shape or type")
    pixel_digest = hashlib.sha256(image.tobytes()).hexdigest()
    if pixel_digest != field(board, "PIXELS_SHA256") or not np.any(image):
        raise ValueError("decoded pixels differ or frame is all zero")
    with output.open("xb") as saved:
        saved.write(png)
    metadata = {"source": field(board, "OUTPUT"), "shape": list(image.shape),
        "dtype": str(image.dtype), "png_bytes": len(png), "png_sha256": digest,
        "pixels_sha256": pixel_digest, "pixel_range": [int(image.min()), int(image.max())],
        "bgr_mean": image.mean(axis=(0, 1)).tolist(),
        "limit": "hash equality proves transport; temporal/color validity needs inspection"}
    with output.with_suffix(".metadata.json").open("x", encoding="utf-8") as saved:
        saved.write(json.dumps(metadata, indent=2) + "\n")
    print("PASS: board PNG and pixel hashes verified;", output)


if __name__ == "__main__":
    main()
