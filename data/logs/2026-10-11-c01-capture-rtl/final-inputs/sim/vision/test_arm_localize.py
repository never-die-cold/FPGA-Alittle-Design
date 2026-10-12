"""文件运行器：固定数据、拒绝路径与来源元数据；产物保留在仓库内。"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from arm_localize import run, export_crops

SOURCE = ROOT / "data/evidence/2026-10-03-arm-localize-baseline/two_targets.json"
OUT = ROOT / "sim/build/arm-localize-test"
OUT.mkdir(parents=True, exist_ok=True)
result = run(SOURCE, OUT / "result.json", (4, 3), 7, 3)
assert [t["bbox"] for t in result["targets"]] == [[1, 1, 2, 4], [7, 2, 9, 5]]
assert [t["pixels"] for t in result["crops"]] == [[[20]*4]*3, [[30]*4]*3]
assert all(t["frame_id"] == 7 and t["config_id"] == 3 for t in result["crops"])
assert result["source"]["sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert result["mode"] == "FILE_REFERENCE" and all(v >= 0 for v in result["timing_ms"].values())
assert json.loads((OUT / "result.json").read_text()) == result
for artifact, target in zip(result["artifacts"], result["crops"]):
    assert artifact["target_id"] == target["target_id"] and artifact["bbox"] == target["bbox"]
    assert artifact["frame_id"] == 7 and artifact["config_id"] == 3
    flattened = bytes(p for row in target["pixels"] for p in row)
    for extension in ("pgm", "hex"):
        content = (OUT / artifact[extension]["path"]).read_bytes()
        assert artifact[extension]["sha256"] == hashlib.sha256(content).hexdigest()
        assert content == (b"P5\n4 3\n255\n" + flattened if extension == "pgm" else
                           "".join(f"{p:02x}\n" for p in flattened).encode("ascii"))
order = export_crops([{**result["crops"][0], "input_size": [2, 2],
                       "pixels": [[0, 64], [128, 255]]}], OUT / "order.json")[0]
assert (OUT / order["pgm"]["path"]).read_bytes() == b"P5\n2 2\n255\n\x00\x40\x80\xff"
assert (OUT / order["hex"]["path"]).read_bytes() == b"00\n40\n80\nff\n"
stale = run(SOURCE, OUT / "reuse.json")
fresh = run(SOURCE, OUT / "reuse.json", max_targets=1)
assert fresh["artifacts"] == [] and json.loads((OUT / "reuse.json").read_text())["artifacts"] == []
assert stale["artifacts"] and (OUT / stale["artifacts"][0]["pgm"]["path"]).is_file()
limited = run(SOURCE, OUT / "limit.json", max_targets=1)
assert limited["status"] == "RECHECK_TARGET_LIMIT" and limited["crops"] == []
for name, pixels, status in (("empty", [[240]*12]*8, "LOCATION_ONLY"),
                             ("border", [[20]*4]*4, "RECHECK_BORDER")):
    image = OUT / (name + ".json")
    image.write_text(json.dumps({"pixels": pixels}), encoding="utf-8")
    checked = run(image, OUT / (name + "-result.json"))
    assert checked["status"] == status and checked["crops"] == []
for kwargs in ({"size": (0, 4)}, {"output": SOURCE}):
    try:
        run(SOURCE, **({"output": OUT / "rejected.json"} | kwargs))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid size or input overwrite accepted")
bad = OUT / "bad.json"
bad.write_text('{"pixels": [[true]]}', encoding="utf-8")
process = subprocess.run([sys.executable, str(ROOT / "src/pynq_host/arm_localize.py"),
                          str(bad), str(OUT / "bad-result.json")], capture_output=True, text=True)
assert process.returncode == 1 and process.stderr.startswith("FAIL:")
assert bad.read_text() == '{"pixels": [[true]]}'
before = (OUT / "result.json").read_bytes()
try:
    run(bad, OUT / "result.json")
except ValueError:
    pass
else:
    raise AssertionError("invalid input accepted")
assert (OUT / "result.json").read_bytes() == before
with patch("arm_localize.export_crops", side_effect=OSError("injected export failure")):
    try:
        run(SOURCE, OUT / "result.json")
    except OSError:
        pass
    else:
        raise AssertionError("export failure ignored")
assert (OUT / "result.json").read_bytes() == before
assert not list(OUT.glob("*.pending"))
cli = subprocess.run([sys.executable, "-B", str(ROOT / "src/pynq_host/arm_localize.py"),
                      str(SOURCE.relative_to(ROOT)), str((OUT / "cli.json").relative_to(ROOT)),
                      "--size", "4", "3", "--frame-id", "7", "--config-id", "3"],
                     cwd=ROOT, capture_output=True, text=True)
assert cli.returncode == 0 and cli.stdout.startswith("PASS:"), cli.stderr
assert json.loads((OUT / "cli.json").read_text())["crops"] == result["crops"]
print("PASS: file localization exact boxes/crops, metadata, empty/recheck and invalid input")
print("PASS: PGM/hex exact row order, hashes, target association and stale manifest isolation")
if len(sys.argv) == 3:
    pc, arm = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:])
    for field in ("schema_version", "mode", "frame_id", "config_id", "width", "height", "status", "targets", "crops", "crop_size", "source", "parameters", "reference_sha256"):
        assert pc[field] == arm[field], field
    assert arm["runtime"]["machine"] == "armv7l"
    if "artifacts" in pc and "artifacts" in arm:
        assert len(pc["artifacts"]) == len(arm["artifacts"])
        for left, right in zip(pc["artifacts"], arm["artifacts"]):
            assert {k: v for k, v in left.items() if k not in ("pgm", "hex")} == {k: v for k, v in right.items() if k not in ("pgm", "hex")}
            assert all(left[ext]["sha256"] == right[ext]["sha256"] for ext in ("pgm", "hex"))
    print("PASS: ARM/PC boxes, crop pixels, parameters and input/reference hashes match")
