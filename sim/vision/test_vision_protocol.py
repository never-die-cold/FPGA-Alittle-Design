import copy
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from vision_protocol import mock_packet, validate_packet, is_current, MAX_TRIGGER_REF_LEN
from vision_mock_service import make_server


def post_json(base, path, body):
    request = urllib.request.Request(base + path, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=2) as response:
        return json.load(response)


def test_result_fields(packet):
    for valid in (packet, {**packet, "trigger_ref": "ref-1"},
                  {**packet, "targets": []}):
        assert validate_packet(valid) is valid
    cases = [("packet", {**packet, name: value}) for name, value in
             (("extra", 1), ("class", "bolt"), ("verdict", "CHECK_PASS"))]
    for name, value in (("extra", 1), ("class", "bolt"), ("verdict", "CHECK_PASS")):
        bad = copy.deepcopy(packet)
        bad["targets"][0][name] = value
        cases.append(("target", bad))
    cases.extend(("packet", value) for value in (None, [], "invalid"))
    for value in (None, [], "invalid"):
        cases.append(("target", {**packet, "targets": [value]}))
    for scope, bad in cases:
        try:
            validate_packet(bad)
        except ValueError as error:
            assert str(error) == f"invalid {scope} fields", str(error)
        else:
            raise AssertionError(f"invalid {scope} fields accepted")
    print("PASS: Q01 result fields: 3 valid / 12 invalid packets")


def main():
    packet = mock_packet("session-a", 10, 2, 7)
    test_result_fields(packet)
    # D3 判据：session + config_id + 年龄；frame_id 不参与（仅换帧号仍判当前）
    assert is_current(packet, "session-a", 2)
    assert is_current({**packet, "frame_id": 999}, "session-a", 2)
    assert not is_current(packet, "session-b", 2)
    assert not is_current(packet, "session-a", 1)
    for age in (-5, 5):
        stale = {**packet, "created_at": time.time()-age}
        assert not is_current(stale, "session-a", 2)
    for field, value in (("mode", "HARDWARE"), ("frame_id", True), ("created_at", float("nan")),
                         ("check_id", None), ("check_id", True)):
        bad = {**packet, field: value}
        try:
            validate_packet(bad)
            raise AssertionError("bad packet accepted")
        except ValueError:
            pass
    missing = {k: v for k, v in packet.items() if k != "check_id"}
    try:
        validate_packet(missing)
        raise AssertionError("packet without check_id accepted")
    except ValueError:
        pass
    echoed = mock_packet("s", 1, 0, 1, "ref-1")
    assert echoed["trigger_ref"] == "ref-1"
    for ref in (123, "", "x" * (MAX_TRIGGER_REF_LEN + 1)):
        try:
            validate_packet({**packet, "trigger_ref": ref})
            raise AssertionError("invalid trigger_ref accepted")
        except ValueError:
            pass
    bad = copy.deepcopy(packet)
    bad["targets"][0]["bbox"][2] = 2000
    try:
        validate_packet(bad)
        raise AssertionError("out-of-frame box accepted")
    except ValueError:
        pass
    # 半开区间端点语义（对齐定位外包需求 L2）：右下端点可恰为 w/h；退化、反向、越界拒绝
    edge = copy.deepcopy(packet)
    edge["targets"] = [{"target_id": 0, "bbox": [1279, 719, 1280, 720]}]
    validate_packet(edge)
    for box in ([200, 170, 200, 289], [300, 170, 200, 289], [0, 0, 1280, 721]):
        invalid = copy.deepcopy(packet)
        invalid["targets"][0]["bbox"] = box
        try:
            validate_packet(invalid)
            raise AssertionError("degenerate/reversed/out-of-frame box accepted")
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
        check = validate_packet(post_json(base, "/v1/check", b'{"trigger_ref":"t-1"}'))
        assert check["check_id"] == 1 and check["trigger_ref"] == "t-1" and check["config_id"] == 1
        plain = validate_packet(post_json(base, "/v1/check", b""))
        assert plain["check_id"] == 2 and "trigger_ref" not in plain
        for path, body, expected in (("/bad", None, 404), ("/v1/config", b'{"control":16}', 400),
                                     ("/v1/config", b'[]', 400), ("/v1/check", b'{"other":1}', 400)):
            try:
                urllib.request.urlopen(urllib.request.Request(base+path, body), timeout=2)
                raise AssertionError("invalid request accepted")
            except urllib.error.HTTPError as error:
                assert error.code == expected
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    print("PASS: M2 HTTP mock check/config/status/location + check/config/session/stale/error contract")


if __name__ == "__main__":
    main()
