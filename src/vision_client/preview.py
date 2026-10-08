"""Windows preview prototype. Round-level overlay per docs/vision-sync-protocol-decisions.md.

画面来源：UVC 采集卡（--source）或本机合成场景（--mock）。网络结果按轮次语义叠加：
状态机（D2 触发 / D3 有效性撤框 / D5 重连）在 rounds.py，离板测试 sim/vision/test_vision_rounds.py；
批次记录（D8–D10）在 records.py（--records-dir 开启，仅手动触发的有效轮次）；
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
from records import AnomalyLog, BatchRecords
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
    parser.add_argument("--records-dir", type=Path,
                        help="batch record dir (D8-D10): manual-triggered current rounds only")
    parser.add_argument("--trigger-frame", type=int, default=0,
                        help="self-check hook: simulate one manual trigger (c) at frame N")
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
    recorder = BatchRecords(args.records_dir) if args.records_dir else None
    anomalies = AnomalyLog(args.records_dir) if args.records_dir else None
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
            will_record = False
            if remote is None:
                if capture is None:
                    p = mock_packet("local-preview", i, 0, i)
                    targets = p["targets"]
                    label = (f"MOCK ONLY | ROUND {p['check_id']} | 0.0s ago | "
                             f"{len(p['targets'])} targets")
                else:
                    label = "VIDEO ONLY | UNASSOCIATED | no board recognition"
            else:
                if args.trigger_frame and i == args.trigger_frame:
                    remote.trigger(now)  # 联调自检：模拟按 c（覆盖 D8 记录路径）
                remote.poll(now, args.interval)
                fresh = time.time()  # 接收后再取钟：overlay/记录年龄不与"请求前"混用（防负年龄 flap）
                current, status_text = remote.overlay(fresh)
                targets = remote.packet["targets"] if current else None
                will_record = (recorder is not None and current
                               and remote.last_round_manual and recorder.accept(remote.packet))
                if will_record:
                    status_text += f" | REC {recorder.count + 1}"
                label = "MOCK ONLY | " + status_text
            shown = render(frame, targets, label)
            if will_record:
                recorder.write(remote.packet, shown, fresh - remote.received_at)
            if anomalies is not None and remote is not None:
                for event in remote.drain_events():
                    anomalies.log(remote.mode, event, shown)
            if args.save and not cv2.imwrite(str(args.save), shown):
                raise RuntimeError("preview image save failed")
            if not args.headless:
                cv2.imshow("M2 vision preview", shown)
                key = cv2.waitKey(33) & 255
                if key in (27, ord("q")):
                    break
                if key == ord("c") and remote is not None:
                    remote.trigger(now)
    finally:
        if capture is not None:
            capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
