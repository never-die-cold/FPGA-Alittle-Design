"""W05-2：真引擎走通服务（file_engine → inspection_run）——重依赖入口。

在服务骨架上验证 file_engine 适配器：FP32 原型 + 共享 ROI 预处理 + 工单规则，
经 v1.2 LIVE 报文与 (session, check) 产物目录返回。黄金值冻结自归档运行
data/evidence/2026-10-10-offline-inspection/runs/synthetic-001（同夹具同参数）。
本机若缺 torch/cv2/numpy，自动挂接仓库本地依赖目录 sim/build/vision-{torch,client}-deps。
"""
import hashlib
import json
import shutil
import sys
import threading
import urllib.request
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
for dep in ("vision-torch-deps", "vision-client-deps"):
    path = root / "sim" / "build" / dep
    if path.is_dir():
        sys.path.append(str(path))
sys.path.insert(0, str(root / "src/pynq_host"))
from inspection_rules import judge
from vision_live_service import FileCaptures, file_engine, make_server
from vision_protocol import validate_packet

FIXTURE = root / "data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png"
WEIGHTS = root / "models/cnn-border-fill-best.pt"
ORDER = {"bolt": 1, "nut": 1, "washer": 1}


def main():
    out = root / "sim/build/vision/engine-test"
    shutil.rmtree(out, ignore_errors=True)
    captures = out / "captures"
    captures.mkdir(parents=True)
    (captures / "synthetic.png").write_bytes(FIXTURE.read_bytes())
    engine = file_engine(WEIGHTS, dict(ORDER), 0.8, 10)
    server = make_server(port=0, root=out / "service", captures=FileCaptures(captures),
                         engine=engine, order=dict(ORDER))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    import inspection_model
    model_spy = patch.object(inspection_model, "PrototypeClassifier",
                             wraps=inspection_model.PrototypeClassifier)
    loads = model_spy.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/check",
            b'{"trigger_ref": "engine-1"}', {"Content-Type": "application/json"})
        packet = validate_packet(json.loads(urllib.request.urlopen(request, timeout=60).read()))
        assert packet["mode"] == "LIVE" and packet["prototype"] is True
        assert packet["trigger_ref"] == "engine-1"
        decision = packet["decision"]
        # 黄金值（同夹具同参数，10-10 归档 synthetic-001）：类别集合与工单计数逐项一致
        assert [t["class"] for t in packet["targets"]] == ["bolt", "washer", "bolt"]
        assert decision["actual"] == {"bolt": 2, "nut": 0, "washer": 1}
        assert decision["missing"] == {"bolt": 0, "nut": 1, "washer": 0}
        assert decision["extra"] == {"bolt": 1, "nut": 0, "washer": 0}
        assert packet["status"] == "CHECK_FAIL" == decision["verdict"]
        assert decision["reasons"] == [] and all(0.8 <= t["score"] <= 1 for t in packet["targets"])
        # 服务映射不改判：decision 必须等于规则引擎对同目标列表的重算
        assert decision == judge(packet["targets"], dict(ORDER), 0.8, 10)
        # 产物链：capture 原字节 + packet.json + inspection_run 完整证据（含源哈希）
        round_dir = out / "service" / packet["session_id"][:8] / f"check-{packet['check_id']:06d}"
        assert (round_dir / "capture.png").read_bytes() == FIXTURE.read_bytes()
        assert json.loads((round_dir / "packet.json").read_text(encoding="utf-8")) == packet
        run_dir = round_dir / f"chk{packet['check_id']:06d}"
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        assert result["request_id"] == f"chk{packet['check_id']:06d}"
        assert result["decision"] == decision
        assert result["provenance"]["source_sha256"] == \
            hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        for name in ("source.bin", "frame.png", "annotated.png"):
            assert (run_dir / name).exists(), name
        assert result["targets"] and all((run_dir / t["roi_path"]).exists()
                                         for t in result["targets"])
        # 快照核对器（C04 §2.3 + NC Q3 细则）：绑定/源哈希/ROI 像素哈希链；ROI 篡改必须拒绝
        from round_artifacts import SnapshotError, load_snapshot
        service_root = out / "service"
        snap = load_snapshot(service_root, packet["session_id"], packet["check_id"])
        assert snap["sha256"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        assert snap["engine_result"] is not None and snap["engine_result"]["targets"]
        roi = run_dir / snap["engine_result"]["targets"][0]["roi_path"]
        original_roi = roi.read_bytes()
        roi.write_bytes(b"\x89PNG-tampered-roi")
        try:
            load_snapshot(service_root, packet["session_id"], packet["check_id"])
            raise AssertionError("tampered ROI accepted")
        except SnapshotError:
            pass
        roi.write_bytes(original_roi)
        assert load_snapshot(service_root, packet["session_id"],
                             packet["check_id"])["sha256"] == snap["sha256"]
        # The same loaded model serves automatic memory rounds with identical predictions.
        for expected_id in (2, 3):
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/v1/check",
                b'{}', {"Content-Type": "application/json"})
            automatic = validate_packet(json.loads(urllib.request.urlopen(request, timeout=60).read()))
            assert automatic["check_id"] == automatic["frame_id"] == expected_id
            assert automatic["targets"] == packet["targets"]
            assert automatic["decision"] == packet["decision"]
            assert "trigger_ref" not in automatic
            session_dir = round_dir.parent
            assert not (session_dir / f"check-{expected_id:06d}").exists()
            assert json.loads((session_dir / "latest_packet.json").read_text()) == automatic
        assert loads.call_count == 1, loads.call_count
        assert not list(out.rglob("*.pending"))
    finally:
        server.shutdown()
        server.server_close()
        model_spy.stop()
    print("PASS: live service real engine (golden counts, manual artifacts, memory parity, one model load)")


if __name__ == "__main__":
    main()
