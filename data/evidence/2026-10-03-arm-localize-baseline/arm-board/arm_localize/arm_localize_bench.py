#!/usr/bin/env python3
"""固定合成输入的软件性能基线；原始输入、每次结果和统计均保留在输出目录。"""
import argparse
import datetime
import json
import math
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_localize import run


def summarize(values):
    return {"min": min(values), "median": statistics.median(values),
            "p95": sorted(values)[math.ceil(0.95 * len(values))-1], "max": max(values)}


def image_for(case):
    if case == "tiny":
        root = Path(__file__).resolve().parent
        source = root / "two_targets.json"
        if not source.is_file():
            source = root.parents[1] / "data/evidence/2026-10-03-arm-localize-baseline/two_targets.json"
        return json.loads(source.read_text(encoding="utf-8"))["pixels"]
    image = [[240] * 1280 for _ in range(720)]
    if case == "720p_six":
        boxes = [(90, 90, 32, 24), (460, 130, 48, 32), (900, 80, 64, 40),
                 (130, 460, 80, 48), (590, 410, 48, 64), (1020, 470, 72, 52)]
        for index, (x0, y0, width, height) in enumerate(boxes):
            for y in range(y0, y0+height):
                for x in range(x0, x0+width):
                    image[y][x] = 20 + index*7 + ((x-x0) + 2*(y-y0)) % 13
    return image


def benchmark(output, cases, warmup=1, repeats=5, size=(64, 64)):
    if warmup < 0 or repeats < 2 or min(size) < 1:
        raise ValueError("warmup>=0, repeats>=2 and positive size required")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix="run-", dir=output))
    report = {"schema_version": 1, "mode": "SYNTHETIC_FILE_REFERENCE",
              "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "warmup": warmup, "repeats": repeats, "crop_size": list(size),
              "p95_method": "nearest-rank; five samples means p95=max", "cases": []}
    for case_index, case in enumerate(cases):
        folder = session / case
        folder.mkdir()
        source = folder / "input.json"
        source.write_text(json.dumps({"pixels": image_for(case)}, separators=(",", ":")), encoding="utf-8")
        for index in range(warmup):
            run(source, folder / f"warmup-{index:02d}.json", size, 100+case_index, 7)
        samples = []
        for index in range(repeats):
            destination = folder / f"sample-{index:02d}.json"
            started = time.perf_counter_ns()
            result = run(source, destination, size, 100+case_index, 7)
            elapsed = (time.perf_counter_ns()-started)/1e6
            expected = {"tiny": 2, "720p_empty": 0, "720p_six": 6}[case]
            if result["status"] != "LOCATION_ONLY" or len(result["targets"]) != expected:
                raise ValueError(f"unexpected synthetic case result: {case}")
            samples.append({"result": destination.relative_to(output).as_posix(),
                            **result["timing_ms"], "total_call": elapsed})
            print(f"INFO: {case} sample={index+1}/{repeats} total_ms={elapsed:.3f}", flush=True)
        report["cases"].append({"name": case, "width": result["width"], "height": result["height"],
                                "targets": len(result["targets"]), "samples": samples,
                                "stats_ms": {key: summarize([s[key] for s in samples])
                                             for key in ("locate", "crop", "total_call")}})
        report["runtime"] = result["runtime"]
        report["reference_sha256"] = result["reference_sha256"]
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: synthetic benchmark {len(cases)} cases, warmup={warmup}, repeats={repeats}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", choices=("tiny", "720p_empty", "720p_six"),
                        default=("tiny", "720p_empty", "720p_six"))
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--size", nargs=2, type=int, default=(64, 64))
    args = parser.parse_args()
    try:
        benchmark(args.out, args.cases, args.warmup, args.repeats, args.size)
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: benchmark {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
