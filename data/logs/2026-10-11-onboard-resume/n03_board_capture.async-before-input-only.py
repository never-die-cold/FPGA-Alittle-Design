"""Capture a full BGR frame while PYNQ base HDMI-out mirrors HDMI-in."""

import asyncio
import hashlib
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


def timed_out(signum, frame):
    raise TimeoutError("N03 timeout; closing video pipelines")


async def main():
    if not BASE_BIT.is_file() or OUTPUT.exists():
        raise RuntimeError("base.bit missing or capture output already exists")
    signal.signal(signal.SIGTERM, timed_out)
    print("PHASE: loading PYNQ base overlay", flush=True)
    base = Overlay(str(BASE_BIT))
    print("PHASE: base loaded", flush=True)
    hdmi_in, hdmi_out = base.video.hdmi_in, base.video.hdmi_out
    with ExitStack() as cleanup:
        cleanup.callback(hdmi_in.close)
        cleanup.callback(hdmi_out.close)
        cleanup.callback(base.video.axi_vdma.readchannel.tie, None)
        hdmi_in.configure(PIXEL_BGR)
        print("MODE:", hdmi_in.mode, "COLOR: BGR", flush=True)
        if (hdmi_in.mode.width, hdmi_in.mode.height, hdmi_in.mode.bits_per_pixel) != (1280, 720, 24):
            raise RuntimeError("unexpected input mode")
        hdmi_out.configure(hdmi_in.mode, PIXEL_BGR)
        hdmi_in.start()
        hdmi_out.start()
        hdmi_in.tie(hdmi_out)
        print("PHASE: HDMI IN/OUT tied; capturing", flush=True)
        # The driver may return one buffered stale frame; discard it first.
        time.sleep(2)
        for sample in range(8):
            warmup = await asyncio.wait_for(hdmi_in.readframe_async(), timeout=5)
            try:
                print("WARMUP:", sample, int(warmup.min()), int(warmup.max()), flush=True)
            finally:
                warmup.freebuffer()
        start = time.perf_counter()
        frame = await asyncio.wait_for(hdmi_in.readframe_async(), timeout=5)
        try:
            shape, dtype, strides = frame.shape, frame.dtype, frame.strides
            image = np.array(frame, copy=True)
        finally:
            frame.freebuffer()
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
        print("PHASE: COEXIST_WINDOW 20s; host may capture HDMI OUT", flush=True)
        time.sleep(20)
    if not np.any(image):
        raise RuntimeError("all-zero captured frame; image validity failed")
    print("PASS: full BGR copy and HDMI IN/OUT lifecycle complete", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
