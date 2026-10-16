"""Teeth check: the idle-clear ordering test must fail on the board's 2026-10-12 order.

Rebuilds the pre-fix sequence (clear before nonzero geometry) in sim/build/vision/python/mutant
and runs the real suite against it; the recorded board failure must reappear.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / 'src/pynq_host/c01_capture.py'
TEST = ROOT / 'sim/vision/test_c01_capture.py'
MUTANT = ROOT / 'sim/build/vision/python/mutant'
ORDERED = "            self.dma.write(VSIZE, 720)\n            self.evidence['configured_idle']"
PRE_FIX = ("            self.dma.write(SR, ERRORS | IRQ | 0x2000)\n"
           "            self.evidence['cleared_idle']")


def run(test_path, env=None):
    return subprocess.run([sys.executable, str(test_path)], capture_output=True, text=True, env=env)


baseline = run(TEST)
assert baseline.returncode == 0, baseline.stdout + baseline.stderr

source = DRIVER.read_text(encoding='utf-8')
assert ORDERED in source and PRE_FIX in source, 'driver idle sequence changed; update this probe'
mutated = source.replace(ORDERED, "            self.evidence['configured_idle']", 1)
mutated = mutated.replace(
    PRE_FIX,
    "            self.dma.write(SR, ERRORS | IRQ | 0x2000)\n"
    "            self.dma.write(VSIZE, 720)  # board 2026-10-12 order: clear before geometry\n"
    "            self.evidence['cleared_idle']", 1)
assert mutated != source
shutil.rmtree(MUTANT, ignore_errors=True)
MUTANT.mkdir(parents=True)
(MUTANT / 'c01_capture.py').write_text(mutated, encoding='utf-8')
(MUTANT / 'sitecustomize.py').write_text(
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('c01_capture', " + repr(str(MUTANT / 'c01_capture.py')) + ")\n"
    "module = importlib.util.module_from_spec(spec)\n"
    "sys.modules['c01_capture'] = module\n"
    "spec.loader.exec_module(module)\n", encoding='utf-8')

result = run(TEST, dict(os.environ, PYTHONPATH=os.pathsep.join(
    filter(None, (str(MUTANT), os.environ.get('PYTHONPATH', ''))))))
output = result.stdout + result.stderr
assert result.returncode != 0, 'pre-fix ordering was not caught by the suite'
assert 'DMA configured idle reset/clear not clean' in output, 'board failure signature missing'
assert 'test_recorded_idle_faults_reach_clean_state_after_geometry' in output, 'new test did not fire'
print('PASS: pre-fix idle ordering reproduces the board 0x4810 failure; sticky-fault test has teeth')
