"""Board-only exact multi-target and repeated-job check on frozen ROI bytes."""
import argparse
import fcntl
import hashlib
import json
import math
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("package", "vectors", "app-root", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new directory")
    sys.path.insert(0, str(args.app_root / "src/pynq_host"))
    sys.path.insert(0, str(args.package / "payload/tools"))
    from cop_payload_loader import preflight, prepare_board
    from cop_driver import CopDriver, PynqDmaPlane, PynqMmio
    from pynq import MMIO, allocate
    manifest, payload, _, _, _ = preflight(args.package, "roi_001")
    vectors = json.loads((args.vectors / "manifest.json").read_bytes())
    if hashlib.sha256(payload).hexdigest() != vectors["payload_sha256"]:
        raise ValueError("payload differs from frozen integer expectations")
    inputs = []
    for row in vectors["rois"][1:]:
        raw = (args.vectors / row["path"]).read_bytes()
        if len(raw) != 4096 or hashlib.sha256(raw).hexdigest() != row["roi_sha256"]:
            raise ValueError("ROI byte/hash mismatch")
        inputs.append((row, raw))
    if not inputs:
        raise ValueError("no scene ROI vectors")
    lock = Path("/home/xilinx/fpga-product.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    args.output.mkdir(parents=True)
    _, actual_clock = prepare_board(args.package, 1)[:2]
    cop = PynqMmio(MMIO(0x40000000, 4096), 0x40000000)
    plane = PynqDmaPlane(MMIO(0x40010000, 65536), MMIO(0x40020000, 65536),
                         cop, allocate, max_targets=10, timeout=15)
    driver = CopDriver(cop, plane, {"bolt": 3, "nut": 3, "washer": 3}, .8, 10, 10,
                       model_payload=payload, model_id=manifest["model_id"],
                       addresses=plane.addresses, dma_after_commit=True,
                       job_timeout_s=20, accept_timeout_s=5)
    schedules = [inputs[:1], inputs[:3], inputs, list(reversed(inputs)),
                 [inputs[i % len(inputs)] for i in range(10)], inputs]
    reports = []
    try:
        for number, schedule in enumerate(schedules, 1):
            job = {"job_id": number, "work_order_rev": 1, "capture_id": number,
                   "source_config_id": 1, "timeout_cycles": 400000000,
                   "targets": [{"target_id": i, "roi": raw}
                               for i, (_, raw) in enumerate(schedule)]}
            result = driver.run(job)
            checks = []
            for index, ((expected, _), actual) in enumerate(zip(schedule, result["targets"])):
                logits = [v-256 if v > 127 else v for v in actual["logits"]]
                ranked = sorted(range(3), key=lambda i: (-expected["logits"][i], i))
                margin = expected["logits"][ranked[0]]-expected["logits"][ranked[1]]
                checks.append({"target_id": index, "case": expected["name"],
                    "expected_logits": expected["logits"], "actual": actual,
                    "match": logits == expected["logits"] and actual["target_id"] == index
                    and actual["valid"] == 1 and actual["error"] == 0
                    and actual["class"] == ("bolt", "nut", "washer")[ranked[0]]
                    and actual["margin_q"] == margin
                    and actual["score_q15"] == (margin*32767+127)//254
                    and bool(actual["low_conf"]) == (margin < math.ceil(.8*254))})
            record = {"job": number, "count": len(schedule), "checks": checks,
                      "result": result, "pass": len(checks) == len(schedule)
                      and all(item["match"] for item in checks)}
            (args.output/f"job-{number:02d}.json").write_text(json.dumps(record, indent=2)+"\n")
            reports.append(record)
            driver.consume(result)
            print(f"BOARD_JOB job={number} count={len(schedule)} seq={result['result_seq']} pass={record['pass']}", flush=True)
            if not record["pass"]:
                raise RuntimeError("hardware differs from frozen integer expectations")
        summary = {"pass": True, "jobs": len(reports), "targets": sum(r["count"] for r in reports),
                   "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                   "fclk1_mhz": actual_clock,
                   "payload_sha256": vectors["payload_sha256"],
                   "bit_sha256": hashlib.sha256((args.package/"payload/pynq_cop_40mhz.bit").read_bytes()).hexdigest(),
                   "result_sequences": [r["result"]["result_seq"] for r in reports]}
        (args.output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
        print(json.dumps(summary), flush=True)
    except Exception as error:
        failure = {"pass": False, "exception": repr(error), "completed_jobs": len(reports),
                   "snapshot": driver.terminal_snapshot("numeric_bench_failure")}
        (args.output/"failure.json").write_text(json.dumps(failure, indent=2)+"\n")
        raise
    finally:
        plane.free()


if __name__ == "__main__":
    main()
