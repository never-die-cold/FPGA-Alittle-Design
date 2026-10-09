"""Windows preview prototype. Round-level overlay per docs/vision-sync-protocol-decisions.md.

画面来源：UVC 采集卡（--source）或本机合成场景（--mock）。
- 状态机（D2 触发 / D3 有效性撤框 / D5 重连）在 rounds.py（离板测试 test_vision_rounds.py）；
- 批次记录与异常事件在 records.py；本文件负责取帧与 HUD 绘制。

HUD 设计 v3（data/logs/2026-10-08-exe-ui-design/README.md）：
- 左上状态框：模式徽标（MOCK ONLY / LIVE / VIDEO ONLY）+ 状态行；
- 右上四格指标面板：ROUND / TARGETS / REC / AGE + 新鲜度条（UVC-only 模式隐藏面板）；
- 目标：实线绿方框 + T 序号片。
MOCK 结果恒标 MOCK ONLY，不代表板上识别（plan.md §3.4）。无 --endpoint 时纯视频显示
VIDEO ONLY | UNASSOCIATED，不叠任何框。
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

FONT = cv2.FONT_HERSHEY_DUPLEX
PANEL = (34, 26, 20)        # 深蓝黑衬底 #141A22
CYAN = (255, 210, 0)        # 主色 / 新鲜度条 #00D2FF
GREEN = (130, 230, 0)       # 目标框 / 有效 #00E682
AMBER = (32, 176, 255)      # 徽标琥珀 #FFB020
AMBER_DEEP = (0, 150, 240)  # 等待文字深琥珀 #F09600
RED = (79, 77, 255)         # 过期/故障 #FF4D4F
TEXT = (246, 248, 250)
DIM = (150, 156, 160)
SEP = (88, 80, 74)
BORDER = (150, 140, 130)


def tsize(text, scale, th=1):
    (w, h), _ = cv2.getTextSize(text, FONT, scale, th)
    return w, h


def put(img, text, org, scale, color, th=1, align="left"):
    w, _ = tsize(text, scale, th)
    x, y = org
    if align == "right":
        x -= w
    elif align == "center":
        x -= w // 2
    cv2.putText(img, text, (x, y), FONT, scale, color, th, cv2.LINE_AA)


def panel(img, rect, alpha=0.55):
    """半透明衬底：仅混合面板 ROI（不全屏），性能可控。"""
    x0, y0, x1, y1 = rect
    roi = img[y0:y1, x0:x1]
    base = np.empty_like(roi)
    base[:] = PANEL
    cv2.addWeighted(base, alpha, roi, 1.0 - alpha, 0, roi)


def framed(img, rect):
    panel(img, rect)
    cv2.rectangle(img, (rect[0], rect[1]), (rect[2], rect[3]), BORDER, 1)


def chip(img, x, y, text, fg, bg, scale=0.55, th=2, pad=8):
    w, h = tsize(text, scale, th)
    cv2.rectangle(img, (x, y), (x + w + 2 * pad, y + h + 12), bg, -1)
    put(img, text, (x + pad, y + h + 6), scale, fg, th)


def mock_frame(packet):
    """合成场景（--mock 演示）：冷灰工作台 + 细网格 + 椭圆"零件"（暗色，便于定位风格）。"""
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


def draw_targets(frame, targets):
    """v3：实线绿色方框 + T 序号片（颜色 + 形状 + 文字三重编码）。"""
    for target in targets:
        x0, y0, x1, y1 = target["bbox"]
        cv2.rectangle(frame, (x0, y0), (x1 - 1, y1 - 1), GREEN, 2, cv2.LINE_AA)
        chip(frame, x0, max(y0 - 34, 0), f"T{target['target_id']}", (10, 20, 10), GREEN)


def draw_hud(frame, hud):
    """HUD 层（设计 v3）。hud 由调用方按模式组装：
    badge=(文本, 底色) / status=(文本, 颜色, 线宽) / metrics=[(标签, 数值, 颜色)] 或 None /
    fresh=(剩余比例 0..1, 颜色) 或 None。
    """
    framed(frame, (24, 20, 384, 122))
    chip(frame, 40, 36, hud["badge"][0], (16, 14, 12), hud["badge"][1], scale=0.8, th=2, pad=12)
    text, color, th = hud["status"]
    put(frame, text, (42, 103), 0.45 if th == 1 else 0.5, color, th)
    if hud["metrics"] is None:
        return
    x1, y0 = frame.shape[1] - 24, 20
    x0, y1 = x1 - 520, 116
    framed(frame, (x0, y0, x1, y1))
    cell_w = (x1 - x0) // 4
    for i, (label, value, color) in enumerate(hud["metrics"]):
        cx = x0 + cell_w * i + cell_w // 2
        put(frame, label, (cx, y0 + 26), 0.42, DIM, 1, "center")
        put(frame, value, (cx, y0 + 74), 1.2, color, 2, "center")
        if i:
            cv2.line(frame, (x0 + cell_w * i, y0 + 14), (x0 + cell_w * i, y1 - 14), SEP, 1)
    if hud["fresh"] is not None:
        frac, color = hud["fresh"]
        bar_y = y1 + 5
        cv2.rectangle(frame, (x0, bar_y), (x1, bar_y + 5), (70, 62, 56), -1)
        if frac > 0:
            cv2.rectangle(frame, (x0, bar_y), (x0 + int((x1 - x0) * frac), bar_y + 5), color, -1)


def render(frame, targets, hud):
    frame = frame.copy()
    if targets is not None:
        draw_targets(frame, targets)
    draw_hud(frame, hud)
    return frame


def green_pixels(image):
    """绿色目标框像素计数（int16 防 uint8 溢出；供 selftest 与打包断言复用）。"""
    f = image.astype(np.int16)
    return int(((f[:, :, 1] > 150) & (f[:, :, 1] - f[:, :, 0] > 60)
                & (f[:, :, 1] - f[:, :, 2] > 60)).sum())


def metrics_cells(packet, rec_count, age_text, value_color):
    return [("ROUND", str(packet["check_id"]) if packet else "--", value_color),
            ("TARGETS", str(len(packet["targets"])) if packet else "--", value_color),
            ("REC", str(rec_count) if rec_count is not None else "--",
             TEXT if rec_count is not None else DIM),
            ("AGE", age_text, value_color)]


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
        hud = {"badge": ("MOCK ONLY", AMBER),
               "status": ("STREAMING | 1280x720 | session selftest", DIM, 1),
               "metrics": metrics_cells(p, 0, "0.0s", TEXT),
               "fresh": (1.0, CYAN)}
        shown = render(mock_frame(p), p["targets"], hud)
        assert shown.shape == (720, 1280, 3)
        assert green_pixels(shown) > 500, "target boxes missing in selftest render"
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
            w, h = frame.shape[1], frame.shape[0]
            targets = None
            will_record = False
            fresh = now
            if remote is None:
                if capture is None:
                    p = mock_packet("local-preview", i, 0, i)
                    targets = p["targets"]
                    status_line = (f"LOCAL DEMO | synthetic | {w}x{h}", DIM, 1)
                    cells = metrics_cells(p, None, "0.0s", TEXT)
                    fresh_bar = None
                else:
                    status_line = ("UNASSOCIATED | no board recognition", DIM, 1)
                    cells = None  # UVC-only：隐藏指标面板（无结果源，不空转仪表）
                    fresh_bar = None
                hud = {"badge": ("MOCK ONLY", AMBER) if capture is None else ("VIDEO ONLY", DIM),
                       "status": status_line, "metrics": cells, "fresh": fresh_bar}
            else:
                if args.trigger_frame and i == args.trigger_frame:
                    remote.trigger(now)  # 联调自检：模拟按 c（覆盖 D8 记录路径）
                remote.poll(now, args.interval)
                fresh = time.time()  # 接收后再取钟：overlay/记录年龄不与"请求前"混用（防负年龄 flap）
                current, _ = remote.overlay(fresh)
                targets = remote.packet["targets"] if current else None
                will_record = (recorder is not None and current
                               and remote.last_round_manual and recorder.accept(remote.packet))
                rec_count = recorder.count + (1 if will_record else 0) if recorder is not None else None
                badge = ("LIVE", GREEN) if remote.mode == "LIVE" else ("MOCK ONLY", AMBER)
                age = fresh - remote.received_at if remote.received_at is not None else None
                if current:
                    frac = max(0.0, 1.0 - age / args.max_age)
                    hud = {"badge": badge,
                           "status": (f"STREAMING | {w}x{h} | session {remote.session[:8]}", DIM, 1),
                           "metrics": metrics_cells(remote.packet, rec_count, f"{age:.1f}s", TEXT),
                           "fresh": (frac, CYAN)}
                else:
                    hud = {"badge": badge,
                           "status": ("WAITING FOR RESULT", AMBER_DEEP, 2),
                           "metrics": metrics_cells(None, rec_count,
                                                    f"{age:.1f}s" if age is not None else "--",
                                                    AMBER_DEEP),
                           "fresh": (1.0, RED)}
            shown = render(frame, targets, hud)
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
