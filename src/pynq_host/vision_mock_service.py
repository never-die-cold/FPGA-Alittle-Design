"""Local M2 API mock + LIVE 网络替身. No MMIO, board access, inference or batch counting.

默认绑定 127.0.0.1；--host 0.0.0.0 供 EXE 远程联调（服务托管在他机，如 Pi）时使用。
mock 结果仅供界面联调，不代表板上识别（plan.md §3.4）。
schema v1.1（docs/vision-sync-protocol-decisions.md）：POST /v1/check 触发一轮检查，
check_id 单调回绕；/v1/latest 保留为调试拉取口（帧号随轮询推进，携带当前 check_id）。

--live 网络替身（W06，C04 §3.2）：模拟"服务正常 + 硬件已连接"的 LIVE 服务，
发 v1.2 LIVE 报文（类别/分数/decision 为确定性合成值），prototype 恒为 true——
替身永远不是实时推理，EXE 恒加 PROTOTYPE 标识；其记录/截图不得作为板上证据。
"""
import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from vision_protocol import CLASSES, VERSION, mock_packet, uint, validate_packet


class State:
    def __init__(self, live=False):
        self.mode = "LIVE" if live else "MOCK"
        self.session_id = str(uuid.uuid4())
        self.config_id = 0
        self.frame_id = 0
        self.check_id = 0
        self.control = 0
        self.lock = threading.Lock()

    def latest(self):
        with self.lock:
            self.frame_id = (self.frame_id + 1) & 0xFFFFFFFF
            if self.mode == "LIVE":
                return live_packet(self.session_id, self.frame_id, self.config_id, self.check_id)
            return mock_packet(self.session_id, self.frame_id, self.config_id, self.check_id)

    def check(self, trigger_ref):
        """D2：一轮检查 = 触发一次 → 抓一帧快照 → 回包（mock 即时完成）。"""
        with self.lock:
            self.frame_id = (self.frame_id + 1) & 0xFFFFFFFF
            self.check_id = (self.check_id + 1) & 0xFFFFFFFF
            if self.mode == "LIVE":
                return live_packet(self.session_id, self.frame_id, self.config_id,
                                   self.check_id, trigger_ref)
            return mock_packet(self.session_id, self.frame_id, self.config_id,
                               self.check_id, trigger_ref)

    def configure(self, request):
        if not isinstance(request, dict) or set(request) != {"control"}:
            raise ValueError("expected control only")
        control = uint(request["control"], "control")
        if control > 15:
            raise ValueError("reserved control bits")
        with self.lock:
            self.control = control
            self.config_id = (self.config_id + 1) & 0xFFFFFFFF
            return {"mode": self.mode, "applied_config_id": self.config_id}


def parse_trigger_ref(body):
    """请求体可选：无 body / {} / {"trigger_ref": "..."}；未知字段拒绝（D6 严格校验）。"""
    if not body:
        return None
    request = json.loads(body)
    if not isinstance(request, dict) or set(request) - {"trigger_ref"}:
        raise ValueError("expected trigger_ref only")
    ref = request.get("trigger_ref")
    if ref is not None and (not isinstance(ref, str) or not 0 < len(ref) <= 64):
        raise ValueError("invalid trigger_ref")
    return ref


LIVE_WORK_ORDER = {"bolt": 2, "nut": 2, "washer": 2}
LIVE_POS = ((180, 170, 339, 289), (730, 380, 929, 520), (420, 120, 580, 270),
            (980, 140, 1140, 290), (300, 460, 470, 620), (880, 560, 1040, 700))
LIVE_CLASSES = ("bolt", "bolt", "nut", "nut", "washer", "washer")
LIVE_SCORES = (0.97, 0.94, 0.91, 0.88, 0.96, 0.93)


def live_packet(session_id, frame_id, config_id, check_id, trigger_ref=None, prototype=True):
    """--live 替身报文（v1.2 LIVE 轮廓）：check_id % 3 循环 PASS / FAIL / RECHECK。

    工单恒为 2/2/2；FAIL 轮少一件 washer；RECHECK 轮 T5 类别为 null、分数 0.42（低分阻断）。
    类别/分数是确定性合成值，仅联调 EXE 显示，不代表板上识别。
    """
    scenario = (check_id + 2) % 3  # check_id 从 1 起：PASS → FAIL → RECHECK 循环
    targets = []
    for tid in range(5 if scenario == 1 else 6):
        label, score = LIVE_CLASSES[tid], LIVE_SCORES[tid]
        if scenario == 2 and tid == 5:
            label, score = None, 0.42  # 未分类 + 低分：覆盖 EXE 的 null/低分显示路径
        targets.append({"target_id": tid, "bbox": list(LIVE_POS[tid]),
                        "class": label, "score": score})
    actual = {name: 0 for name in CLASSES}
    for target in targets:
        if target["class"] is not None:
            actual[target["class"]] += 1
    delta = {name: actual[name] - LIVE_WORK_ORDER[name] for name in CLASSES}
    decision = {
        "verdict": ("CHECK_PASS", "CHECK_FAIL", "RECHECK")[scenario],
        "expected": dict(LIVE_WORK_ORDER), "actual": actual, "delta": delta,
        "missing": {name: -min(delta[name], 0) for name in CLASSES},
        "extra": {name: max(delta[name], 0) for name in CLASSES},
        "reasons": {0: [], 1: ["washer count below work order"],
                    2: ["low score T5"]}[scenario],
    }
    payload = {"version": VERSION, "mode": "LIVE", "session_id": session_id,
               "frame_id": frame_id, "config_id": config_id, "check_id": check_id,
               "width": 1280, "height": 720, "created_at": time.time(),
               "status": decision["verdict"], "targets": targets,
               "decision": decision, "prototype": prototype}
    if trigger_ref is not None:
        payload["trigger_ref"] = trigger_ref
    return validate_packet(payload)


def make_server(host="127.0.0.1", port=8765, live=False):
    state = State(live)
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body):
            data = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def read_body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("body size")
            return self.rfile.read(length) if length else b""

        def do_GET(self):
            if self.path == "/v1/latest":
                self.reply(200, state.latest())
            elif self.path == "/v1/status":
                self.reply(200, {"mode": state.mode, "session_id": state.session_id,
                                 "hardware_connected": state.mode == "LIVE"})
            else:
                self.reply(404, {"error": "unknown route"})

        def do_POST(self):
            if self.path not in ("/v1/config", "/v1/check"):
                self.reply(404, {"error": "unknown route"})
                return
            try:
                body = self.read_body()
                if self.path == "/v1/check":
                    self.reply(200, state.check(parse_trigger_ref(body)))
                else:
                    if not body:
                        raise ValueError("body size")
                    self.reply(200, state.configure(json.loads(body)))
            except (ValueError, TypeError) as error:
                self.reply(400, {"error": str(error)})

        def log_message(self, *args):
            pass
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1",
                        help="绑定地址；0.0.0.0 = 允许他机（EXE 联调机）访问")
    parser.add_argument("--live", action="store_true",
                        help="LIVE 网络替身：发 v1.2 LIVE 报文（prototype 恒 true，非实时结果）")
    args = parser.parse_args()
    shown = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    label = "LIVE STAND-IN (prototype, not on-board recognition)" if args.live else "MOCK ONLY"
    print(f"{label}: http://{shown}:{args.port}/v1/status", flush=True)
    make_server(host=args.host, port=args.port, live=args.live).serve_forever()
    make_server(host=args.host, port=args.port).serve_forever()
