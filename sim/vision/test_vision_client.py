"""Exercise the packaged Windows EXE against the local M2 HTTP service."""
import shutil
import subprocess
import sys
import threading
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from vision_mock_service import make_server
import cv2  # 由构建脚本 PYTHONPATH（vision-client-deps）提供

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
    # 内容断言：叠加生效时画面必须有绿色目标框像素。2026-10-08 曾出现 /v1/check 误发 GET
    # （404）导致端点模式叠框全部失效、"跑通即通过"的旧断言未能发现，故补此检查。
    frame = cv2.imread(str(image))
    assert frame is not None, "saved frame unreadable"
    green = int(((frame[:, :, 1] > 120) & (frame[:, :, 0] < 90) & (frame[:, :, 2] < 90)).sum())
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
