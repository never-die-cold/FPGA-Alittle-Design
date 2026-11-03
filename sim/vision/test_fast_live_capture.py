"""Direct frame handoff preserves capture evidence and persist-before-consume."""
from pathlib import Path
import hashlib
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from vision_live_service import State

root = Path(__file__).resolve().parents[2] / "sim/build/vision" / ("direct-" + uuid.uuid4().hex)
frame = object()
class Captures:
    backend, prototype, seq = "TEST", True, 0
    def capture_round(self, output):
        path = output / "capture.png"
        path.write_bytes(b"lossless-capture-evidence")
        self.seq += 1
        return path, frame
    def capture(self, output):
        raise AssertionError("unnecessary legacy capture")
class Engine:
    def inspect_round(self, received, output, request):
        assert received is frame
        assert (output / "capture.sha256").read_text().strip() == hashlib.sha256((output / "capture.png").read_bytes()).hexdigest()
        self.output = output
        return {"width":1,"height":1,"targets":[],"status":"CHECK_FAIL",
                "decision":{"verdict":"CHECK_FAIL","expected":{"bolt":1,"nut":0,"washer":0},
                "actual":{"bolt":0,"nut":0,"washer":0},"delta":{"bolt":-1,"nut":0,"washer":0},
                "missing":{"bolt":1,"nut":0,"washer":0},"extra":{"bolt":0,"nut":0,"washer":0},"reasons":[]}}
    def __call__(self, *args):
        raise AssertionError("unnecessary PNG decode path")
    def consume(self):
        assert (self.output / "packet.json").is_file()
engine = Engine()
state = State(root,Captures(),engine,{"bolt":1,"nut":0,"washer":0})
assert state.check("direct-frame")["check_id"] == 1
print("PASS: direct frame avoids redundant PNG decode; PNG/hash/packet persist before consume")
