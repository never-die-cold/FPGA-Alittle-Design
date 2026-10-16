"""打包 EXE × LIVE 检查服务联合离板回归（W08-2）——打包门禁。

由 build_vision_client.ps1 调用（依赖其 PYTHONPATH=vision-client-deps）。
场景：EXE --mock 取像 + W05 检查服务（FILE 后端 + 桩引擎）轮次叠加，
--trigger-frame 手动触发落一条批次记录；核对叠框渲染、记录字段、服务侧
(capture.png, packet.json) 产物齐全与原子落盘，退出码非零即失败。
"""
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from vision_live_service import FileCaptures, make_server

import cv2
import numpy as np

EXE = root / "sim/build/vision-client/dist/vision_preview/vision_preview.exe"
OUT = root / "sim/build/vision-client/service-e2e"


def engine(capture_path, round_dir, request_id):
    (round_dir / "engine.json").write_text(json.dumps({"request_id": request_id}),
                                          encoding="utf-8")
    return {"status": "CHECK_FAIL",
            "targets": [{"target_id": 0, "bbox": [180, 170, 339, 289],
                         "class": "bolt", "score": 0.97},
                        {"target_id": 1, "bbox": [730, 380, 929, 520],
                         "class": "nut", "score": 0.91},
                        {"target_id": 2, "bbox": [300, 460, 470, 620],
                         "class": "washer", "score": 0.95}],
            "decision": {"verdict": "CHECK_FAIL",
                         "expected": {"bolt": 2, "nut": 2, "washer": 2},
                         "actual": {"bolt": 1, "nut": 1, "washer": 1},
                         "delta": {"bolt": -1, "nut": -1, "washer": -1},
                         "missing": {"bolt": 1, "nut": 1, "washer": 1},
                         "extra": {"bolt": 0, "nut": 0, "washer": 0}, "reasons": []},
            "width": 1280, "height": 720}


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    captures = OUT / "captures"
    captures.mkdir(parents=True)
    (captures / "cap-a.png").write_bytes(b"\x89PNG-fake-a")
    (captures / "cap-b.png").write_bytes(b"\x89PNG-fake-b")
    server = make_server(port=0, root=OUT / "service", captures=FileCaptures(captures),
                         engine=engine, order={"bolt": 2, "nut": 2, "washer": 2})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        records = OUT / "records"
        image = OUT / "preview.png"
        result = subprocess.run([str(EXE), "--mock", "--headless", "--frames", "150",
            "--endpoint", f"http://127.0.0.1:{server.server_port}", "--save", str(image),
            "--records-dir", str(records), "--trigger-frame", "3"],
            capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
        assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        frame = cv2.imread(str(image))
        assert frame is not None, "saved frame unreadable"
        view = frame[88:799, 24:1288].astype(np.int16)
        green = int(((view[:, :, 1] > 150) & (view[:, :, 1] - view[:, :, 0] > 60)
                     & (view[:, :, 1] - view[:, :, 2] > 60)).sum())
        assert green > 500, f"service overlay boxes missing from packaged frame (green={green})"
        rows = [json.loads(line) for line in
                (records / "records.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1, "manual trigger must record exactly one round"
        row = rows[0]
        assert row["mode"] == "LIVE" and row["prototype"] is True
        assert row["status"] == "CHECK_FAIL" and row["decision"]["missing"]["washer"] == 1
        assert row["screenshot"].startswith("screenshots/proto_")
        rounds = sorted((OUT / "service").glob("*/check-*"))
        assert len(rounds) >= 6, f"too few service rounds: {len(rounds)}"
        assert all((r / "capture.png").exists() and (r / "packet.json").exists()
                   for r in rounds), "service artifacts incomplete"
        assert not list(OUT.rglob("*.pending")), "atomic writes must not leave .pending files"
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: packaged EXE x live service joint e2e (overlay render, proto_ record, artifacts)")


if __name__ == "__main__":
    main()
