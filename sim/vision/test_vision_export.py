"""批次记录 CSV 导出（src/vision_client/export_records.py）离线测试。

纯 stdlib；落盘在仓库内 sim/build/vision/export-test/。
覆盖：表头与行数、关键字段、v2 派生列（status/missing/extra/prototype）、
targets JSON 单元格、v1 旧记录兼容、UTF-8-BOM（Excel 兼容）、
记录文件缺失时报错（不静默产出空表）。
"""
import csv
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from export_records import export_records
from records import BatchRecords
from vision_mock_service import live_packet
from vision_protocol import mock_packet


def main():
    out = root / "sim/build/vision/export-test"
    if out.exists():
        shutil.rmtree(out)
    rec = BatchRecords(out, save_image=lambda path, frame: True)
    rec.write(mock_packet("sess-export-0001", 7, 2, 5), None)
    rec.write(mock_packet("sess-export-0001", 8, 2, 6), None)
    rec.write(live_packet("sess-export-0001", 9, 2, 9), None)  # (9+2)%3=2 → RECHECK+prototype
    # v1 旧记录（verdict 预留字段、无 status/decision）：导出必须兼容，不炸不丢
    v1_row = {"schema_version": 1, "mode": "LIVE", "session_id": "sess-export-0001",
              "check_id": 10, "config_id": 2, "frame_id": 11,
              "recorded_at": "2026-10-10T00:00:00", "result_age_s": 0.2, "created_at": 0,
              "target_count": 1, "targets": [], "verdict": None, "screenshot": "screenshots/x.png"}
    with (out / "records.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(v1_row) + "\n")
    csv_path, count = export_records(out)
    assert count == 4 and csv_path.name == "records.csv"
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf"), "missing UTF-8 BOM"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    row = rows[0]
    assert row["check_id"] == "5" and row["mode"] == "MOCK" and row["target_count"] == "2"
    assert row["status"] == "LOCATION_ONLY" and row["prototype"] == "0"
    assert row["missing"] == "" and row["extra"] == ""
    assert row["screenshot"] == "screenshots/mock_sess-exp_000005.png"
    assert json.loads(row["targets"])[0]["bbox"] == [180, 170, 339, 289]
    proto_row = rows[2]
    assert proto_row["mode"] == "LIVE" and proto_row["prototype"] == "1"
    assert proto_row["status"] == "RECHECK" and proto_row["missing"] == "washer:1"
    assert proto_row["extra"] == "" and proto_row["reasons"] == "low score T5"
    v1_csv = rows[3]
    assert v1_csv["status"] == "LOCATION_ONLY" and v1_csv["prototype"] == "0"
    assert v1_csv["verdict"] == "" and v1_csv["missing"] == "" and v1_csv["reasons"] == ""
    try:
        export_records(out / "missing")
        raise AssertionError("missing records file accepted")
    except FileNotFoundError:
        pass
    print("PASS: records CSV v2 columns (status/missing/extra/prototype) + v1 compat + BOM + errors")


if __name__ == "__main__":
    main()
