"""Validate repository evidence and recompute the module-one comparison matrix."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("nofwd", "fwd", "bht1", "bht2")


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(folder):
    require(read(folder / "all-final.exit.txt").strip() == "0", "Full regression did not exit zero")
    require(read(folder / "arch-final.exit.txt").strip() == "0", "Arch matrix did not exit zero")
    all_log = read(folder / "all-final.log")
    runs = re.findall(r"^== coremark mode=(\d+) hex=(\S+) exit=(\d+) tohost=(\d+) cycles=(\d+) retired=(\d+) bubbles=(\d+)", all_log, re.M)
    bht = re.findall(r"^BHT: mode=(\d+) lookup=(\d+) hit=(\d+) miss=(\d+)", all_log, re.M)
    passes = re.findall(r"^PASS: coremark[^\r\n]*", all_log, re.M)
    classes = re.findall(r"^CLASS: mode=\d+ mul=(\d+) div=(\d+) load_use=(\d+) raw_nofwd=(\d+) control=(\d+) other=(\d+) classified=(\d+)", all_log, re.M)
    require(len(runs) == len(bht) == len(passes) == len(classes) == 8, "Expected bench and CoreMark four-profile matrices")
    obs = re.findall(r"obs iter=(\d+) seedcrc=0x(\w+) crclist=0x(\w+) crcmatrix=0x(\w+) crcstate=0x(\w+) crcfinal=0x(\w+) t0=(\d+) t1=(\d+) errors=(\d+)", all_log)
    require(len(obs) == 4, "Expected four CoreMark observation blocks")
    result = {"benchmark": {}, "coremark": {}, "arch_tests": 0, "ooc": {}}
    for i, (run, bp, cls) in enumerate(zip(runs, bht, classes)):
        profile = PROFILES[i % 4]
        mode, image, exit_code, tohost, cycles, retired, bubbles = run
        cycles, retired, bubbles = map(int, (cycles, retired, bubbles))
        bp_mode, lookup, hit, miss = map(int, bp)
        cls = list(map(int, cls))
        require(int(mode) == (0 if profile == "nofwd" else 1), "Wrong forwarding profile")
        require(bp_mode == (0, 0, 1, 2)[i % 4] and hit + miss == lookup, "BHT accounting mismatch")
        require(cycles == retired + bubbles and sum(cls[:6]) == cls[6] == bubbles, "Cycle accounting mismatch")
        require(exit_code == "0" and tohost == ("327535569" if i < 4 else "34713"), "Wrong firmware result")
        group = "benchmark" if i < 4 else "coremark"
        require(image.endswith("bench_v0_1.hex" if i < 4 else "coremark.hex"), "Wrong image")
        row = dict(cycles=cycles, retired=retired, bubbles=bubbles, cpi=cycles / retired,
                   lookup=lookup, hit=hit, miss=miss, hit_percent=(100 * hit / lookup if lookup else None),
                   control=cls[4], log="all-final.log")
        if i >= 4:
            block = obs[i - 4]
            require(block[:6] == ("32", "e9f5", "e714", "1fd7", "8e3a", "8799"), "CRC golden mismatch")
            ticks = int(block[7]) - int(block[6])
            require(ticks > 0, "Invalid CoreMark timer window")
            row.update(ticks=ticks, coremark_per_mhz=32_000_000 / ticks, errors_raw=int(block[8]))
            xsim = read(folder / "xsim-pass" / f"module1_{profile}.log")
            require(passes[i] in xsim and "BHT: mode=%s lookup=%s hit=%s miss=%s" % bp in xsim,
                    "XSim counters differ from final Icarus run")
            require("FAIL:" not in xsim and "FATAL:" not in xsim, "XSim failed")
        result[group][profile] = row
    for group in ("benchmark", "coremark"):
        rows = result[group]
        require(len({r["retired"] for r in rows.values()}) == 1, "Retired differs across profiles")
        for profile, row in rows.items():
            row["gain_vs_nofwd_percent"] = 100 * (1 - row["cycles"] / rows["nofwd"]["cycles"])
            row["gain_vs_fwd_percent"] = 100 * (1 - row["cycles"] / rows["fwd"]["cycles"])
    require(result["coremark"]["fwd"]["gain_vs_nofwd_percent"] >= 8, "Forwarding performance gate failed")
    matrix = read(ROOT / "sim/scripts/run_arch_test_matrix.sh")
    entries = re.findall(r"([IM]):([\w-]+)", re.search(r"tests=\((.*?)\)", matrix, re.S)[1])
    require(f"PASS: arch-test matrix {len(entries)} tests x 4 modes" in read(folder / "arch-complete.log"), "Arch matrix incomplete")
    for _, name in entries:
        signatures = []
        for profile in PROFILES:
            log = read(folder / "arch-complete" / f"{name}.{profile}.log")
            require(f"PASS: {name}-{profile} signature" in log and "FAIL:" not in log, f"Arch golden failed: {name}/{profile}")
            signatures.append(hashlib.sha256((folder / "arch-complete" / f"{name}.{profile}.signature.output").read_bytes()).hexdigest())
        require(len(set(signatures)) == 1, f"Arch signature mismatch: {name}")
    result["arch_tests"] = len(entries) * 4
    audit = read(folder / "ooc-complete.log")
    require("PASS: five OOC checkpoints hold/DRC audit" in audit, "OOC audit incomplete")
    for label, setup, hold in re.findall(r"AUDIT: (\S+) setup=([\d.-]+) hold=([\d.-]+) critical_drc=0", audit):
        checks = re.findall(r"checking\s+\w+\s+\((\d+)\)", read(folder / "ooc-complete" / label / "check_timing.rpt"))
        require(checks and all(int(count) == 0 for count in checks), f"Internal timing checks failed: {label}")
        result["ooc"][label] = dict(setup_ns=float(setup), hold_ns=float(hold), critical_drc=0)
    require(len(result["ooc"]) == 5, "Missing OOC profiles")
    fixed = re.findall(r"FIXED_ROUTE: (\S+) setup=([\d.-]+) hold=([\d.-]+) period=11.520", audit)
    require(len(fixed) == 2 and all(float(s) >= 0 and float(h) >= 0 for _, s, h in fixed), "Default/BHT1 timing gate failed")
    result["fixed_route"] = {name: dict(setup_ns=float(s), hold_ns=float(h), period_ns=11.520) for name, s, h in fixed}
    return result


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "data/logs/2026-10-07-module1-closure"
    try:
        summary = summarize(folder)
        (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: {summary['arch_tests']} arch signatures; eight workload runs; four XSim matches; five OOC audits; two fixed-route gates")
    except (ValueError, OSError) as error:
        sys.exit(f"FAIL: {error}")
