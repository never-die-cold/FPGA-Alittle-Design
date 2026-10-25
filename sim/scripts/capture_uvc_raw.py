#!/usr/bin/env python3
"""Capture lossless BGR evidence from the named USB Video DirectShow device."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--save-all", action="store_true",
                        help="save and verify every frame, with per-frame pixel hashes")
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be positive")
    repo = Path(__file__).resolve().parents[2]
    output = args.output_dir.resolve()
    if repo not in output.parents or output.exists():
        parser.error("output must be a new directory inside the repository")
    listing = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(Path(__file__).with_name("list_dshow_video.ps1"))],
        text=True, capture_output=True, check=True,
    )
    matches = [int(line.split("\t", 1)[0]) for line in listing.stdout.splitlines()
               if line.split("\t", 1)[-1] == "USB Video"]
    if len(matches) != 1:
        raise RuntimeError(f"USB Video enumeration was ambiguous: {listing.stdout!r}")
    index = matches[0]
    output.mkdir(parents=True)
    (output / "devices.txt").write_text(listing.stdout, encoding="utf-8")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"USB Video at DirectShow index {index} did not open")
    frame = None
    read_ms = []
    frame_records = []
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        mode = {"width": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                "height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                "fps_reported": cap.get(cv2.CAP_PROP_FPS),
                "fourcc": fourcc.to_bytes(4, "little").decode("ascii", "replace")}
        capture_started = time.perf_counter()
        for count in range(args.frames):
            started = time.perf_counter()
            ok, frame = cap.read()
            read_ms.append(round((time.perf_counter() - started) * 1000, 3))
            if not ok:
                raise RuntimeError(f"USB Video read failed at frame {count + 1}")
            if frame.shape != (720, 1280, 3) or frame.dtype != np.uint8:
                raise RuntimeError(f"unexpected frame {count + 1}: {frame.shape}/{frame.dtype}")
            if args.save_all:
                frame_path = output / f"frame-{count + 1:03d}.png"
                if not cv2.imwrite(str(frame_path), frame):
                    raise RuntimeError(f"could not save {frame_path}")
                decoded_frame = cv2.imread(str(frame_path), cv2.IMREAD_UNCHANGED)
                if decoded_frame is None or not np.array_equal(frame, decoded_frame):
                    raise RuntimeError(f"pixel roundtrip failed: {frame_path}")
                frame_records.append({
                    "index": count + 1, "path": frame_path.name,
                    "elapsed_s": round(time.perf_counter() - capture_started, 6),
                    "pixels_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                    "png_sha256": hashlib.sha256(frame_path.read_bytes()).hexdigest(),
                })
        capture_elapsed_s = round(time.perf_counter() - capture_started, 3)
    finally:
        cap.release()
    if frame is None or frame.shape != (720, 1280, 3) or frame.dtype != np.uint8:
        raise RuntimeError(f"unexpected frame shape/dtype: {getattr(frame, 'shape', None)} / "
                           f"{getattr(frame, 'dtype', None)}")
    png = output / "raw.png"
    if not cv2.imwrite(str(png), frame):
        raise RuntimeError("could not save raw PNG")
    decoded = cv2.imread(str(png), cv2.IMREAD_UNCHANGED)
    if decoded is None or not np.array_equal(frame, decoded):
        raise RuntimeError("saved PNG does not decode to original BGR pixels")
    record = {"source": "USB Video UVC; no board check association",
              "device_index": index, "frames_read": args.frames,
              "shape": list(frame.shape), "dtype": str(frame.dtype), "mode": mode,
              "read_ms": read_ms, "capture_elapsed_s": capture_elapsed_s,
              "channel_order": "BGR", "saved_frames": frame_records,
              "save_all": args.save_all,
              "read_calls_per_second": round(args.frames / capture_elapsed_s, 2),
              "pixels_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
              "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest()}
    (output / "metadata.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: USB Video index={index} frames={args.frames} BGR={frame.shape} "
          f"PNG={png} SHA256={record['png_sha256']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise
