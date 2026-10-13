"""C02 software golden inputs for RTL arithmetic, no hardware/model claim."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/coprocessor"))
from int8_reference import requantize_i8, gap_average256, classify_logits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if ROOT not in output.parents:
        raise ValueError("goldens must be inside repository")
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    rng = random.Random(20261013)
    cases = [(a, m, s, r) for a in (-(1 << 31), -1025, -129, -127, -5, -3, -1,
                0, 1, 3, 5, 127, 129, 1025, (1 << 31)-1)
             for m in (1, 3, 127, (1 << 31)-1) for s in range(63) for r in (0, 1)]
    cases += [(rng.randrange(-(1 << 31), 1 << 31), rng.randrange(1, 1 << 31),
               rng.randrange(63), rng.randrange(2)) for _ in range(512)]
    cases += [(123, 0, 0, 0), (-123, 1 << 31, 1, 0), (7, 1, 63, 0)]
    rows = []
    for a, m, s, r in cases:
        error = not 1 <= m < 1 << 31 or not 0 <= s <= 62
        expected = 0 if error else requantize_i8(max(a, 0) if r else a, m, s)
        rows.append(f"{a & 0xffffffff:08x} {m:08x} {s} {r} {expected & 255:02x} {int(error)}")
    records["requant"] = rows
    records["gap"] = [f"{s:08x} {gap_average256(s):02x} 0" for s in range(32513)]
    records["gap"] += ["00007f01 00 1", "ffffffff 00 1"]
    cases = [(tuple(margin-127 if i == winner else -127 for i in range(3)), threshold)
             for margin in range(255) for winner in range(3) for threshold in (0, margin, min(255, margin+1))]
    cases += [((v, v, v), 1) for v in (-127, -1, 0, 127)]
    cases += [(tuple(rng.randrange(-127, 128) for _ in range(3)), rng.randrange(256)) for _ in range(512)]
    cases += [((-128, 0, 1), 0), ((1, -128, 0), 1), ((0, 1, -128), 2)]
    rows = []
    for logits, threshold in cases:
        error = -128 in logits
        result = {"class_id": 3, "margin_q": 0, "score_q15": 0, "low_conf": True} if error else classify_logits(logits, threshold)
        rows.append(" ".join([*(f"{value & 255:02x}" for value in logits), str(threshold),
            str(result["class_id"]), str(result["margin_q"]), str(result["score_q15"]),
            str(int(result["low_conf"])), str(int(error))]))
    records["logits"] = rows
    manifest = {"kind": "C02_DIAGNOSTIC_ARITHMETIC", "seed": 20261013,
        "reference_sha256": hashlib.sha256((ROOT/"src/coprocessor/int8_reference.py").read_bytes()).hexdigest(),
        "files": {}}
    for name, rows in records.items():
        payload = ("\n".join(rows) + "\n").encode("ascii")
        (output/f"{name}.txt").write_bytes(payload)
        manifest["files"][name] = {"vectors": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print("PASS: C02 arithmetic goldens", {name: len(rows) for name, rows in records.items()})


if __name__ == "__main__":
    main()
