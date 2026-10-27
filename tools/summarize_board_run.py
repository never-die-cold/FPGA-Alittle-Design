#!/usr/bin/env python3
"""Summarize NC loader JSON/serial logs; verdict is data-only, not board acceptance."""
import argparse, csv, json, re
from pathlib import Path
FIELDS = ("class_id", "margin_q", "score_q15", "low_conf", "logits")
def integer(value):
    return int(value, 0) if isinstance(value, str) else int(value)
def read_expected(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["case"]: row for row in csv.DictReader(stream, delimiter="\t")}
def collect(root):
    clocks, status_groups, runs = [], [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".json", ".txt", ".log"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        objects = []
        if path.suffix.lower() == ".json":
            try:
                objects.append(json.loads(text))
            except json.JSONDecodeError:
                pass
        else:
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        objects.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if "fclk1_mhz" in obj:
                clocks.append((str(path), float(obj["fclk1_mhz"])))
            if "status_first_reads" in obj:
                status_groups.append((str(path), [integer(v) for v in obj["status_first_reads"]]))
            if "case" in obj:
                runs.append((str(path), obj))
        for match in re.finditer(r"measured_fclk1_mhz=([0-9.]+)", text):
            clocks.append((str(path), float(match.group(1))))
        for match in re.finditer(r"status_first_reads=([^\r\n]+)", text):
            values = re.findall(r"0x[0-9a-fA-F]+|\b\d+\b", match.group(1))
            status_groups.append((str(path), [integer(value) for value in values]))
    return clocks, status_groups, runs
def summarize(root, expected_path):
    expected = read_expected(expected_path)
    clocks, status_groups, runs = collect(root)
    rows, passed = [], True
    def check(source, case, field, observed, wanted, match):
        nonlocal passed
        passed &= match
        rows.append((source, case, field, str(observed), str(wanted), "MATCH" if match else "MISMATCH"))
    if not clocks: check("-", "clock", "fclk1_mhz", "MISSING", "40.000000", False)
    for source, value in clocks:
        check(source, "clock", "fclk1_mhz", f"{value:.6f}", "40.000000", value == 40.0)
    if not status_groups: check("-", "clock", "first_STATUS", "MISSING", "0x00000001", False)
    for index, (source, values) in enumerate(status_groups):
        observed = "MISSING" if not values else f"0x{values[0]:08x}"
        check(source, f"status_group_{index}", "first_STATUS", observed, "0x00000001",
              bool(values) and values[0] == 1)
    if not runs: check("-", "result", "loader_JSON", "MISSING", "pattern/zero", False)
    for source, run in runs:
        case = str(run["case"]); wanted = expected.get(case)
        if wanted is None:
            check(source, case, "case", case, "known case", False); continue
        error = integer(run.get("error_code", -1))
        sequence = integer(run.get("result_seq", 0))
        check(source, case, "ERROR_CODE", f"0x{error & 0xffffffff:08x}", "0x00000000", error == 0)
        check(source, case, "RESULT_SEQ", sequence, ">0", sequence > 0)
        for field in FIELDS:
            observed = run.get(field, "MISSING")
            target = wanted[field]
            if field == "logits":
                observed = ",".join(map(str, observed)) if isinstance(observed, list) else str(observed)
            else:
                try:
                    observed = integer(observed)
                    target = integer(target)
                except (TypeError, ValueError):
                    pass
            check(source, case, field, observed, target, observed == target)
    header = "source\tcase\tfield\tobserved\texpected\tverdict"
    body = ["\t".join(row) for row in rows]
    body += [f"DATA_CHECK={'PASS' if passed else 'FAIL'}",
             "NOTE=data-layer verdict only; it does not declare board acceptance"]
    return passed, "\n".join([header] + body) + "\n"
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path); parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    passed, report = summarize(args.input, args.expected)
    if args.output: args.output.write_bytes(report.encode("utf-8"))
    print(report, end="")
    return 0 if passed else 1
if __name__ == "__main__":
    raise SystemExit(main())
