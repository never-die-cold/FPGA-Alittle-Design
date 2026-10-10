"""A checked file manifest renders in the HUD without camera or network."""
import json
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
import cv2
ROOT = Path(__file__).resolve().parents[2]
for name in ("src/pynq_host", "src/vision_client"):
    sys.path.insert(0, str(ROOT / name))
from inspection_artifacts import digest, save_bytes, save_png
from replay_viewer import render_manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path)
    args = parser.parse_args()
    build = ROOT / "sim/build/inspection"
    build.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as directory:
        folder = Path(directory)
        frame = np.full((720, 1280, 3), 220, np.uint8)
        artifacts = [save_bytes(folder, "source.bin", b"source")]
        artifacts += [save_png(folder, name, frame) for name in ("frame.png", "annotated.png")]
        result = {"mode": "FILE_REPLAY", "request_fingerprint": "same", "artifacts": artifacts,
                  "width": 1280, "height": 720, "request_id": "viewer-test", "targets": [],
                  "decision": {"actual": {"bolt": 1, "nut": 0, "washer": 0},
                               "expected": {"bolt": 1, "nut": 0, "washer": 0}, "verdict": "CHECK_PASS"}}
        for actual in (result["decision"]["actual"], None):
            result["decision"]["actual"] = actual
            raw = json.dumps(result).encode()
            (folder / "result.json").write_bytes(raw)
            (folder / "result.sha256").write_text(digest(raw), encoding="ascii")
            canvas = render_manifest(folder / "result.json")
            assert canvas.shape == (900, 1600, 3) and canvas.dtype == np.uint8
            assert tuple(canvas[32, 1120]) == (32, 176, 255), "replay must show amber offline status"
        if args.exe:
            command = [str(args.exe.resolve()), "--replay", str(folder / "result.json"), "--headless"]
            rendered = subprocess.run(command + ["--save", str(folder / "viewer.png")],
                                      capture_output=True, text=True, timeout=20)
            assert rendered.returncode == 0, rendered.stdout + rendered.stderr
            packaged = cv2.imread(str(folder / "viewer.png"))
            assert packaged.shape == (900, 1600, 3) and tuple(packaged[32, 1120]) == (32, 176, 255)
            rejected = subprocess.run(command + ["--mock"], capture_output=True, text=True, timeout=20)
            assert rejected.returncode == 2, "packaged replay must reject mixed mock mode"
            print("PASS: packaged FILE REPLAY rendering and conflicting mode rejection")
        (folder / "source.bin").write_bytes(b"tampered")
        try:
            render_manifest(folder / "result.json")
        except ValueError:
            pass
        else:
            raise AssertionError("viewer accepted modified evidence")
    print("PASS: checked FILE REPLAY HUD; normal/unknown counts and altered evidence rejection")


if __name__ == "__main__":
    main()
