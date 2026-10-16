"""批次记录 CSV 导出（M4「记录导出」项）：records.jsonl → 表格（Excel 可读）。

用法：
    py export_records.py <records-dir> [--out PATH]

默认输出 <records-dir>/records.csv；编码 UTF-8-BOM（Excel 双击打开中文不乱码）。
targets 列保留 JSON 原文（含 bbox）；screenshot 列保留相对路径（与记录目录同级引用）。
记录文件不存在时报错退出（不静默产出空表）。
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FIELDS = ["recorded_at", "mode", "prototype", "status", "missing", "extra", "reasons",
          "session_id", "check_id", "config_id", "frame_id",
          "result_age_s", "target_count", "screenshot", "targets", "verdict"]


def _derive(row):
    """v2 行取 status/decision；v1 行（verdict 预留、无 decision）退化为 LOCATION_ONLY。

    reasons 列承载判定原因（如 target_limit——超限轮次的"部分计数"标识，C04 Q5）：
    没有该列时，超限重算计数与完整计数在导出件里无法区分。
    """
    decision = row.get("decision") or {}
    status = decision.get("verdict") or row.get("status") or row.get("verdict") or "LOCATION_ONLY"
    missing = ";".join(f"{name}:{n}" for name, n in decision.get("missing", {}).items() if n)
    extra = ";".join(f"{name}:{n}" for name, n in decision.get("extra", {}).items() if n)
    reasons = ";".join(decision.get("reasons", []) or [])
    return status, missing, extra, reasons


def load_records(records_dir):
    path = Path(records_dir) / "records.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no records file: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def export_records(records_dir, out_path=None):
    """返回 (输出路径, 记录条数)。"""
    rows = load_records(records_dir)
    out = Path(out_path) if out_path else Path(records_dir) / "records.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row = dict(row)
            status, missing, extra, reasons = _derive(row)
            row["status"] = status
            row["missing"] = missing
            row["extra"] = extra
            row["reasons"] = reasons
            row["prototype"] = int(bool(row.get("prototype")))
            row["targets"] = json.dumps(row.get("targets", []), ensure_ascii=False)
            writer.writerow(row)
    return out, len(rows)


def main():
    parser = argparse.ArgumentParser(description="批次记录 JSONL -> CSV 导出")
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    out, count = export_records(args.records_dir, args.out)
    print(f"PASS: exported {count} records -> {out}")


if __name__ == "__main__":
    main()
