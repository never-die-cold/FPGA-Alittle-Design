"""Capture one full BGR frame through PYNQ base HDMI-in VDMA."""

import hashlib
import time
from pathlib import Path

import cv2
import numpy as np
from pynq import Overlay
from pynq.lib.video import COLOR_BGR


BASE_BIT = Path("/usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/overlays/base/base.bit")
OUTPUT = Path("/home/xilinx/vision_m2/n03-base-001.png")


def main():
    if not BASE_BIT.is_file() or OUTPUT.exists():
        raise RuntimeError("base.bit missing or capture output already exists")
    print("PHASE: loading PYNQ base overlay", flush=True)
    base = Overlay(str(BASE_BIT))
    hdmi_in = base.video.hdmi_in
    hdmi_in.configure(COLOR_BGR)
    print("MODE:", hdmi_in.mode, "COLOR: BGR", flush=True)
    hdmi_in.start()
    try:
        start = time.perf_counter()
        frame = hdmi_in.readframe()
        try:
            shape, dtype, strides = frame.shape, frame.dtype, frame.strides
            image = np.array(frame, copy=True)
        finally:
            frame.freebuffer()
        elapsed_ms = (time.perf_counter() - start) * 1000
    finally:
        hdmi_in.stop()
    if image.shape != (720, 1280, 3) or image.dtype != np.uint8:
        raise RuntimeError(f"unexpected frame: shape={image.shape} dtype={image.dtype}")
    if not cv2.imwrite(str(OUTPUT), image):
        raise RuntimeError("PNG write failed")
    restored = cv2.imread(str(OUTPUT), cv2.IMREAD_UNCHANGED)
    if restored is None or not np.array_equal(image, restored):
        raise RuntimeError("PNG pixels differ from captured frame")
    print("FRAME:", shape, dtype, "strides=", strides, flush=True)
    print("COPY:", image.flags.c_contiguous, "read_ms=", round(elapsed_ms, 3), flush=True)
    print("PIXELS_SHA256:", hashlib.sha256(image.tobytes()).hexdigest(), flush=True)
    print("PNG_SHA256:", hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), flush=True)
    print("PNG_BYTES:", OUTPUT.stat().st_size, flush=True)
    print("PASS: full BGR frame copied before VDMA buffer release", flush=True)


if __name__ == "__main__":
    main()
