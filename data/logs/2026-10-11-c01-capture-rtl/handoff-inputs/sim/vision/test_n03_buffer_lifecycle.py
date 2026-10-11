"""Replay the board's recorded freebuffer body with a harmless munmap spy.

No hardware, native unmapping or deployed driver patch is performed.
"""
import ast
import ctypes
import textwrap
from pathlib import Path
from types import MethodType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
record = ROOT / "data/logs/2026-10-11-onboard-resume/n03-buffer-free-lifecycle.txt"
text = record.read_text(encoding="utf-8")
signature = "    def freebuffer(self):"
body = signature + text.split(signature, 1)[1].split("\n    @property", 1)[0]
unmaps, returned = [], []
namespace = {"ctypes": ctypes,
             "libc": SimpleNamespace(munmap=lambda pointer, size: unmaps.append(size))}
exec(compile(textwrap.dedent(body), str(record), "exec"), namespace)
release = namespace["freebuffer"]


def cached_frame():
    return SimpleNamespace(memory=object(), pointer=(1, object(), 4096),
        return_to=SimpleNamespace(return_pointer=returned.append), freed=False,
        virtual_address=4096, nbytes=256, bo=1)


frame = cached_frame()
release(frame)  # Explicit release used by N03.
assert len(returned) == 1 and not unmaps and frame.pointer == 0
release(frame)  # Same call made later by PynqBuffer.__del__.
assert unmaps == [256] and not hasattr(frame, "bo")
print("REPRODUCED: cached frame returned once; second release calls munmap")

unmaps.clear()
returned.clear()
frame = cached_frame()
tree = ast.parse((ROOT / "sim/scripts/n03_board_capture.py").read_text(encoding="utf-8"))
helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "release_frame")
exec(compile(ast.Module(body=[helper], type_ignores=[]), "production release_frame", "exec"), namespace)
guard = namespace["release_frame"]
frame.freebuffer = MethodType(release, frame)
guard(frame)
release(frame)  # Recorded destructor path after explicit guarded release.
guard(frame)  # Repeating the guarded release must also be harmless.
assert len(returned) == 1 and not unmaps
print("PASS: production guard prevents second unmap of a cached frame")
frame = cached_frame()
frame.pointer = 0
frame.return_to = None
frame.freebuffer = MethodType(release, frame)
guard(frame)
guard(frame)
assert unmaps == [256]
print("PASS: ordinary buffer still unmapped once")
print("LIMIT: spy replay proves the branch, not the cause of a native crash")
