"""Reproduce tutorial codec findings without editing its source or goldens."""
import contextlib
import io
from pathlib import Path
import runpy

path = Path(__file__).resolve().parents[3] / "sim/tools/verify_rv32i.py"
with contextlib.redirect_stdout(io.StringIO()):
    module = runpy.run_path(str(path))
actual = module["decode"](0x800000EF)
assert actual == "jal x1, 1048576", actual
print("REPRODUCED: 0x800000ef decoded as", actual,
      "; signed J immediate must be -1048576")
text = path.read_text(encoding="utf-8").replace('"007302b3"', '"00000000"', 1)
scope, captured = {}, io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(text, str(path), "exec"), scope)
assert scope["ok"] is False and "HAS MISMATCH" in captured.getvalue()
print("REPRODUCED: injected wrong expected word prints HAS MISMATCH but returns normally")
