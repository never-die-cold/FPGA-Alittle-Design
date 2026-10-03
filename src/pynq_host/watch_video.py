#!/usr/bin/env python3
"""watch_video —— 板端视频在位监视器（上板诊断用）

周期性 commit（短超时）探测帧首确认：能确认=VIDEO_OK（视频在位）；
超时=NO_VIDEO（dvi2rgb 未锁定/无源）；busy=BUSY。输出带相对时间戳。
用法（root）: python3 watch_video.py [时长秒，默认120]
"""
import sys
import time

from vision_regs import VisionRegs

BASE = 0x40000000
DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0

v = VisionRegs(base=BASE)
t0 = time.monotonic()
last = None
while time.monotonic() - t0 < DURATION:
    rel = time.monotonic() - t0
    try:
        cfg = v.commit(timeout=0.6)
        state = f"VIDEO_OK cfg={cfg}"
    except TimeoutError:
        state = "NO_VIDEO"
    except RuntimeError:
        state = "BUSY"
    if state.split()[0] != last:
        print(f"{rel:7.1f}s {state}", flush=True)
        last = state.split()[0]
    time.sleep(0.4)
print(f"{time.monotonic() - t0:7.1f}s watch done", flush=True)
