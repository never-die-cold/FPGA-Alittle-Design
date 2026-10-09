"""Exercise the packaged Windows EXE against the local M2 HTTP service."""
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from vision_mock_service import make_server
import cv2  # 由构建脚本 PYTHONPATH（vision-client-deps）提供
import numpy as np

server = make_server(port=0)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
exe = root / "sim/build/vision-client/dist/vision_preview/vision_preview.exe"
image = root / "sim/build/vision-client/http-preview.png"
record_dir = root / "sim/build/vision-client/records-auto-check"
shutil.rmtree(record_dir, ignore_errors=True)
try:
    result = subprocess.run([str(exe), "--mock", "--headless", "--frames", "3",
        "--endpoint", f"http://127.0.0.1:{server.server_port}", "--save", str(image),
        "--records-dir", str(record_dir)],
        capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    # D8：自动间隔轮次永不落批次记录（"--frames 3" 无手动触发 → 无 records.jsonl）
    assert not (record_dir / "records.jsonl").exists(), "auto rounds must not create batch records"
    # 手动触发路径（--trigger-frame 模拟按 c）：恰好一条批次记录 + 异常事件日志存在
    manual_dir = root / "sim/build/vision-client/records-manual-check"
    shutil.rmtree(manual_dir, ignore_errors=True)
    manual = subprocess.run([str(exe), "--mock", "--headless", "--frames", "6",
        "--endpoint", f"http://127.0.0.1:{server.server_port}", "--save", str(image),
        "--records-dir", str(manual_dir), "--trigger-frame", "2"],
        capture_output=True, text=True, timeout=20)
    if manual.returncode != 0:
        raise AssertionError(manual.stdout + manual.stderr)
    rows = (manual_dir / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1, "manual trigger must record exactly one batch"
    row = json.loads(rows[0])
    assert row["mode"] == "MOCK" and row["screenshot"].startswith("screenshots/mock_")
    assert (manual_dir / row["screenshot"]).exists()
    assert (manual_dir / "anomalies.jsonl").exists(), "state events must be journalled"
    # 内容断言：叠加生效时画面必须有绿色目标框像素。2026-10-08 曾出现 /v1/check 误发 GET
    # （404）导致端点模式叠框全部失效、"跑通即通过"的旧断言未能发现，故补此检查。
    # v3 绿为 (130,230,0)，判据改用 int16 差值（防 uint8 运算溢出误判背景）。
    frame = cv2.imread(str(image))
    assert frame is not None, "saved frame unreadable"
    f = frame.astype(np.int16)
    green = int(((f[:, :, 1] > 150) & (f[:, :, 1] - f[:, :, 0] > 60)
                 & (f[:, :, 1] - f[:, :, 2] > 60)).sum())
    assert green > 500, f"round overlay targets missing from packaged preview frame (green={green})"
    failure = subprocess.run([str(exe), "--mock", "--headless", "--frames", "1",
        "--endpoint", f"http://127.0.0.1:{server.server_port}/missing"],
        capture_output=True, text=True, timeout=20)
    assert failure.returncode != 0, "invalid endpoint was silently accepted"
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
print("PASS: packaged EXE HTTP mock preview + unreachable route rejects, no UVC/board access")
