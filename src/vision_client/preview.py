"""Windows preview prototype（EdgeSight 应用外壳，HUD v4）。

画面来源：UVC 采集卡（--source）或本机合成场景（--mock）。
- 状态机（D2 触发 / D3 有效性撤框 / D5 重连）在 rounds.py；批次记录与异常事件在 records.py；
- 应用外壳（顶栏/视频视口/指标面板/检测对象列表/RUN 按钮）在 hud.py：静态基座与固定形状
  元素预渲染缓存，每帧仅粘贴 + 动态文本（~6-10ms/帧）；
- 文本由 hud_text.TextEngine（Pillow 真实字体，Inter）渲染。

HUD 设计 v4 定稿与说明：data/logs/2026-10-09-exe-hud-v4/。
MOCK 结果恒标 MOCK ONLY，不代表板上识别（plan.md §3.4）。
"""
import argparse
import sys
import time
import urllib.error
from collections import deque
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pynq_host"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vision_protocol import mock_packet
from rounds import RemoteRounds
from records import AnomalyLog, BatchRecords
from hud_text import TextEngine
from hud import (AMBER, AMBER_DEEP, BUTTON, CYAN, DIM, GREEN, MAIN, RED, Hud)
import cv2
import numpy as np

WINDOW = "EdgeSight Vision Preview"
VIEW_RECT = (24, 88, 1264, 711)  # 视频视口（与 hud.VIEW 同步；selftest 区域断言用）


def mock_frame(packet):
    """合成场景（--mock 演示）：冷灰工作台 + 细网格 + 椭圆"零件"。"""
    frame = np.full((packet["height"], packet["width"], 3), (196, 200, 204), np.uint8)
    for x in range(0, packet["width"], 80):
        cv2.line(frame, (x, 0), (x, packet["height"]), (188, 192, 196), 1)
    for y in range(0, packet["height"], 80):
        cv2.line(frame, (0, y), (packet["width"], y), (188, 192, 196), 1)
    for target in packet["targets"]:
        x0, y0, x1, y1 = target["bbox"]
        cv2.ellipse(frame, ((x0 + x1) // 2, (y0 + y1) // 2),
                    ((x1 - x0) // 2 - 12, (y1 - y0) // 2 - 12), 0, 0, 360,
                    (92, 96, 102), -1, cv2.LINE_AA)
    return frame


def green_pixels(image):
    """绿色目标框像素计数（int16 防 uint8 溢出；供 selftest 与打包断言复用）。"""
    f = image.astype(np.int16)
    return int(((f[:, :, 1] > 150) & (f[:, :, 1] - f[:, :, 0] > 60)
                & (f[:, :, 1] - f[:, :, 2] > 60)).sum())


def clock_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _set_dpi_awareness():
    """声明 DPI 感知：高分屏（如 2880x1800@200%）下按物理像素 1:1 输出，不被系统拉伸/切割。"""
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PerMonitorV2（Win8.1+）
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except (ImportError, AttributeError, OSError):
        pass  # 非 Windows 或不可用：保持默认


def _work_area():
    """主屏工作区（物理像素，已 DPI 感知）。失败时回退 1600x900。"""
    try:
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.right - rect.left, rect.bottom - rect.top
    except (ImportError, AttributeError, OSError):
        pass
    return 1600, 900


class FpsMeter:
    def __init__(self, span=30):
        self.times = deque(maxlen=span)

    def tick(self, now):
        self.times.append(now)

    def value(self):
        if len(self.times) < 2:
            return 0
        span = self.times[-1] - self.times[0]
        return round((len(self.times) - 1) / span) if span > 0 else 0


def demo_state(packet, fps):
    targets = [tuple(t["bbox"]) for t in packet["targets"]]
    return {"badge": ("MOCK ONLY", AMBER),
            "status": ("LOCAL DEMO", MAIN, "SemiBold"),
            "detail": f"{packet['width']} x {packet['height']} | {fps} FPS",
            "clock": clock_text(),
            "cells": [("ROUND", str(packet["check_id"]), MAIN),
                      ("TARGETS", str(len(targets)), MAIN),
                      ("REC", "--", DIM)],
            "fresh": None, "boxes": targets, "list": targets, "button": False}


def uvc_state(shape, fps):
    return {"badge": ("VIDEO ONLY", DIM),
            "status": ("UNASSOCIATED | no board recognition", DIM, "Regular"),
            "detail": f"{shape[1]} x {shape[0]} | {fps} FPS",
            "clock": clock_text(), "cells": None, "fresh": None,
            "boxes": None, "list": None, "button": False}


def endpoint_state(remote, rec_count, current, age, fps, shape):
    rec_val = str(rec_count) if rec_count is not None else "--"
    rec_color = MAIN if rec_count is not None else DIM
    state = {"badge": ("LIVE", GREEN) if remote.mode == "LIVE" else ("MOCK ONLY", AMBER),
             "clock": clock_text(),
             "detail": f"{shape[1]} x {shape[0]} | {fps} FPS | session {remote.session[:8]}",
             "button": True}
    if current:
        targets = [tuple(t["bbox"]) for t in remote.packet["targets"]]
        state.update(status=("STREAMING", MAIN, "SemiBold"),
                     cells=[("ROUND", str(remote.packet["check_id"]), MAIN),
                            ("TARGETS", str(len(targets)), MAIN),
                            ("REC", rec_val, rec_color)],
                     fresh=(max(0.0, 1.0 - age / remote.max_age), CYAN),
                     boxes=targets, list=targets)
    else:
        state.update(status=("WAITING FOR RESULT", AMBER_DEEP, "SemiBold"),
                     cells=[("ROUND", "--", AMBER_DEEP), ("TARGETS", "--", AMBER_DEEP),
                            ("REC", rec_val, rec_color)],
                     fresh=(1.0, RED), boxes=None, list=[])
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--replay", type=Path, help="checked file inspection result.json (offline snapshot)")
    parser.add_argument("--endpoint", help="result service URL, e.g. http://127.0.0.1:8765")
    parser.add_argument("--source", type=int, default=0, help="UVC capture device index")
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--save", type=Path)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--max-age", type=float, default=1.0, help="D3 result age window (s)")
    parser.add_argument("--interval", type=float, default=0.5,
                        help="auto check trigger period (s); must be < --max-age")
    parser.add_argument("--records-dir", type=Path,
                        help="batch record dir (D8-D10): manual-triggered current rounds only")
    parser.add_argument("--trigger-frame", type=int, default=0,
                        help="self-check hook: simulate one manual trigger (c) at frame N")
    args = parser.parse_args()
    _set_dpi_awareness()
    if args.replay:
        if args.mock or args.endpoint or args.records_dir or args.selftest or args.trigger_frame:
            parser.error("--replay cannot combine with mock, endpoint, records, selftest or trigger")
        from replay_viewer import show_replay
        show_replay(args, _work_area)
        return
    if args.selftest:
        engine = TextEngine()
        p = mock_packet("selftest", 1, 0, 1)
        canvas = Hud(engine).render(mock_frame(p), demo_state(p, 30))
        assert canvas.shape == (900, 1600, 3)
        vx, vy, vw, vh = VIEW_RECT
        assert green_pixels(canvas[vy:vy + vh, vx:vx + vw]) > 500, "target boxes missing in viewport"
        assert engine.cjk_path, "CJK font missing in package"
        probe = np.zeros((44, 260, 3), np.uint8)
        w, h = engine.draw(probe, "螺栓 螺母 垫圈", 6, 8, 24, (230, 237, 246), "SemiBold")
        assert w > 60 and h > 12 and probe.sum() > 0, "CJK text render failed"
        print("PASS: preview mock renderer packaged runtime")
        return
    if args.interval >= args.max_age:
        parser.error("--interval must be < --max-age, otherwise each round expires before the next")
    if args.headless and args.frames < 1:
        parser.error("headless requires --frames > 0")
    remote = RemoteRounds(args.endpoint, args.max_age) if args.endpoint else None
    if remote is not None:
        try:
            status = remote.handshake()
        except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
            sys.exit(f"result service unreachable at startup: {error}")
        print(f"session {status['session_id']} mode {status['mode']} "
              f"hardware_connected {status['hardware_connected']}", flush=True)
    recorder = BatchRecords(args.records_dir) if args.records_dir else None
    anomalies = AnomalyLog(args.records_dir) if args.records_dir else None
    hud = Hud(TextEngine())
    fps = FpsMeter()
    click_pending = [False]
    disp = (1600, 900)
    scale = 1.0
    if not args.headless:
        aw, ah = _work_area()
        scale = min(aw / 1600.0, ah / 900.0, 2.0)  # 等比适配工作区，上限 2x 防过度放大
        disp = (int(1600 * scale) & ~1, int(900 * scale) & ~1)
        print(f"display {disp[0]}x{disp[1]} (scale {scale:.2f}, work area {aw}x{ah})", flush=True)

        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                bx, by, bw, bh = BUTTON
                mx, my = x / scale, y / scale  # 窗口像素 → 画布坐标
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    click_pending[0] = True
    else:
        def on_mouse(event, x, y, flags, param):
            pass

    scene = None
    capture = None if args.mock else cv2.VideoCapture(args.source, cv2.CAP_DSHOW)
    if not args.headless:
        cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WINDOW, on_mouse)
    try:
        i = 0
        while not args.frames or i < args.frames:
            i += 1
            now = time.time()
            fps.tick(now)
            if capture is not None:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("UVC frame unavailable")
            else:
                if scene is None:
                    scene = mock_frame(mock_packet("scene", 0, 0, 0))
                frame = scene
            will_record = False
            fresh = now
            if remote is None:
                if capture is None:
                    state = demo_state(mock_packet("local-preview", i, 0, i), fps.value())
                else:
                    state = uvc_state(frame.shape, fps.value())
            else:
                if args.trigger_frame and i == args.trigger_frame:
                    remote.trigger(now)  # 联调自检：模拟按 c / 点按钮（覆盖 D8 记录路径）
                remote.poll(now, args.interval)
                fresh = time.time()  # 接收后再取钟：overlay/记录年龄不与"请求前"混用（防负年龄 flap）
                current, _ = remote.overlay(fresh)
                age = fresh - remote.received_at if remote.received_at is not None else None
                will_record = (recorder is not None and current
                               and remote.last_round_manual and recorder.accept(remote.packet))
                rec_count = (recorder.count + (1 if will_record else 0)
                             if recorder is not None else None)
                state = endpoint_state(remote, rec_count, current, age, fps.value(), frame.shape)
            canvas = hud.render(frame, state)
            if will_record:
                recorder.write(remote.packet, canvas, fresh - remote.received_at)
            if anomalies is not None and remote is not None:
                for event in remote.drain_events():
                    anomalies.log(remote.mode, event, canvas)
            if args.save and not cv2.imwrite(str(args.save), canvas):
                raise RuntimeError("preview image save failed")
            if not args.headless:
                cv2.imshow(WINDOW, canvas if scale == 1.0
                           else cv2.resize(canvas, disp, interpolation=cv2.INTER_LINEAR))
                key = cv2.waitKey(1) & 255
                if key in (27, ord("q")):
                    break
                if key == ord("c") and remote is not None:
                    remote.trigger(now)
                if click_pending[0]:
                    click_pending[0] = False
                    if remote is not None:
                        remote.trigger(now)
                delay = 1.0 / 30.0 - (time.time() - now)  # 30fps 节流（渲染耗时计入）
                if delay > 0:
                    time.sleep(delay)
    finally:
        if capture is not None:
            capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
