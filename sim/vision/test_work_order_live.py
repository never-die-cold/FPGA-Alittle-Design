"""HTTP work order -> engine/driver/firmware rules, with no implicit startup order."""
import json
from pathlib import Path
import sys
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/pynq_host"))
from cop_engine import CopEngine
from vision_live_service import FileCaptures, make_server

out = ROOT / "sim/build/vision" / ("work-order-" + uuid.uuid4().hex)
frames = out / "frames"
frames.mkdir(parents=True)
fixture = ROOT / "data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png"
(frames / "one.png").write_bytes(fixture.read_bytes())
captures = FileCaptures(frames)
engine = CopEngine(None, .8, classes=("bolt", "nut", "washer"))
applied, fail = [7], [False]


def configure(control):
    assert control == 0
    if fail[0]:
        raise RuntimeError("configuration ACK timed out")
    applied[0] += 1
    return applied[0]


captures.configure = configure
server = make_server(port=0, root=out, captures=captures, engine=engine,
                     order=None, initial_config_id=7)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"


def request(path, data=None, code=200):
    req = Request(base + path, data=None if data is None else json.dumps(data).encode())
    try:
        response = urlopen(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == code, response.read()
        return json.load(response)


try:
    assert request("/v1/status")["work_order"] is None
    request("/v1/check", {}, 400)
    assert captures.seq == 0 and engine.driver.order is None
    for bad in [None, {}, {"bolt":True,"nut":0,"washer":0},
                {"bolt":0,"nut":0,"washer":0}, {"bolt":11,"nut":0,"washer":0}]:
        request("/v1/config", {"control":0,"order":bad}, 400)
        assert request("/v1/status")["config_id"] == 7
    first = {"bolt":1,"nut":1,"washer":1}
    ack = request("/v1/config", {"control":0,"order":first})
    assert ack["work_order"] == first and ack["applied_config_id"] == 8
    p = request("/v1/check", {"trigger_ref":"first"})
    assert p["decision"]["expected"] == first and p["config_id"] == 8
    second = {"bolt":2,"nut":1,"washer":0}
    request("/v1/config", {"control":0,"order":second})
    request("/v1/latest", code=404)
    p = request("/v1/check", {})
    assert p["decision"]["expected"] == second and p["config_id"] == 9
    assert engine.order == engine.driver.order == request("/v1/status")["work_order"] == second
    fail[0] = True
    request("/v1/config", {"control":0,"order":first}, 503)
    assert request("/v1/status")["config_id"] == 9 and engine.order == second
    print("PASS: no implicit order; validate/ACK/apply; firmware and PS agree; failed ACK preserves order")
finally:
    server.shutdown()
    server.server_close()
    engine.close()
