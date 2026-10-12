"""Offline fault checks for N03; fake video drivers do not prove hardware."""
import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "sim/build/n03-capture-offline"
OUT.mkdir(parents=True, exist_ok=True)
events = []
state = {"mode": "ok"}


class Frame(np.ndarray):
    def freebuffer(self):
        events.append("free")
        self[:] = 0


class Video:
    def __init__(self, name):
        self.name = name
        self.mode = types.SimpleNamespace(width=1280, height=720, bits_per_pixel=24)

    def configure(self, *args):
        if state["mode"] == "configure" and self.name == "in":
            raise ValueError("injected configure failure")

    def start(self):
        events.append(self.name + "-start")

    def close(self):
        events.append(self.name + "-close")

    def tie(self, output):
        events.append("tie")

    async def readframe_async(self):
        if state["mode"] == "timeout":
            await asyncio.Event().wait()
        values = np.zeros((720, 1280, 3), dtype=np.uint8)
        if state["mode"] != "black":
            values[:, :, 1] = 100
            values[0, 0, 2] = 200
        return values.view(Frame)


def untie(output):
    assert output is None
    events.append("untie")


base = types.SimpleNamespace(video=types.SimpleNamespace(hdmi_in=Video("in"),
    hdmi_out=Video("out"), axi_vdma=types.SimpleNamespace(readchannel=types.SimpleNamespace(tie=untie))))
pynq = types.ModuleType("pynq")
pynq.Overlay = lambda path: base
video = types.ModuleType("pynq.lib.video")
video.PIXEL_BGR = object()
sys.modules.update({"pynq": pynq, "pynq.lib": types.ModuleType("pynq.lib"), "pynq.lib.video": video})
spec = importlib.util.spec_from_file_location("n03", ROOT / "sim/scripts/n03_board_capture.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
capture.BASE_BIT = ROOT / "sim/scripts/n03_board_capture.py"
capture.time.sleep = lambda seconds: None
real_wait = asyncio.wait_for
capture.asyncio.wait_for = lambda task, timeout: real_wait(task, timeout=0.01)

for name, error in (("input-only", None), ("ok", None), ("black", RuntimeError), ("timeout", TimeoutError),
                    ("configure", ValueError)):
    capture.INPUT_ONLY = name == "input-only"
    state["mode"] = name
    events.clear()
    capture.OUTPUT = OUT / (name + "-" + capture.uuid.uuid4().hex + ".png")
    try:
        asyncio.run(capture.main())
    except Exception as caught:
        assert error and isinstance(caught, error), (name, caught)
    else:
        assert error is None, name
    if capture.INPUT_ONLY:
        assert events[-1] == "in-close" and "out-start" not in events and "tie" not in events
    else:
        assert events[-3:] == ["untie", "out-close", "in-close"], events
    if name in ("ok", "input-only"):
        saved = cv2.imread(str(capture.OUTPUT))
        assert saved[0, 0, 2] == 200 and saved[1, 1, 1] == 100
        assert events.count("free") == 9
    if name in ("timeout", "configure"):
        assert not capture.OUTPUT.exists()
    print("PASS: offline N03", name, "cleanup and frame ownership")
