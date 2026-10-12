"""批次记录 CSV 导出（src/vision_client/export_records.py）离线测试。

纯 stdlib；落盘在仓库内 sim/build/vision/export-test/。
覆盖：表头与行数、关键字段、targets JSON 单元格、UTF-8-BOM（Excel 兼容）、
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
from vision_protocol import mock_packet


def main():
    out = root / "sim/build/vision/export-test"
    if out.exists():
        shutil.rmtree(out)
    rec = BatchRecords(out, save_image=lambda path, frame: True)
    rec.write(mock_packet("sess-export-0001", 7, 2, 5), None)
    rec.write(mock_packet("sess-export-0001", 8, 2, 6), None)
    csv_path, count = export_records(out)
    assert count == 2 and csv_path.name == "records.csv"
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf"), "missing UTF-8 BOM"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    row = rows[0]
    assert row["check_id"] == "5" and row["mode"] == "MOCK" and row["target_count"] == "2"
    assert row["screenshot"] == "screenshots/mock_sess-exp_000005.png"
    assert json.loads(row["targets"])[0]["bbox"] == [180, 170, 339, 289]
    try:
        export_records(out / "missing")
        raise AssertionError("missing records file accepted")
    except FileNotFoundError:
        pass
    print("PASS: records CSV export header/rows/targets/BOM + missing-file error")


if __name__ == "__main__":
    main()
