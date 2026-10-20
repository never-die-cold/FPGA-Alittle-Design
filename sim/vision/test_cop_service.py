"""LIVE service + EXE state machine on the simulated coprocessor (C03 §13).

Exercises: one full manual round, artifact/trace chain, duplicate trigger_ref,
stale-result failure (503, no packet, EXE drops the old PASS), same-ref retry,
and one record only after the retried round is adopted.
"""
import hashlib
import json
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
import rounds
from cop_engine import CopEngine
from records import BatchRecords
from round_artifacts import SnapshotError, load_snapshot
from rounds import RemoteRounds, WAITING
from vision_live_service import FileCaptures, make_server
from vision_protocol import validate_packet

FIXTURE = root / "data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png"
ORDER = {"bolt": 1, "nut": 1, "washer": 1}
OUT = root / "sim/build/vision/cop-service-test"


def post(base, ref):
    request = urllib.request.Request(
        base + "/v1/check", json.dumps({"trigger_ref": ref}).encode(),
        {"Content-Type": "application/json"})
    return validate_packet(json.loads(urllib.request.urlopen(request, timeout=20).read()))


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    captures = OUT / "captures"
    captures.mkdir(parents=True)
    (captures / "scene.png").write_bytes(FIXTURE.read_bytes())
    engine = CopEngine(ORDER, 0.8, 16, classes=("bolt", "nut", "washer"))
    server = make_server(port=0, root=OUT / "service", captures=FileCaptures(captures),
                         engine=engine, order=dict(ORDER))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        remote = RemoteRounds(base, max_age=1.0)
        status = remote.handshake()
        assert status["mode"] == "LIVE" and status["engine"] == "COP_SIM"
        assert status["prototype"] is True and status["hardware_connected"] is True

        # 1) One full manual round: PASS, artifacts, traceable decision.
        now = time.time()
        assert remote.trigger(now)
        remote.poll(now, 0.5)
        packet = remote.packet
        assert packet["status"] == "CHECK_PASS" and remote.last_round_manual
        assert [t["class"] for t in packet["targets"]] == ["bolt", "nut", "washer"]
        assert remote.overlay(time.time())[0]
        snap = load_snapshot(OUT / "service", packet["session_id"], packet["check_id"])
        assert snap["sha256"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        assert snap["cop_trace"]["kind"] == "cop_job"
        assert snap["cop_trace"]["decision"] == packet["decision"]
        round_dir = OUT / "service" / packet["session_id"][:8] / f"check-{packet['check_id']:06d}"
        trace = json.loads((round_dir / "cop_trace.json").read_text(encoding="utf-8"))
        assert trace["kind"] == "cop_job" and trace["simulated"] is True
        assert trace["driver"]["fw"]["verdict"] == "CHECK_PASS"
        assert trace["decision"] == packet["decision"]
        assert (round_dir / "capture.sha256").read_text().strip() == snap["sha256"]
        # Tampered ROI bytes must break the snapshot chain.
        roi_path = round_dir / trace["rois"][0]["path"]
        original = roi_path.read_bytes()
        roi_path.write_bytes(b"\x00" * 4096)
        try:
            load_snapshot(OUT / "service", packet["session_id"], packet["check_id"])
            raise AssertionError("tampered cop ROI accepted")
        except SnapshotError:
            pass
        roi_path.write_bytes(original)
        assert load_snapshot(OUT / "service", packet["session_id"],
                             packet["check_id"])["cop_trace"] is not None
        assert not list((OUT / "service").rglob("*.pending"))

        # 2) Duplicate trigger_ref: same round, no second capture/check_id.
        first = post(base, "dup-ref")
        second = post(base, "dup-ref")
        assert first["check_id"] == second["check_id"]
        assert first["frame_id"] == second["frame_id"]
        assert first["created_at"] == second["created_at"]
        assert len(list((OUT / "service" / first["session_id"][:8]).glob(
            f"check-{first['check_id']:06d}"))) == 1

        # 3) Stale result: 503, no packet.json, EXE must not keep showing old PASS.
        old = remote.packet
        engine.sim.faults.stale_result = True
        bodies = []
        real_http = rounds.http_json
        def spy(url, body=None):
            if url.endswith("/v1/check"):
                bodies.append(body)
            return real_http(url, body)
        with patch.object(rounds, "http_json", side_effect=spy):
            now += 0.6
            assert remote.trigger(now)
            remote.poll(now, 0.5)
            assert remote.fails == 1 and remote.packet is old
            assert remote.manual_failed is True
            assert remote.overlay(time.time()) == (False, WAITING)
            failed_id = first["check_id"] + 1  # the duplicate posts consumed check_id 2
            failed_dir = OUT / "service" / old["session_id"][:8] / f"check-{failed_id:06d}"
            assert (failed_dir / "capture.png").is_file()
            assert not (failed_dir / "packet.json").exists()
            failure = json.loads((failed_dir / "cop_trace.json").read_text(encoding="utf-8"))
            assert failure["kind"] == "cop_failure" and "RESULT_SEQ" in failure["error"]
            assert bodies and "trigger_ref" in bodies[0]
            failed_ref = bodies[0]["trigger_ref"]

            # 4) Same-ref retry after clearing the fault becomes one adopted round.
            engine.sim.faults.stale_result = False
            now += 0.6
            remote.poll(now, 0.5)
            assert bodies[-1]["trigger_ref"] == failed_ref, "retry must reuse trigger_ref"
            assert remote.fails == 0 and not remote.manual_failed
            assert remote.last_round_manual and remote.overlay(time.time())[0]
            assert remote.packet["check_id"] == failed_id + 1
            assert remote.packet["status"] == "CHECK_PASS"

        # 5) Records: only the adopted retry is recorded; duplicate key is rejected.
        rec = BatchRecords(OUT / "records",
                           save_image=lambda path, frame: (path.write_bytes(b"shot") or True))
        assert rec.accept(remote.packet) and rec.write(remote.packet, None, 0.1)
        assert rec.accept(remote.packet) is False and rec.write(remote.packet, None, 0.1) is None
        assert rec.count == 1
        row = json.loads((OUT / "records" / "records.jsonl").read_text(encoding="utf-8"))
        assert row["status"] == "CHECK_PASS" and row["prototype"] is True
        assert row["decision"] == remote.packet["decision"]
        kinds = {event["kind"] for event in remote.drain_events()}
        assert "overlay_error" in kinds and "overlay_ok" in kinds, kinds
        print("PASS: cop service x EXE (round/trace/duplicate-ref/stale-failure/same-ref retry/record)")
    finally:
        server.shutdown()
        server.server_close()
        engine.close()


if __name__ == "__main__":
    main()
