#!/usr/bin/env python3
"""Capture the selected USB HDMI device exclusively; save actual frame evidence.

The source index must be confirmed against DirectShow device enumeration.
This script does no image processing or diagnostic-mode simulation.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opencv-dir", type=Path)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()
    if args.frames < 2:
        parser.error("frames must be >=2")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dll = None
    if args.opencv_dir:
        lib = args.opencv_dir.resolve()
        sys.path.insert(0, str(lib))
        if os.name == "nt":
            dll = os.add_dll_directory(str(lib))
    import cv2
    cap = cv2.VideoCapture(args.source, cv2.CAP_DSHOW)
    result = {"source": args.source, "opened": cap.isOpened(), "received": 0,
              "black_frames": 0, "min_luma_std": None}
    try:
        if not cap.isOpened():
            raise RuntimeError("selected USB device unavailable; close other capture programs")
        result["settings"] = [cap.set(prop, value) for prop, value in (
            (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")),
            (cv2.CAP_PROP_FRAME_WIDTH, 1280), (cv2.CAP_PROP_FRAME_HEIGHT, 720), (cv2.CAP_PROP_FPS, 30))]
        result["actual"] = {"width": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                            "height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT), "fps": cap.get(cv2.CAP_PROP_FPS)}
        # Drain startup buffers after a mode change; do not preserve stale frames.
        for _ in range(30):
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("USB frame unavailable")
        started = time.monotonic()
        first = None
        for _ in range(args.frames):
            ok, frame = cap.read()
            if not ok or frame.shape[:2] != (720, 1280):
                raise RuntimeError("USB 720p frame unavailable")
            if first is None:
                first = frame.copy()
            result["received"] += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            contrast = float(gray.std())
            result["min_luma_std"] = contrast if result["min_luma_std"] is None else min(result["min_luma_std"], contrast)
            result["black_frames"] += int(not frame.any())
        result["elapsed_s"] = time.monotonic() - started
        args.output.parent.mkdir(parents=True, exist_ok=True)
        for label, picture in (("first", first), ("last", frame)):
            if not cv2.imwrite(str(args.output.with_name(args.output.name + f"-{label}.png")), picture):
                raise RuntimeError("PNG write failed")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result.update(mean=float(gray.mean()), std=float(gray.std()),
                      channel_difference=float(abs(frame[:, :, 0].astype("int16") - frame[:, :, 2]).mean()),
                      laplacian_variance=float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        print(f"PASS: USB source={args.source} 1280x720 received={result['received']}")
    except RuntimeError as error:
        result["error"] = str(error)
        print(f"FAIL: {error}")
    finally:
        cap.release()
        args.output.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if dll:
            dll.close()
    print(json.dumps(result))
    return int("error" in result)


if __name__ == "__main__":
    raise SystemExit(main())
