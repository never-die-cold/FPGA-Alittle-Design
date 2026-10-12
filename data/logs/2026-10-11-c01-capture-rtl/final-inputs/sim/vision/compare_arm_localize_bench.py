"""对比已留存的 PC/ARM 原始样本与导出文件，不用 timing/runtime 作相等判据。"""
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compare(pc_root, arm_root):
    pc, arm = load(pc_root / "summary.json"), load(arm_root / "summary.json")
    assert arm["runtime"]["machine"] == "armv7l"
    assert pc["reference_sha256"] == arm["reference_sha256"]
    assert pc["warmup"] == arm["warmup"] and pc["repeats"] == arm["repeats"]
    assert [c["name"] for c in pc["cases"]] == [c["name"] for c in arm["cases"]]
    fields = ("schema_version", "mode", "frame_id", "config_id", "width", "height", "status",
              "targets", "crops", "crop_size", "source", "parameters", "reference_sha256")
    checked = 0
    for left_case, right_case in zip(pc["cases"], arm["cases"]):
        assert len(left_case["samples"]) == len(right_case["samples"]) == pc["repeats"]
        for left_sample, right_sample in zip(left_case["samples"], right_case["samples"]):
            left_path, right_path = pc_root / left_sample["result"], arm_root / right_sample["result"]
            left, right = load(left_path), load(right_path)
            for path, record in ((left_path, left), (right_path, right)):
                assert hashlib.sha256((path.parent / record["source"]["name"]).read_bytes()).hexdigest() == record["source"]["sha256"]
            assert all(left[field] == right[field] for field in fields)
            assert len(left["artifacts"]) == len(right["artifacts"])
            for left_file, right_file in zip(left["artifacts"], right["artifacts"]):
                for key in ("target_id", "frame_id", "config_id", "bbox", "pixel_format", "size"):
                    assert left_file[key] == right_file[key]
                for extension in ("pgm", "hex"):
                    left_bytes = (left_path.parent / left_file[extension]["path"]).read_bytes()
                    right_bytes = (right_path.parent / right_file[extension]["path"]).read_bytes()
                    assert left_bytes == right_bytes
                    assert hashlib.sha256(left_bytes).hexdigest() == left_file[extension]["sha256"] == right_file[extension]["sha256"]
            checked += 1
    print(f"PASS: PC/ARM benchmark {len(pc['cases'])} cases, {checked} samples, exact boxes/pixels/PGM/hex/hashes")


if __name__ == "__main__":
    try:
        compare(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError, AssertionError, KeyError, IndexError) as exc:
        print(f"FAIL: benchmark comparison {exc}", file=sys.stderr)
        sys.exit(1)
