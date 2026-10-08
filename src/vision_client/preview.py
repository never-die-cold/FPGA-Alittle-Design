"""Windows preview prototype. Round-level overlay per docs/vision-sync-protocol-decisions.md.

画面来源：UVC 采集卡（--source）或本机合成场景（--mock）。网络结果按轮次语义叠加：
- D2：POST /v1/check 触发一轮检查；D3：session+config+年龄三判据，过期/断联撤框；
- D5：连续失败 >= FAIL_LIMIT 视为会话失效，自动重新握手。
MOCK 结果恒标 MOCK ONLY，不代表板上识别（plan.md §3.4）。无 --endpoint 时
纯视频显示 VIDEO ONLY | UNASSOCIATED，不叠任何框。
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pynq_host"))
from vision_protocol import mock_packet, validate_packet, is_current
import cv2
import numpy as np

REQUEST_TIMEOUT = 2.0
FAIL_LIMIT = 3
BANNER_H = 55


def http_json(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read(65537))


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


class RemoteRounds:
    """D2/D3/D5 会话状态机：握手 → 周期触发 → 有效性判定 → 连续失败重握手。"""

    def __init__(self, endpoint, max_age):
        self.endpoint = endpoint.rstrip("/")
        self.max_age = max_age
        self.session = None
        self.expected_config = None
        self.fails = 0
        self.last_trigger = 0.0
        self.packet = None

    def handshake(self):
        status = http_json(self.endpoint + "/v1/status")
        applied = http_json(self.endpoint + "/v1/config", {"control": 0})["applied_config_id"]
        self.session = status["session_id"]
        self.expected_config = applied
        self.fails = 0
        self.packet = None
        self.last_trigger = 0.0
        return status

    def poll(self, now, interval):
        if now - self.last_trigger < interval:
            return
        self.last_trigger = now
        try:
            self.packet = validate_packet(http_json(self.endpoint + "/v1/check"))
            self.fails = 0
        except (urllib.error.URLError, OSError, ValueError) as error:
            self.fails += 1
            print(f"WARN: check failed ({self.fails}/{FAIL_LIMIT}): {error}", flush=True)
            if self.fails >= FAIL_LIMIT:
                self.handshake()

    def overlay(self, now):
        if self.packet is not None and self.session is not None \
                and is_current(self.packet, self.session, self.expected_config, self.max_age):
            age = now - self.packet["created_at"]
            return True, (f"ROUND {self.packet['check_id']} | {age:.1f}s ago | "
                          f"{len(self.packet['targets'])} targets")
        return False, "WAITING FOR RESULT"


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
