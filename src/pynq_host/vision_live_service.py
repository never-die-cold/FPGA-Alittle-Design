"""W05 正式检查服务骨架：HTTP 轮次/产物/幂等层 + 可插拔检查引擎（C04 §2.3）。

与 vision_mock_service 的区别：真实引擎、每轮新捕获、(session_id, check_id) 唯一定位
产物（capture.png + capture.sha256 + packet.json，读取与哈希核对入口 src/pynq_host/round_artifacts.py）。
FILE 原型自动轮询在内存中检查并更新 latest_packet.json；手动触发保存完整产物。
--archive-every-round 恢复逐轮归档。分类器复用，权重文件变化后须重启服务。
- 引擎契约：engine(capture_path, round_dir, request_id) -> {status, targets, decision, width, height}；
  默认 file_engine（懒加载 inspection_run——cv2/numpy/torch 仅在真正服务时导入，
  本文件保持 stdlib 可测，接入 run_vision_python.sh）。
- prototype 由捕获后端结构性决定：FILE 后端恒 true（离线产物代实时，C04 §3.2），无开关；
  真实取帧后端（N03）接入时才允许 false。
- 超限映射：引擎 decision 计数为 None（target_limit）时，按报文内已列目标重算
  actual/delta/missing/extra，verdict/reasons 保持 RECHECK——不截断放行（检查V0 §3）；
  映射已登记 C04 §2.2 待 NC/JL 追认。
- frame_id = 软件 capture 序号（C04 Q1：非 cop_frame_id）；每轮恰一次新捕获（文件按序轮换）；
  端点与 mock 同形（/v1/status /v1/check /v1/config），EXE 无需改动即可消费。
"""
import argparse
import hashlib
import json
import threading
import time
import uuid
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from vision_mock_service import parse_trigger_ref
from vision_protocol import VERSION, validate_packet

CLASSES = ("bolt", "nut", "washer")


def atomic_write(path, data):
    """原子落盘：先写 .pending 再改名（对齐 inspection_run 的 result.pending→result.json）。"""
    pending = path.with_name(path.name + ".pending")
    pending.write_bytes(data)
    pending.replace(path)


class FileCaptures:
    """FILE 捕获后端：目录内 PNG 按序轮换，每轮复制一份作为本轮 capture；prototype 恒 true。"""

    backend = "FILE"
    prototype = True

    def __init__(self, capture_dir):
        self.files = sorted(Path(capture_dir).glob("*.png"))
        if not self.files:
            raise ValueError(f"no PNG captures in {capture_dir}")
        self.seq = 0

    def capture(self, round_dir):
        path = self.files[self.seq % len(self.files)]
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        raw = path.read_bytes()
        atomic_write(round_dir / "capture.png", raw)
        return round_dir / "capture.png"

    def capture_frame(self):
        import cv2
        import numpy as np
        raw = self.files[self.seq % len(self.files)].read_bytes()
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("capture is not a decodable color image")
        return frame


def complete_decision(decision, targets):
    """超限映射：actual/delta/missing/extra 为 None 时按报文内目标重算；verdict/reasons 不动。"""
    if not isinstance(decision, dict):
        return decision  # LOCATION_ONLY 等无判定场景原样透传
    if all(isinstance(decision.get(name), dict)
           for name in ("actual", "delta", "missing", "extra")):
        return decision
    actual = {name: 0 for name in CLASSES}
    for target in targets:
        if target.get("class") in actual:
            actual[target["class"]] += 1
    delta = {name: actual[name] - decision["expected"][name] for name in CLASSES}
    return {**decision, "actual": actual, "delta": delta,
            "missing": {name: max(-delta[name], 0) for name in CLASSES},
            "extra": {name: max(delta[name], 0) for name in CLASSES}}


class State:
    """会话状态：check_id 单调回绕；每轮 = 新捕获 → 引擎 → 报文校验 → 产物原子落盘。"""

    def __init__(self, root, captures, engine, order, archive_every_round=False):
        self.session_id = str(uuid.uuid4())
        self.config_id = 0
        self.check_id = 0
        self.captures = captures
        self.engine = engine
        self.order = dict(order)
        self.archive_every_round = archive_every_round
        self.last_packet = None
        self.engine_label = getattr(engine, "label", "FILE")
        self.completed_refs = OrderedDict()  # C04 §2.4 draft: retry key window
        self.lock = threading.Lock()
        self.session_dir = Path(root) / self.session_id[:8]
        self.session_dir.mkdir(parents=True, exist_ok=False)
        atomic_write(self.session_dir / "session.json", json.dumps(
            {"session_id": self.session_id, "started_at": time.time(),
             "backend": captures.backend, "engine": self.engine_label,
             "prototype": captures.prototype,
             "order": self.order, "protocol": VERSION}, sort_keys=True).encode())

    def check(self, trigger_ref):
        with self.lock:  # 引擎在锁内执行：检查轮次串行（单板单推理通道的现实约束）
            if trigger_ref is not None and trigger_ref in self.completed_refs:
                # 同一次用户触发的网络重试：回原轮报文，不新取帧、不递增 check_id。
                return self.completed_refs[trigger_ref]
            self.check_id = (self.check_id + 1) & 0xFFFFFFFF
            check = self.check_id
            round_dir = self.session_dir / f"check-{check:06d}"
            memory_round = (trigger_ref is None and not self.archive_every_round
                            and self.captures.prototype is True
                            and hasattr(self.captures, "capture_frame")
                            and hasattr(self.engine, "inspect_frame"))
            if memory_round:
                fields = self.engine.inspect_frame(self.captures.capture_frame())
            else:
                round_dir.mkdir(exist_ok=False)
                capture_path = self.captures.capture(round_dir)
                # 快照哈希侧车（C04 §2.3）：供读取方核对 capture 字节未被替换/篡改
                atomic_write(round_dir / "capture.sha256",
                             (hashlib.sha256(capture_path.read_bytes()).hexdigest() + "\n").encode())
                fields = self.engine(capture_path, round_dir, f"chk{check:06d}")
            packet = validate_packet({
                "version": VERSION, "mode": "LIVE", "session_id": self.session_id,
                "frame_id": self.captures.seq, "config_id": self.config_id,
                "check_id": check, "width": fields["width"], "height": fields["height"],
                "created_at": time.time(), "status": fields["status"],
                "targets": fields["targets"],
                "decision": complete_decision(fields["decision"], fields["targets"]),
                "prototype": self.captures.prototype,
                **({"trigger_ref": trigger_ref} if trigger_ref is not None else {})})
            payload = json.dumps(packet, sort_keys=True).encode()
            if not memory_round:
                atomic_write(round_dir / "packet.json", payload)
            atomic_write(self.session_dir / "latest_packet.json", payload)
            self.last_packet = packet
            if trigger_ref is not None:
                self.completed_refs[trigger_ref] = packet
                while len(self.completed_refs) > 16:
                    self.completed_refs.popitem(last=False)
            return packet


def file_engine(weights, order, min_score, max_targets, policy_max=None):
    """Cached model; polling inspects memory, manual/diagnostic rounds archive provenance."""
    cached = []
    weight_path = Path(weights)
    def classifier():
        signature = (weight_path.stat().st_mtime_ns, weight_path.stat().st_size)
        if not cached:
            from inspection_model import PrototypeClassifier
            cached.extend((PrototypeClassifier(weight_path), signature))
        if signature != cached[1]:
            raise ValueError("model file changed; restart service to load a new model")
        return cached[0]
    def fields(result):
        return {"status": result["decision"]["verdict"],
                "targets": [{"target_id": t["target_id"], "bbox": t["bbox"],
                             "class": t.get("class"), "score": t.get("score")}
                            for t in result["targets"]],
                "decision": result["decision"], "width": result["width"], "height": result["height"]}
    def run(capture_path, round_dir, request_id):
        from inspection_run import run as inspect  # 重依赖（cv2/torch）仅真正服务时导入
        result = inspect(source=capture_path, weights=weights, order=order, output=round_dir,
                         request_id=request_id, min_score=min_score, max_targets=max_targets,
                         policy_max=policy_max, classifier=classifier())
        return fields(result)
    def memory(frame):
        from inspection_replay import inspect_frame
        result, _ = inspect_frame(frame, classifier(), order, min_score, max_targets,
                                  policy_max)
        return fields(result)
    run.inspect_frame = memory
    return run


def make_server(host="127.0.0.1", port=8765, root=None, captures=None, engine=None, order=None,
                archive_every_round=False):
    state = State(root, captures, engine, order, archive_every_round)

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
            if self.path == "/v1/status":
                self.reply(200, {"mode": "LIVE", "session_id": state.session_id,
                                 "hardware_connected": True, "backend": state.captures.backend,
                                 "engine": state.engine_label,
                                 "prototype": state.captures.prototype})
            elif self.path == "/v1/latest":
                if state.last_packet is None:
                    self.reply(404, {"error": "no check yet"})
                else:
                    self.reply(200, state.last_packet)
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
                    request = json.loads(body)
                    if not isinstance(request, dict) or set(request) != {"control"}:
                        raise ValueError("expected control only")
                    control = request["control"]
                    if type(control) is not int or not 0 <= control <= 15:
                        raise ValueError("reserved control bits")
                    with state.lock:
                        state.config_id = (state.config_id + 1) & 0xFFFFFFFF
                        applied = state.config_id
                    self.reply(200, {"mode": "LIVE", "applied_config_id": applied})
            except (ValueError, TypeError) as error:
                self.reply(400, {"error": str(error)})
            except RuntimeError as error:
                # 捕获（C01 所有权/超时/错误）或引擎运行失败：服务侧故障，不产生正常结果
                self.reply(503, {"error": f"capture/engine failed: {error}"})

        def log_message(self, *args):
            pass
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--root", required=True, help="artifact root; one dir per session")
    parser.add_argument("--capture-dir", required=True, help="dir of PNG captures (rotated per round)")
    parser.add_argument("--weights", type=Path,
                        help="FP32 prototype .pt; required by --engine file")
    parser.add_argument("--order", type=int, nargs=3, required=True, metavar=("BOLT", "NUT", "WASHER"))
    parser.add_argument("--min-score", type=float, required=True)
    parser.add_argument("--max-targets", type=int, default=16)
    parser.add_argument("--archive-every-round", action="store_true",
                        help="archive automatic rounds as well as manual checks")
    parser.add_argument("--policy-max", type=int, default=None,
                        help="business cap (default 10); must be <= --max-targets")
    parser.add_argument("--engine", choices=("file", "cop-sim"), default="file",
                        help="file = offline FP32 engine; cop-sim = C03 register sim")
    parser.add_argument("--sim-classes", default="",
                        help="cop-sim scripted classes, e.g. bolt,nut,washer (empty=image-derived)")
    parser.add_argument("--sim-delay-ms", type=float, default=0.0,
                        help="cop-sim per-target delay for BUSY/timeout tests")
    parser.add_argument("--sim-fault", action="append", default=[],
                        choices=("timeout", "crc", "short", "stale", "target-error"),
                        help="persistent cop-sim fault; restart the service to clear")
    args = parser.parse_args()
    order = dict(zip(CLASSES, args.order))
    captures = FileCaptures(args.capture_dir)
    if args.engine == "file":
        if args.weights is None:
            parser.error("--weights is required by --engine file")
        engine = file_engine(args.weights, order, args.min_score, args.max_targets,
                             args.policy_max)
    else:
        from cop_engine import cop_engine
        from cop_mmio_sim import SimFaults
        faults = SimFaults(timeout="timeout" in args.sim_fault,
                           crc_mismatch="crc" in args.sim_fault,
                           short_payload="short" in args.sim_fault,
                           stale_result="stale" in args.sim_fault,
                           target_error=0 if "target-error" in args.sim_fault else None)
        classes = tuple(name.strip() for name in args.sim_classes.split(",") if name.strip())
        engine = cop_engine(order, args.min_score, args.max_targets, args.policy_max,
                            classes=classes, faults=faults,
                            delay_s=args.sim_delay_ms / 1000.0)
    label = getattr(engine, "label", "FILE")
    print(f"LIVE SERVICE (backend={captures.backend}, engine={label}, "
          f"prototype={captures.prototype}): http://{args.host}:{args.port}/v1/status",
          flush=True)
    make_server(host=args.host, port=args.port, root=args.root,
                captures=captures, engine=engine, order=order,
                archive_every_round=args.archive_every_round).serve_forever()
