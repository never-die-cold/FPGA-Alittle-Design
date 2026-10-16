"""Base overlay 捕获后端 × 服务 离板回归（W04/N06）——每轮新帧、失败 503、原型旗标结构性。

fake read（可注入无视频超时/坏几何）驱动 BaseOverlayCaptures 接入 vision_live_service；
板上 read 由板端脚本提供（n03_board_capture.py 的 readframe 样板）。落盘 sim/build/vision/base-backend/。
"""
import hashlib
import json
import shutil
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[2]
for dep in ("vision-client-deps",):
    path = root / "sim" / "build" / dep
    if path.is_dir():
        sys.path.append(str(path))
sys.path.insert(0, str(root / "src/pynq_host"))
import cv2
from base_captures import BaseOverlayCaptures
from vision_live_service import make_server
from vision_protocol import validate_packet


def frame_like(value):
    return np.full((720, 1280, 3), value, np.uint8)


def post(base, payload=None):
    data = json.dumps({} if payload is None else payload).encode()
    request = urllib.request.Request(base + "/v1/check", data,
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read(65537))


def get(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return json.loads(response.read(65537))


def decode(png_bytes):
    return cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)


def engine(capture_path, round_dir, request_id):
    (round_dir / "engine.json").write_text(json.dumps({"request_id": request_id}),
                                           encoding="utf-8")
    return {"status": "LOCATION_ONLY", "targets": [], "decision": None,
            "width": 1280, "height": 720}


def expect_503(base):
    try:
        post(base)
        raise AssertionError("failed capture was accepted")
    except urllib.error.HTTPError as error:
        assert error.code == 503, error.code


def main():
    out = root / "sim/build/vision/base-backend"
    shutil.rmtree(out, ignore_errors=True)
    scene = {"frame": frame_like(40), "fail": None, "reads": 0}

    def read():
        scene["reads"] += 1
        if scene["fail"] is not None:
            raise scene["fail"]
        return scene["frame"]

    captures = BaseOverlayCaptures(read)
    server = make_server(port=0, root=out / "service", captures=captures, engine=engine,
                         order={"bolt": 1, "nut": 1, "washer": 1})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status = get(base, "/v1/status")
        assert status["backend"] == "BASE" and status["prototype"] is False

        # 正常轮：实时捕获后端 → prototype=False；capture.png + 哈希侧车；一轮恰一次取帧
        packet1 = post(base)
        validate_packet(packet1)
        assert packet1["prototype"] is False and packet1["status"] == "LOCATION_ONLY"
        assert scene["reads"] == 1
        sessions = out / "service" / packet1["session_id"][:8]
        round1 = sessions / f"check-{packet1['check_id']:06d}"
        png1 = (round1 / "capture.png").read_bytes()
        assert png1.startswith(b"\x89PNG\r\n\x1a\n")
        assert (round1 / "capture.sha256").read_text(encoding="ascii").strip() == \
            hashlib.sha256(png1).hexdigest()
        assert int(decode(png1)[0, 0, 0]) == 40

        # 每轮新帧：源内容变化后旧轮产物不变化，且取帧次数按轮递增
        scene["frame"] = frame_like(60)
        packet2 = post(base)
        assert scene["reads"] == 2
        round2 = sessions / f"check-{packet2['check_id']:06d}"
        assert int(decode((round2 / "capture.png").read_bytes())[0, 0, 0]) == 60
        assert png1 == (round1 / "capture.png").read_bytes()

        # 无视频/超时（OSError 系）：503、无 packet.json/capture.png
        scene["fail"] = TimeoutError("no video")
        expect_503(base)
        failed = sessions / f"check-{packet2['check_id'] + 1:06d}"
        assert failed.exists() and not (failed / "packet.json").exists()
        assert not (failed / "capture.png").exists()
        scene["fail"] = None

        # 坏几何（非 720p BGR uint8）：同样拒绝发布
        good = scene["frame"]
        scene["frame"] = np.zeros((720, 1280), np.uint8)
        expect_503(base)
        scene["frame"] = good

        # 恢复：新轮正常
        scene["frame"] = frame_like(80)
        packet3 = post(base)
        round3 = sessions / f"check-{packet3['check_id']:06d}"
        assert int(decode((round3 / "capture.png").read_bytes())[0, 0, 0]) == 80
        assert scene["reads"] == 5
        assert not list(out.rglob("*.pending"))
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: base overlay backend new-frame/fault-503/prototype-false (off-board stand-in)")


if __name__ == "__main__":
    main()
