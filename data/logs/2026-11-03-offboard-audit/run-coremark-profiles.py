"""Audit-only parallel BHT profiles, using the existing tb and runner goldens.

python data/logs/2026-11-03-offboard-audit/run-coremark-profiles.py --output data/logs/<new-run>
The output directory must be new and inside the repository. No RTL is changed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.relative_to(ROOT)
output.mkdir(parents=True, exist_ok=False)
build = ROOT / "sim/build/offboard-audit-coremark"
build.mkdir(parents=True, exist_ok=True)
runner = ROOT / "sim/scripts/run_iverilog.sh"
goldens = shlex.split(re.search(r"COREMARK_ARGS=\((.*?)\)",
    runner.read_text(encoding="utf-8"), re.S).group(1))
sources = [ROOT / "sim/riscv/tb_core_coremark.v", *sorted((ROOT/"src/riscv").glob("*.v"))]
anchors = [*sources, runner, ROOT/"src/riscv_fw/coremark.hex"]
(output/"inputs.json").write_text(json.dumps({
    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in anchors}, indent=2), encoding="utf-8")
tool_dir = Path("C:/msys64/ucrt64/bin")
env = dict(os.environ, PATH=str(tool_dir)+os.pathsep+os.environ["PATH"],
           PYTHONIOENCODING="utf-8")


def run(mode):
    binary = build / f"bht{mode}.vvp"
    compile_cmd = [str(tool_dir/"iverilog.exe"), "-g2012", "-Wall",
        "-Ptb_core_coremark.ENABLE_FORWARDING=1", f"-Ptb_core_coremark.BHT_MODE={mode}",
        "-s", "tb_core_coremark", "-o", str(binary), *map(str, sources)]
    run_cmd = [str(tool_dir/"vvp.exe"), str(binary), *goldens]
    with (output/f"bht{mode}.log").open("wb") as stream:
        stream.write((json.dumps(compile_cmd)+"\n"+json.dumps(run_cmd)+"\n").encode())
        stream.flush()
        result = subprocess.run(compile_cmd, cwd=ROOT/"sim", env=env,
                                stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            result = subprocess.run(run_cmd, cwd=ROOT/"sim", env=env,
                                    stdout=stream, stderr=subprocess.STDOUT)
    text = (output/f"bht{mode}.log").read_text(encoding="utf-8", errors="replace")
    passed = result.returncode == 0 and "PASS: coremark" in text
    return {"mode": mode, "exit": result.returncode, "pass": passed}


with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, (1, 2)))
(output/"results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results), flush=True)
sys.exit(0 if all(r["pass"] for r in results) else 1)
