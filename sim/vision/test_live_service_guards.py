"""Offline read-only config/health, disk reserve and write failure checks."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import threading
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen, Request
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from vision_live_service import FileCaptures, State, make_server

out = ROOT / "sim/build/vision" / ("guards-" + uuid.uuid4().hex)
frames = out / "frames"
frames.mkdir(parents=True)
(frames / "one.png").write_bytes(b"fake-png")
captures = FileCaptures(frames)
state = State(out, captures, lambda *a: None, {}, initial_config_id=7)
with patch("vision_live_service.shutil.disk_usage", return_value=SimpleNamespace(free=0)):
    try:
        state.check(None)
        raise AssertionError("low disk was accepted")
    except RuntimeError as error:
        assert "storage reserve" in str(error)
assert state.check_id == 0 and captures.seq == 0
assert not (state.session_dir / "check-000001").exists()

health = [True]
captures.health = lambda: health[0]
server = make_server(port=0, root=out, captures=captures,
                     engine=lambda *a: None, order={}, initial_config_id=7)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"


def status():
    with urlopen(base + "/v1/status", timeout=2) as response:
        return json.load(response)


try:
    for _ in range(2):
        assert status()["config_id"] == 7
    health[0] = False
    assert status()["hardware_connected"] is False
    health[0] = True
    assert status()["hardware_connected"] is True
    with patch.object(captures, "health", side_effect=OSError("MMIO unavailable")):
        assert status()["hardware_connected"] is False
    with patch.object(captures, "capture", side_effect=OSError("disk full")):
        try:
            urlopen(Request(base + "/v1/check", data=b"{}"), timeout=2)
            raise AssertionError("write failure accepted")
        except HTTPError as error:
            assert error.code == 503 and "disk full" in json.load(error)["error"]
    try:
        urlopen(base + "/v1/latest", timeout=2)
        raise AssertionError("failed round published")
    except HTTPError as error:
        assert error.code == 404
finally:
    server.shutdown()
    server.server_close()
print("PASS: read-only configuration/health; low disk refuses before capture; OSError -> 503")
