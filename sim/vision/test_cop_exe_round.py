"""One full service + EXE round on the simulated coprocessor (software pass).

Starts the real LIVE service with CopEngine, runs the real EXE headless against
it with a static fixture, and verifies display/save/traceability end to end.
The compute backend is simulated; this is 模拟跑通, not board recognition.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
sys.path.insert(0, str(root / "src/vision_client"))
from cop_engine import CopEngine
from round_artifacts import load_snapshot
from vision_live_service import FileCaptures, make_server

FIXTURE = root / "data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png"
ORDER = {"bolt": 1, "nut": 1, "washer": 1}
DEFAULT_OUT = root / "sim/build/vision/cop-exe-round"


def green_pixels(image):
    bands = image.astype("int16")
    return int(((bands[:, :, 1] > 150) & (bands[:, :, 1] - bands[:, :, 0] > 60)
                & (bands[:, :, 1] - bands[:, :, 2] > 60)).sum())


def run(out):
    out = Path(out).resolve()
    if root not in out.parents:
        raise ValueError("round output must stay inside the repository")
    shutil.rmtree(out, ignore_errors=True)
    captures = out / "captures"
    captures.mkdir(parents=True)
    (captures / "scene.png").write_bytes(FIXTURE.read_bytes())
    engine = CopEngine(ORDER, 0.8, 16, classes=("bolt", "nut", "washer"))
    server = make_server(port=0, root=out / "service", captures=FileCaptures(captures),
                         engine=engine, order=dict(ORDER))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        command = [sys.executable, str(root / "src/vision_client/preview.py"),
                   "--image", str(FIXTURE), "--endpoint", base, "--headless",
                   "--frames", "45", "--trigger-frame", "1",
                   "--records-dir", str(out / "records"),
                   "--save", str(out / "screen.png"),
                   "--interval", "0.1", "--max-age", "2.0"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
        (out / "exe.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise AssertionError(f"EXE exited {completed.returncode}:\n{completed.stdout}\n"
                                 f"{completed.stderr}")
        assert "session " in completed.stdout and "LIVE" in completed.stdout
        records = [json.loads(line) for line in
                   (out / "records" / "records.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(records) == 1, records
        row = records[0]
        assert row["status"] == "CHECK_PASS" and row["prototype"] is True
        assert row["target_count"] == 3 and row["decision"]["actual"] == dict(ORDER)
        shot = out / "records" / row["screenshot"]
        assert shot.is_file() and row["screenshot"].startswith("screenshots/proto_")
        snap = load_snapshot(out / "service", row["session_id"], row["check_id"])
        trace = snap["cop_trace"]
        assert trace and trace["kind"] == "cop_job"
        assert trace["driver"]["fw"]["verdict"] == "CHECK_PASS"
        assert trace["decision"] == row["decision"]
        assert len(trace["rois"]) == row["target_count"]
        round_dir = out / "service" / row["session_id"][:8] / f"check-{row['check_id']:06d}"
        assert (round_dir / "capture.png").read_bytes() == FIXTURE.read_bytes()
        assert (round_dir / "packet.json").is_file()
        image = cv2.imread(str(out / "screen.png"))
        assert image is not None and image.shape == (900, 1600, 3)
        assert green_pixels(image) > 500, "no green target boxes in saved display"
        assert not list(out.rglob("*.pending"))
        summary = {
            "outcome": "模拟跑通 (COP_SIM service + EXE)",
            "session_id": row["session_id"], "check_id": row["check_id"],
            "status": row["status"], "decision": row["decision"],
            "prototype": True, "record": "records/records.jsonl",
            "screenshot": "screen.png", "record_screenshot": row["screenshot"],
            "capture_sha256": snap["sha256"],
            "trace": "service/" + row["session_id"][:8]
                     + f"/check-{row['check_id']:06d}/cop_trace.json",
            "roi_count": len(trace["rois"]),
            "screen_sha256": hashlib.sha256((out / "screen.png").read_bytes()).hexdigest(),
            "boundary": "simulated compute/register model; not board recognition",
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)
                                          + "\n", encoding="utf-8")
        print(f"PASS: one cop-sim service+EXE round -> {out / 'summary.json'}")
    finally:
        server.shutdown()
        server.server_close()
        engine.close()


def main():
    run(os.environ.get("COP_ROUND_DIR", DEFAULT_OUT))


if __name__ == "__main__":
    main()
