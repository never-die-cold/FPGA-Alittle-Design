"""W05 检查服务骨架（src/pynq_host/vision_live_service.py）离板测试——轮次/产物/幂等层。

纯 stdlib：FILE 捕获后端（字节即 PNG，本层不解码）+ 注入桩引擎；
落盘在仓库内 sim/build/vision/service-test/。覆盖：LIVE 报文校验、每轮新捕获（序号推进、
文件轮换、字节一致）、产物唯一目录与原子落盘、/v1/latest 幂等复用、config 递增、
超限映射（decision 计数 None → 按报文内目标重算）、快照读取器校验（绑定/哈希/篡改负例）、
trigger_ref 回显与 400/404。
"""
import hashlib
import json
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from vision_live_service import FileCaptures, State, make_server
from vision_protocol import validate_packet


def post(base, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(base + path, data, headers)
    with urllib.request.urlopen(request, timeout=2) as response:
        return json.loads(response.read(65537))


def get(base, path):
    with urllib.request.urlopen(base + path, timeout=2) as response:
        return json.loads(response.read(65537))


def stub_engine(rounds):
    """桩引擎：按调用序返回 RECHECK（超限形态）/ CHECK_FAIL / CHECK_PASS；产物写 engine.json。"""
    plan = [
        ("RECHECK", ("bolt", "nut"), ["low_score"], True),
        ("CHECK_FAIL", ("bolt", "bolt", "nut", "nut", "washer"), [], False),
        ("CHECK_PASS", ("bolt", "nut", "washer", "washer"), [], False),
    ]

    def run(capture_path, round_dir, request_id):
        status, classes, reasons, over_limit = plan[min(rounds[0], len(plan) - 1)]
        rounds[0] += 1
        (round_dir / "engine.json").write_text(
            json.dumps({"request_id": request_id}), encoding="utf-8")
        targets = [{"target_id": i, "bbox": [180 + i * 40, 170, 300 + i * 40, 300],
                    "class": cls, "score": 0.9} for i, cls in enumerate(classes)]
        counts = {name: classes.count(name) for name in ("bolt", "nut", "washer")}
        decision = {"verdict": status, "expected": {"bolt": 2, "nut": 2, "washer": 2},
                    "actual": counts, "delta": {k: counts[k] - 2 for k in counts},
                    "missing": {k: max(2 - counts[k], 0) for k in counts},
                    "extra": {k: max(counts[k] - 2, 0) for k in counts},
                    "reasons": reasons}
        if over_limit:  # inspection 链超限形态：计数为 None（服务端 complete_decision 负责映射）
            decision.update(actual=None, delta=None, missing=None, extra=None)
        return {"status": status, "targets": targets, "decision": decision,
                "width": 1280, "height": 720}
    return run


def main():
    out = root / "sim/build/vision/service-test"
    shutil.rmtree(out, ignore_errors=True)
    captures_dir = out / "captures"
    captures_dir.mkdir(parents=True)
    raw_a, raw_b = b"\x89PNG-fake-a", b"\x89PNG-fake-b"
    (captures_dir / "cap-a.png").write_bytes(raw_a)
    (captures_dir / "cap-b.png").write_bytes(raw_b)
    rounds = [0]
    server = make_server(port=0, root=out, captures=FileCaptures(captures_dir),
                         engine=stub_engine(rounds), order={"bolt": 2, "nut": 2, "washer": 2})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status = get(base, "/v1/status")
        assert status["mode"] == "LIVE" and status["hardware_connected"] is True
        assert status["backend"] == "FILE" and status["prototype"] is True
        statuses, packets = [], []
        for i in range(3):
            packet = post(base, "/v1/check", {"trigger_ref": f"ref-{i}"} if i == 0 else {})
            validate_packet(packet)
            packets.append(packet)
            statuses.append(packet["status"])
            assert packet["check_id"] == i + 1 and packet["frame_id"] == i + 1
            assert packet["prototype"] is True and packet["config_id"] == 0  # 未握手 config 前
        assert statuses == ["RECHECK", "CHECK_FAIL", "CHECK_PASS"]
        assert packets[0]["trigger_ref"] == "ref-0"
        assert all("trigger_ref" not in p for p in packets[1:])
        assert packets[0]["decision"]["actual"] == {"bolt": 1, "nut": 1, "washer": 0}  # 超限映射
        assert packets[0]["decision"]["verdict"] == "RECHECK"
        assert "low_score" in packets[0]["decision"]["reasons"]
        assert packets[1]["decision"]["missing"] == {"bolt": 0, "nut": 0, "washer": 1}
        assert packets[2]["decision"]["verdict"] == "CHECK_PASS"
        # 产物：(session, check) 唯一目录；capture 字节 = 对应源文件（轮换 a,b,a）；无 .pending 残留
        sess8 = packets[0]["session_id"][:8]
        meta = json.loads((out / sess8 / "session.json").read_text(encoding="utf-8"))
        assert meta["session_id"] == packets[0]["session_id"]
        assert meta["backend"] == "FILE" and meta["order"] == {"bolt": 2, "nut": 2, "washer": 2}
        for i, raw in enumerate((raw_a, raw_b, raw_a)):
            round_dir = out / sess8 / f"check-{i + 1:06d}"
            assert (round_dir / "capture.png").read_bytes() == raw
            assert (round_dir / "engine.json").exists()
            assert json.loads((round_dir / "packet.json").read_text(encoding="utf-8")) == packets[i]
        assert not list(out.rglob("*.pending")), "atomic writes must not leave .pending files"
        # 快照读取与哈希核对（C04 §2.3 方案，待 NC 确认）：绑定/哈希校验；篡改与缺轮大声失败
        from round_artifacts import SnapshotError, load_snapshot
        snap = load_snapshot(out, packets[0]["session_id"], packets[0]["check_id"])
        assert snap["packet"] == packets[0] and snap["engine_result"] is None
        assert snap["sha256"] == hashlib.sha256(raw_a).hexdigest()
        capture = snap["capture"]
        capture.write_bytes(raw_a[:-1] + b"X")
        try:
            load_snapshot(out, packets[0]["session_id"], packets[0]["check_id"])
            raise AssertionError("tampered capture accepted")
        except SnapshotError:
            pass
        capture.write_bytes(raw_a)
        assert load_snapshot(out, packets[0]["session_id"], packets[0]["check_id"])["sha256"] \
            == snap["sha256"]
        try:
            load_snapshot(out, packets[0]["session_id"], 99)
            raise AssertionError("missing round accepted")
        except SnapshotError:
            pass
        # /v1/latest 幂等复用：不触发引擎（rounds 计数不动）、报文与最后一线相同
        latest = get(base, "/v1/latest")
        assert latest == packets[2] and rounds[0] == 3
        # config 递增 → 后续报文 config_id 跟随；未知字段/非法值/未知路由按 400/404 拒绝
        assert post(base, "/v1/config", {"control": 3})["applied_config_id"] == 1
        assert post(base, "/v1/check", {})["config_id"] == 1
        for path, payload in (("/v1/check", {"unknown": 1}), ("/v1/config", {"control": 16}),
                              ("/v1/config", {"control": "x"})):
            try:
                post(base, path, payload)
                raise AssertionError(f"{path} {payload} accepted")
            except urllib.error.HTTPError as error:
                assert error.code == 400
        try:
            get(base, "/v1/missing")
            raise AssertionError("unknown route accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 404
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: live service rounds/artifacts/idempotent-latest/config/over-limit-mapping/400-404")
    class MemoryCaptures(FileCaptures):
        def capture_frame(self):
            self.seq += 1
            return b"frame-in-memory"
    counter = [0]
    engine = stub_engine(counter)
    def memory(frame):
        assert frame == b"frame-in-memory"
        # Reuse the stub's decision generator without any image or capture write.
        scratch = out / "memory-engine"
        scratch.mkdir(exist_ok=True)
        return engine(None, scratch, "memory")
    engine.inspect_frame = memory
    state = State(out, MemoryCaptures(captures_dir), engine, {"bolt": 2, "nut": 2, "washer": 2})
    first = state.check(None)
    assert not list(state.session_dir.glob("check-*"))
    assert json.loads((state.session_dir / "latest_packet.json").read_text()) == first
    manual = state.check("manual-archive")
    assert manual["trigger_ref"] == "manual-archive"
    assert (state.session_dir / "check-000002/capture.png").exists()
    state.check(None)
    assert len(list(state.session_dir.glob("check-*"))) == 1
    state = State(out, MemoryCaptures(captures_dir), engine, {"bolt": 2, "nut": 2, "washer": 2}, True)
    state.check(None)
    assert (state.session_dir / "check-000001/capture.png").exists()
    # Future non-prototype backends retain C04 Q3 per-round capture evidence.
    real_captures = MemoryCaptures(captures_dir)
    real_captures.prototype = False
    state = State(out, real_captures, engine, {"bolt": 2, "nut": 2, "washer": 2})
    state.check(None)
    assert (state.session_dir / "check-000001/capture.png").exists()
    print("PASS: prototype memory polling; manual, diagnostic and non-prototype rounds retain archives")


if __name__ == "__main__":
    main()
