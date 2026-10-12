"""批次记录存储（src/vision_client/records.py）离线测试——D8–D10 语义 + W07 schema v2。

纯 stdlib：截图写入用桩回调替代 cv2；落盘在仓库内 sim/build/vision/records-test/。
覆盖：手动轮次落记录、键 (session,check_id) 去重、来源前缀（mock_/proto_/无）、
字段完整性（v2：status/decision/prototype/protocol_version）、LIVE 无前缀。
"""
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from records import AnomalyLog, BatchRecords
from vision_mock_service import live_packet
from vision_protocol import mock_packet


def main():
    out = root / "sim/build/vision/records-test"
    if out.exists():
        shutil.rmtree(out)
    written = []
    rec = BatchRecords(out, save_image=lambda path, frame: written.append(path) or True)
    packet = mock_packet("sess-abcd-1234", 7, 2, 5)
    assert rec.accept(packet) and rec.count == 0
    shot = rec.write(packet, None)
    assert rec.count == 1 and not rec.accept(packet)
    assert rec.write(packet, None) is None  # D9 去重：同键重复写入被拒
    rec.write(mock_packet("sess-abcd-1234", 8, 2, 6), None)  # 不同 check_id 可写
    assert rec.count == 2
    live = {**packet, "mode": "LIVE", "check_id": 7}  # 真实 LIVE：无前缀（D10）
    shot_live = rec.write(live, None)
    assert not shot_live.name.startswith(("mock_", "proto_")) and shot.name.startswith("mock_")
    rec.write(mock_packet("sess-abcd-1234", 9, 2, 8), None, age_s=0.25)  # EXE 接收时基年龄优先
    # LIVE+prototype（离线产物代实时，C04 Q2）：proto_ 前缀 + decision 原样入记录
    proto_packet = live_packet("sess-abcd-1234", 10, 2, 9)  # (9+2)%3=2 → RECHECK
    assert proto_packet["prototype"] is True and proto_packet["status"] == "RECHECK"
    rec.write(proto_packet, None)
    assert rec.count == 5
    lines = (out / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    row = json.loads(lines[0])
    assert row["mode"] == "MOCK" and row["check_id"] == 5 and row["frame_id"] == 7
    assert row["config_id"] == 2 and row["schema_version"] == 2
    assert row["target_count"] == 2 and row["targets"][0]["bbox"] == [180, 170, 339, 289]
    # v2：MOCK/LOCATION_ONLY 行 decision 为 null、prototype=False；无 v1 verdict 字段
    assert row["status"] == "LOCATION_ONLY" and row["decision"] is None
    assert row["prototype"] is False and row["protocol_version"] == 1
    assert "verdict" not in row
    assert row["created_at"] == packet["created_at"]
    assert row["screenshot"] == "screenshots/mock_sess-abc_000005.png"
    assert written[0] == out / "screenshots/mock_sess-abc_000005.png"
    assert json.loads(lines[3])["result_age_s"] == 0.25
    proto_row = json.loads(lines[4])
    assert proto_row["prototype"] is True and proto_row["status"] == "RECHECK"
    assert proto_row["decision"]["missing"] == {"bolt": 0, "nut": 0, "washer": 1}
    assert proto_row["decision"]["expected"] == {"bolt": 2, "nut": 2, "washer": 2}
    assert proto_row["screenshot"].startswith("screenshots/proto_")
    live_row = json.loads(lines[2])
    assert not live_row["screenshot"].startswith(("screenshots/proto_", "screenshots/mock_"))
    # D11：异常事件日志（AnomalyLog）独立成文件；prototype 会话的异常截图同样带 proto_ 前缀
    anomaly_shots = []
    anom = AnomalyLog(out, save_image=lambda path, frame: anomaly_shots.append(path) or True)
    first = anom.log("MOCK", {"kind": "overlay_outage", "prev": "ok", "check_id": 4, "fails": 3}, None)
    anom.log("LIVE", {"kind": "overlay_ok", "prev": "outage", "check_id": 4, "fails": 0}, None)
    anom.log("LIVE", {"kind": "overlay_stale", "prev": "ok", "check_id": 4, "fails": 0}, None,
             prototype=True)
    assert first.name == "mock_anomaly_0001.png" and anom.count == 3
    assert not anomaly_shots[1].name.startswith(("mock_", "proto_"))
    assert anomaly_shots[2].name.startswith("proto_")
    a_lines = (out / "anomalies.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(a_lines) == 3
    arow = json.loads(a_lines[0])
    assert arow["kind"] == "overlay_outage" and arow["prev"] == "ok"
    assert arow["check_id"] == 4 and arow["fails"] == 3 and arow["mode"] == "MOCK"
    assert arow["screenshot"] == "screenshots/mock_anomaly_0001.png"
    assert json.loads(a_lines[2])["prototype"] is True
    print("PASS: batch records v2 (decision/status/prototype/prefixes) + anomaly events (D8-D11)")


if __name__ == "__main__":
    main()
