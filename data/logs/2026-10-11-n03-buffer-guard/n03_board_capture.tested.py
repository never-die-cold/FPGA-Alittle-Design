"""Capture a full BGR frame while PYNQ base HDMI-out mirrors HDMI-in."""

import asyncio
import hashlib
import os
import signal
import time
import uuid
from contextlib import ExitStack
from pathlib import Path

import cv2
import numpy as np
from pynq import Overlay
from pynq.lib.video import PIXEL_BGR


BASE_BIT = Path("/usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/overlays/base/base.bit")
OUTPUT = Path("/home/xilinx/vision_m2") / ("n03-base-" + uuid.uuid4().hex + ".png")

INPUT_ONLY = os.environ.get("N03_CAPTURE_ONLY") == "1"



def release_frame(frame):
    # PYNQ 3.1 can munmap a cached pointer on the destructor's second call.
    cached = bool(getattr(frame, "pointer", None)) and getattr(frame, "return_to", None) is not None
    frame.freebuffer()
    if cached:
        frame.freed = True


def close_port(port, name):
    port.close()
    print("CLEANUP:", name, "closed", flush=True)


def timed_out(signum, frame):
    raise TimeoutError("N03 timeout; closing video pipelines")


async def main():
    if not BASE_BIT.is_file() or OUTPUT.exists():
        raise RuntimeError("base.bit missing or capture output already exists")
    signal.signal(signal.SIGTERM, timed_out)
    print("PHASE: loading PYNQ base overlay", flush=True)
    base = Overlay(str(BASE_BIT))
    print("PHASE: base loaded; cached-frame release guard enabled", flush=True)
    hdmi_in, hdmi_out = base.video.hdmi_in, base.video.hdmi_out
    with ExitStack() as cleanup:
        cleanup.callback(close_port, hdmi_in, "HDMI IN")
        if not INPUT_ONLY:
            cleanup.callback(close_port, hdmi_out, "HDMI OUT")
            cleanup.callback(base.video.axi_vdma.readchannel.tie, None)
        hdmi_in.configure(PIXEL_BGR)
        print("MODE:", hdmi_in.mode, "COLOR: BGR", flush=True)
        if (hdmi_in.mode.width, hdmi_in.mode.height, hdmi_in.mode.bits_per_pixel) != (1280, 720, 24):
            raise RuntimeError("unexpected input mode")
        if not INPUT_ONLY:
            hdmi_out.configure(hdmi_in.mode, PIXEL_BGR)
        hdmi_in.start()
        if not INPUT_ONLY:
            hdmi_out.start()
            hdmi_in.tie(hdmi_out)
        print("PHASE:", "INPUT ONLY" if INPUT_ONLY else "HDMI IN/OUT tied", flush=True)
        # The driver may return one buffered stale frame; discard it first.
        time.sleep(2)
        for sample in range(2):
            warmup = await asyncio.wait_for(hdmi_in.readframe_async(), timeout=5)
            try:
                print("WARMUP:", sample, int(warmup.min()), int(warmup.max()), flush=True)
            finally:
                release_frame(warmup)
        start = time.perf_counter()
        frame = await asyncio.wait_for(hdmi_in.readframe_async(), timeout=5)
        try:
            shape, dtype, strides = frame.shape, frame.dtype, frame.strides
            image = np.array(frame, copy=True)
        finally:
            release_frame(frame)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if image.shape != (720, 1280, 3) or image.dtype != np.uint8:
            raise RuntimeError(f"unexpected frame: shape={image.shape} dtype={image.dtype}")
        with OUTPUT.open("xb") as saved:
            ok, encoded = cv2.imencode(".png", image)
            if not ok:
                raise RuntimeError("PNG encode failed")
            saved.write(encoded.tobytes())
        restored = cv2.imread(str(OUTPUT), cv2.IMREAD_UNCHANGED)
        if restored is None or not np.array_equal(image, restored):
            raise RuntimeError("PNG pixels differ from captured frame")
        print("OUTPUT:", OUTPUT, flush=True)
        print("FRAME:", shape, dtype, "strides=", strides, flush=True)
        print("COPY:", image.flags.c_contiguous, "read_ms=", round(elapsed_ms, 3), flush=True)
        print("PIXELS_SHA256:", hashlib.sha256(image.tobytes()).hexdigest(), flush=True)
        print("PNG_SHA256:", hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), flush=True)
        print("PNG_BYTES:", OUTPUT.stat().st_size, flush=True)
        print("PIXEL_RANGE:", int(image.min()), int(image.max()), flush=True)
        if not np.any(image):
            raise RuntimeError("all-zero captured frame; image validity failed")
        for sample in range(6):
            extra = await asyncio.wait_for(hdmi_in.readframe_async(), timeout=5)
            try:
                print("REPEAT:", sample, int(extra.min()), int(extra.max()), flush=True)
            finally:
                release_frame(extra)
        if not INPUT_ONLY:
            print("PHASE: COEXIST_WINDOW 20s; host may capture HDMI OUT", flush=True)
            time.sleep(20)
    print("CLEANUP: COMPLETE", flush=True)
    print("PASS: full BGR copy;", "input-only" if INPUT_ONLY else "HDMI IN/OUT coexist", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
