"""批次记录存储（src/vision_client/records.py）离线测试——D8–D10 语义。

纯 stdlib：截图写入用桩回调替代 cv2；落盘在仓库内 sim/build/vision/records-test/。
覆盖：手动轮次落记录、键 (session,check_id) 去重、MOCK 前缀、字段完整性、LIVE 无前缀。
"""
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from records import AnomalyLog, BatchRecords
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
    live = {**packet, "mode": "LIVE", "check_id": 7}  # LIVE 记录文件名不带 mock_ 前缀（D10）
    shot_live = rec.write(live, None)
    assert not shot_live.name.startswith("mock_") and shot.name.startswith("mock_")
    lines = (out / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    row = json.loads(lines[0])
    assert row["mode"] == "MOCK" and row["check_id"] == 5 and row["frame_id"] == 7
    assert row["config_id"] == 2 and row["schema_version"] == 1
    assert row["target_count"] == 2 and row["targets"][0]["bbox"] == [180, 170, 339, 289]
    assert row["verdict"] is None
    assert row["screenshot"] == "screenshots/mock_sess-abc_000005.png"
    assert written[0] == out / "screenshots/mock_sess-abc_000005.png"
    # D11：异常事件日志（AnomalyLog）独立成文件，截图按序编号，LIVE 不带 mock_ 前缀
    anomaly_shots = []
    anom = AnomalyLog(out, save_image=lambda path, frame: anomaly_shots.append(path) or True)
    first = anom.log("MOCK", {"kind": "overlay_outage", "prev": "ok", "check_id": 4, "fails": 3}, None)
    anom.log("LIVE", {"kind": "overlay_ok", "prev": "outage", "check_id": 4, "fails": 0}, None)
    assert first.name == "mock_anomaly_0001.png" and anom.count == 2
    assert not anomaly_shots[1].name.startswith("mock_")
    a_lines = (out / "anomalies.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(a_lines) == 2
    arow = json.loads(a_lines[0])
    assert arow["kind"] == "overlay_outage" and arow["prev"] == "ok"
    assert arow["check_id"] == 4 and arow["fails"] == 3 and arow["mode"] == "MOCK"
    assert arow["screenshot"] == "screenshots/mock_anomaly_0001.png"
    print("PASS: batch records key-dedup/mock-prefix/fields + anomaly events (D8-D11)")


if __name__ == "__main__":
    main()
