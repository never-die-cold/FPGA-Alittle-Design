"""Windows preview prototype. Round-level overlay per docs/vision-sync-protocol-decisions.md.

画面来源：UVC 采集卡（--source）或本机合成场景（--mock）。网络结果按轮次语义叠加：
状态机（D2 触发 / D3 有效性撤框 / D5 重连）在 rounds.py，离板测试 sim/vision/test_vision_rounds.py；
本文件只负责取帧、画框与横幅。MOCK 结果恒标 MOCK ONLY，不代表板上识别（plan.md §3.4）。
无 --endpoint 时纯视频显示 VIDEO ONLY | UNASSOCIATED，不叠任何框。
"""
import argparse
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pynq_host"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vision_protocol import mock_packet
from rounds import RemoteRounds
import cv2
import numpy as np

BANNER_H = 55


def mock_frame(packet):
    frame = np.full((packet["height"], packet["width"], 3), (220, 230, 240), np.uint8)
    for target in packet["targets"]:
        x0, y0, x1, y1 = target["bbox"]
        cv2.rectangle(frame, (x0, y0), (x1 - 1, y1 - 1), (40, 50, 60), -1)
    return frame


def draw_targets(frame, targets):
    # bbox 为半开区间 [x0,x1)×[y0,y1)；OpenCV 画笔含端点像素，故右下取 x1-1/y1-1 覆盖同一像素集。
    for target in targets:
        x0, y0, x1, y1 = target["bbox"]
        cv2.rectangle(frame, (x0, y0), (x1 - 1, y1 - 1), (40, 160, 30), 2)
        cv2.putText(frame, f"target {target['target_id']}", (x0, y0 - 8), 0, .6, (20, 80, 20), 2)


def draw_banner(frame, text):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], BANNER_H), (35, 35, 35), -1)
    cv2.putText(frame, text, (16, 35), 0, .8, (255, 255, 255), 2)


def render(frame, targets, label):
    frame = frame.copy()
    if targets is not None:
        draw_targets(frame, targets)
    draw_banner(frame, label)
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--endpoint", help="result service URL, e.g. http://127.0.0.1:8765")
    parser.add_argument("--source", type=int, default=0, help="UVC capture device index")
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--save", type=Path)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--max-age", type=float, default=1.0, help="D3 result age window (s)")
    parser.add_argument("--interval", type=float, default=0.5,
                        help="auto check trigger period (s); must be < --max-age")
    args = parser.parse_args()
    if args.selftest:
        p = mock_packet("selftest", 1, 0, 1)
        shown = render(mock_frame(p), p["targets"], "MOCK ONLY | ROUND 1 | 0.0s ago | 2 targets")
        assert shown.shape == (720, 1280, 3)
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
    scene = None
    capture = None if args.mock else cv2.VideoCapture(args.source, cv2.CAP_DSHOW)
    try:
        i = 0
        while not args.frames or i < args.frames:
            i += 1
            now = time.time()
            if capture is not None:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("UVC frame unavailable")
            else:
                if scene is None:
                    scene = mock_frame(mock_packet("scene", 0, 0, 0))
                frame = scene
            targets = None
            if remote is None:
                if capture is None:
                    p = mock_packet("local-preview", i, 0, i)
                    targets = p["targets"]
                    label = (f"MOCK ONLY | ROUND {p['check_id']} | 0.0s ago | "
                             f"{len(p['targets'])} targets")
                else:
                    label = "VIDEO ONLY | UNASSOCIATED | no board recognition"
            else:
                remote.poll(now, args.interval)
                current, status_text = remote.overlay(now)
                targets = remote.packet["targets"] if current else None
                label = "MOCK ONLY | " + status_text
            shown = render(frame, targets, label)
            if args.save and not cv2.imwrite(str(args.save), shown):
                raise RuntimeError("preview image save failed")
            if not args.headless:
                cv2.imshow("M2 vision preview", shown)
                key = cv2.waitKey(33) & 255
                if key in (27, ord("q")):
                    break
                if key == ord("c") and remote is not None:
                    remote.last_trigger = 0.0
    finally:
        if capture is not None:
            capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
