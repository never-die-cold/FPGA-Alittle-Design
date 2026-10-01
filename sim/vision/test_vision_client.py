"""Exercise the packaged Windows EXE against the local M2 HTTP service."""
import subprocess
import sys
import threading
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/pynq_host"))
from vision_mock_service import make_server

server = make_server(port=0)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
exe = root / "sim/build/vision-client/dist/vision_preview/vision_preview.exe"
image = root / "sim/build/vision-client/http-preview.png"
try:
    result = subprocess.run([str(exe), "--mock", "--headless", "--frames", "3",
        "--endpoint", f"http://127.0.0.1:{server.server_port}", "--save", str(image)],
        capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    failure = subprocess.run([str(exe), "--mock", "--headless", "--frames", "1",
        "--endpoint", f"http://127.0.0.1:{server.server_port}/missing"],
        capture_output=True, text=True, timeout=20)
    assert failure.returncode != 0, "invalid endpoint was silently accepted"
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
print("PASS: packaged EXE HTTP mock preview + unreachable route rejects, no UVC/board access")
