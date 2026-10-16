"""服务 × EXE 联合离板回归（W08-1）——工业场景黄金矩阵。

服务 = vision_live_service（FILE 后端 + 场景引擎，prototype 恒 true）；
EXE 侧 = 真实逻辑层（rounds.RemoteRounds 状态机 + records.BatchRecords + live_view），
不依赖 cv2/窗口/板卡/打包；落盘在仓库内 sim/build/vision/joint-test/。

黄金矩阵（场景 → 判定/横幅/记录三重期望；"6/6"=实际/工单）：
  pass    CHECK_PASS  "6/6"  横幅 "CHECK_PASS"            无差额
  missing CHECK_FAIL  "5/6"  横幅 "CHECK_FAIL -washerx1"  缺件
  extra   CHECK_FAIL  "7/6"  横幅 "CHECK_FAIL +boltx1"    多余
  wrong   CHECK_FAIL  "6/6"  横幅 "CHECK_FAIL -washerx1 +nutx1"  错料（缺一多一）
  recheck RECHECK     "5/6"  横幅 "RECHECK -washerx1"     未分类+低分
另覆盖：损坏报文（服务侧 400 拒绝、不写产物；EXE 侧拒绝无效报文未被冒用）、
旧结果（超龄撤框、旧配置撤框）、断联（撤框且失败的手动轮不落记录——D8 采纳点）、
重启（新会话≠旧结果，自动重握手恢复）。
"""
import json
import shutil
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from records import BatchRecords
from rounds import RemoteRounds, WAITING, live_view
from vision_live_service import FileCaptures, make_server
from vision_protocol import validate_packet

WORK = {"bolt": 2, "nut": 2, "washer": 2}
BOLT, NUT, WASH = ("bolt", 0.97), ("nut", 0.93), ("washer", 0.95)
SCENARIOS = {  # name -> (status, [(class, score)...], reasons)
    "pass": ("CHECK_PASS", [BOLT, ("bolt", .95), NUT, ("nut", .91), WASH, ("washer", .94)], []),
    "missing": ("CHECK_FAIL", [BOLT, ("bolt", .95), NUT, ("nut", .91), WASH], []),
    "extra": ("CHECK_FAIL", [BOLT, ("bolt", .95), ("bolt", .93), NUT, ("nut", .91),
                             WASH, ("washer", .94)], []),
    "wrong": ("CHECK_FAIL", [BOLT, ("bolt", .95), NUT, ("nut", .91), ("nut", .90), WASH], []),
    "recheck": ("RECHECK", [BOLT, ("bolt", .95), NUT, ("nut", .91), WASH, (None, .42)],
                ["low_score", "unknown_class"]),
}
GOLDEN = {  # name -> (verdict, 横幅差额, 实际/工单)
    "pass": ("CHECK_PASS", "", "6/6"), "missing": ("CHECK_FAIL", "-washerx1", "5/6"),
    "extra": ("CHECK_FAIL", "+boltx1", "7/6"),
    "wrong": ("CHECK_FAIL", "-washerx1 +nutx1", "6/6"),
    "recheck": ("RECHECK", "-washerx1", "5/6"),
}


def build_engine(pick):
    """场景引擎：pick = [场景名]（可变容器，主流程逐轮改写）。"""
    def run(capture_path, round_dir, request_id):
        name = pick[0]
        status, classes, reasons = SCENARIOS["pass" if name == "corrupt" else name]
        targets = [{"target_id": i, "bbox": [180 + 40 * i, 170, 340 + 40 * i, 290],
                    "class": cls, "score": score} for i, (cls, score) in enumerate(classes)]
        if name == "corrupt":
            targets[0]["unexpected_field"] = 1  # 未知字段：服务端 validate_packet 应拒绝
        counts = {n: sum(1 for cls, _ in classes if cls == n) for n in WORK}
        delta = {n: counts[n] - WORK[n] for n in WORK}
        decision = {"verdict": status, "expected": dict(WORK), "actual": counts, "delta": delta,
                    "missing": {n: max(-delta[n], 0) for n in WORK},
                    "extra": {n: max(delta[n], 0) for n in WORK}, "reasons": reasons}
        return {"status": status, "targets": targets, "decision": decision,
                "width": 1280, "height": 720}
    return run


class RogueHandler(BaseHTTPRequestHandler):
    """冒烟替身：对任何 POST 回一个含未知字段的"LIVE"报文（EXE 侧必须拒绝）。"""
    def do_POST(self):
        data = b'{"mode": "LIVE", "evil": 1}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def main():
    out = root / "sim/build/vision/joint-test"
    shutil.rmtree(out, ignore_errors=True)
    captures = out / "captures"
    captures.mkdir(parents=True)
    (captures / "cap-a.png").write_bytes(b"\x89PNG-fake-a")
    (captures / "cap-b.png").write_bytes(b"\x89PNG-fake-b")
    pick = ["pass"]
    server = make_server(port=0, root=out / "service", captures=FileCaptures(captures),
                         engine=build_engine(pick), order=dict(WORK))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    remote = RemoteRounds(base, max_age=1.0)
    status = remote.handshake()
    assert status["mode"] == "LIVE" and status["hardware_connected"] is True
    assert remote.expected_config == 1 and status["prototype"] is True
    rec = BatchRecords(out / "records", save_image=lambda path, frame: True)
    now = 10_000.0

    def step(scenario):
        pick[0] = scenario
        nonlocal_now = now + 0.6
        remote.poll(nonlocal_now, 0.5)
        return nonlocal_now

    # 第 1 阶段：黄金矩阵（自动轮，永不落记录——D8 结构性保证）
    for scenario, (verdict, delta, totals) in GOLDEN.items():
        now = step(scenario)
        packet = remote.packet
        validate_packet(packet)
        view = live_view(packet)
        assert packet["status"] == verdict, (scenario, packet["status"])
        assert (view["verdict"], view["delta"], view["targets"]) == (verdict, delta, totals), \
            (scenario, view)
        assert remote.overlay(time.time())[0] is True, scenario
    assert live_view(remote.packet)["labels"][-1] == ("unclassified", "0.42")  # null 类别→未分类
    assert not (out / "records" / "records.jsonl").exists(), "auto rounds must not record"

    # 第 2 阶段：手动轮记录（每场景恰一条；键去重与 v2 字段）
    for scenario in ("pass", "missing", "recheck"):
        pick[0] = scenario
        now += 0.6
        assert remote.trigger(now) is True
        remote.poll(now, 0.5)
        assert remote.last_round_manual and remote.overlay(time.time())[0]
        assert rec.accept(remote.packet)
        rec.write(remote.packet, None, time.time() - remote.received_at)
    rows = [json.loads(l) for l in
            (out / "records" / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3 and rec.count == 3
    assert rows[0]["status"] == "CHECK_PASS" and set(rows[0]["decision"]["missing"].values()) == {0}
    assert rows[1]["decision"]["missing"] == {"bolt": 0, "nut": 0, "washer": 1}
    assert rows[2]["status"] == "RECHECK" and "low_score" in rows[2]["decision"]["reasons"]
    assert rows[2]["targets"][-1]["class"] is None
    assert all(r["prototype"] is True and r["screenshot"].startswith("screenshots/proto_")
               for r in rows)

    # 第 3 阶段：损坏报文——服务侧拒绝（400、无 packet.json、消耗的轮次不落记录）
    prev = remote.packet
    now = step("corrupt")
    assert remote.fails == 1 and remote.packet is prev, "corrupt round must not be adopted"
    cdir = out / "service" / prev["session_id"][:8] / f"check-{prev['check_id'] + 1:06d}"
    assert cdir.exists() and (cdir / "capture.png").exists()
    assert not (cdir / "packet.json").exists(), "rejected packet must not be persisted"
    now = step("pass")  # 恢复：下一轮正常采纳、fails 清零
    assert remote.fails == 0 and remote.packet["check_id"] == prev["check_id"] + 2

    # 第 4 阶段：损坏报文——EXE 侧拒绝（冒烟替身回无效报文；旧结果不得被冒用）
    rogue = ThreadingHTTPServer(("127.0.0.1", 0), RogueHandler)
    threading.Thread(target=rogue.serve_forever, daemon=True).start()
    good_base = remote.endpoint
    remote.endpoint = f"http://127.0.0.1:{rogue.server_port}"
    now += 0.6
    remote.poll(now, 0.5)
    assert remote.fails == 1 and remote.packet["check_id"] == prev["check_id"] + 2
    rogue.shutdown()
    rogue.server_close()
    remote.endpoint = good_base
    now = step("pass")
    assert remote.fails == 0 and remote.packet["check_id"] == prev["check_id"] + 3

    # 第 5 阶段：旧结果——超龄撤框 + 旧配置撤框（重握手恢复）
    remote.received_at = time.time() - 1.5
    assert remote.overlay(time.time()) == (False, WAITING)
    applied = json.loads(urllib.request.urlopen(urllib.request.Request(
        base + "/v1/config", b'{"control": 3}', {"Content-Type": "application/json"}),
        timeout=2).read())["applied_config_id"]
    assert applied == 2
    now = step("pass")
    assert remote.packet["config_id"] == 2 and remote.expected_config == 1
    assert remote.overlay(time.time()) == (False, WAITING), "old-config result must not overlay"
    remote.handshake()
    now = step("pass")
    assert remote.overlay(time.time())[0] is True

    # 第 6 阶段：断联（撤框 + 失败手动轮不落记录）→ 重启（新会话自动恢复）
    port = server.server_port
    server.shutdown()
    server.server_close()
    now += 0.6
    assert remote.trigger(now) is True  # 断联中的手动触发
    for _ in range(3):
        now += 0.6
        remote.poll(now, 0.5)
    assert remote.fails >= 3 and not remote.last_round_manual  # 采纳点语义：未冒名
    assert remote.overlay(time.time()) == (False, WAITING)
    assert rec.count == 3, "outage must not add records"
    server = make_server(port=port, root=out / "service", captures=FileCaptures(captures),
                         engine=build_engine(pick), order=dict(WORK))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    now += 0.6
    remote.poll(now, 0.5)  # 检测到新会话 → 重握手，本轮不采纳
    assert remote.packet is None
    now = step("pass")
    assert remote.overlay(time.time())[0] is True and not remote.last_round_manual
    now += 0.6
    assert remote.trigger(now) is True
    remote.poll(now, 0.5)
    assert remote.last_round_manual and remote.overlay(time.time())[0]
    rec.write(remote.packet, None, time.time() - remote.received_at)
    assert rec.count == 4

    # 收尾：事件沿完整（D11）、无 .pending 残留、记录金标
    kinds = {e["kind"] for e in remote.drain_events()}
    assert {"overlay_stale", "overlay_config", "overlay_outage", "overlay_ok",
            "session_changed", "rehandshake_failed"} <= kinds, kinds
    assert not list(out.rglob("*.pending")), "atomic writes must not leave .pending files"
    rows = (out / "records" / "records.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 4 and json.loads(rows[3])["prototype"] is True
    server.shutdown()
    server.server_close()
    print("PASS: joint service x EXE golden matrix (pass/missing/extra/wrong/recheck, "
          "corrupt-packet both sides, stale/config, outage/restart, records)")


if __name__ == "__main__":
    main()
