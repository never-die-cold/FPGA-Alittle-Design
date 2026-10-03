import copy
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from vision_protocol import mock_packet, validate_packet, is_current
from vision_mock_service import make_server


def main():
    packet = mock_packet("session-a", 10, 2)
    assert is_current(packet, "session-a", 10, 2)
    assert not is_current(packet, "session-b", 10, 2)
    assert not is_current(packet, "session-a", 9, 2)
    assert not is_current(packet, "session-a", 10, 1)
    for age in (-5, 5):
        stale = {**packet, "created_at": time.time()-age}
        assert not is_current(stale, "session-a", 10, 2)
    for field, value in (("mode", "HARDWARE"), ("frame_id", True), ("created_at", float("nan"))):
        bad = {**packet, field: value}
        try:
            validate_packet(bad)
            raise AssertionError("bad packet accepted")
        except ValueError:
            pass
    bad = copy.deepcopy(packet)
    bad["targets"][0]["bbox"][2] = 2000
    try:
        validate_packet(bad)
        raise AssertionError("out-of-frame box accepted")
    except ValueError:
        pass
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        def get(path):
            with urllib.request.urlopen(base+path, timeout=2) as response:
                return json.load(response)
        assert get("/v1/status")["hardware_connected"] is False
        first = validate_packet(get("/v1/latest"))
        request = urllib.request.Request(base+"/v1/config", b'{"control":3}', {"Content-Type":"application/json"})
        with urllib.request.urlopen(request, timeout=2) as response:
            assert json.load(response)["applied_config_id"] == 1
        second = validate_packet(get("/v1/latest"))
        assert second["config_id"] == 1 and second["frame_id"] == first["frame_id"]+1
        for path, body, expected in (("/bad", None, 404), ("/v1/config", b'{"control":16}', 400), ("/v1/config", b'[]', 400)):
            try:
                urllib.request.urlopen(urllib.request.Request(base+path, body), timeout=2)
                raise AssertionError("invalid request accepted")
            except urllib.error.HTTPError as error:
                assert error.code == expected
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    print("PASS: M2 HTTP mock config/status/location + frame/config/session/stale/error contract")


if __name__ == "__main__":
    main()
