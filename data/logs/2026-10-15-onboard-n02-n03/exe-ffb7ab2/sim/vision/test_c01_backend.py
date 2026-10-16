"""C01 捕获后端 × 服务 离板回归（W04）——所有权租约、独立副本与失败路径。

fake 环境（VDMA 寄存器/描述符/CAP1/分配器/代次）驱动真实驱动 src/pynq_host/c01_capture.py，
经 C01Captures 接入 vision_live_service：一轮 = 一个新单次租约；失败轮（等待期错误/完成超时/
采集期代次变化）不产 packet.json/capture.png，缓冲恰一次归还或按驱动契约隔离；恢复后新轮正常。
落盘在仓库内 sim/build/vision/c01-backend/。
覆盖 docs/c01-ddr-frame-ownership-v0.md §5 矩阵离板行：独立副本、错误/超时拒绝、代次变化、
恢复与归还；硬件侧"写事务完成/槽绑定"仍待 NC 实机（§7 注记）。
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
from c01_backend import C01Captures
from c01_capture import QUARANTINE, SHAPE, SingleFrameCapture
from vision_live_service import make_server
from vision_protocol import validate_packet

CR, SR, PARK, VSIZE, RUN = 0x30, 0x34, 0x28, 0xA0, 0x11011


class Status:
    def __init__(self, rig):
        self.rig = rig

    def read(self, offset):
        return self.rig.cap.get(offset, 0)


class Buffer(np.ndarray):
    def __new__(cls, address, rig):
        obj = np.zeros(SHAPE, np.uint8).view(cls)
        obj.physical_address = address
        obj.rig = rig
        obj.frees = 0
        return obj

    def invalidate(self):
        pass

    def freebuffer(self):
        if self.frees:
            self.rig.double_free += 1
            raise RuntimeError("double free of DMA buffer")
        self.frees += 1
        self.rig.frees += 1


class Rig:
    """最小 VDMA S2MM 替身：写 VSIZE 且 RS=1 视为启动；首个 SR 轮询回报完成/错误。

    complete=False 模拟不完成（超时）；error 置位模拟等待期 DMA 错误；
    fill 回调在返回完成态前注入本帧内容并可顺带改写 generation（模拟 overlay 重载）。
    """

    def __init__(self, complete=True, error=0, fill=None):
        self.reg = {CR: 0, SR: 1 | 0x1000, PARK: 0}
        self.cap = {offset: 0 for offset in range(0, 0x24, 4)}
        self.cap.update({0: 0x43415031, 4: 1, 0x14: 1280, 0x18: 720})
        self.status = Status(self)
        self.complete, self.error, self.fill = complete, error, fill
        self.generation = "gen-A"
        self.started = self.polled = False
        self.round_buffers = []
        self.frees = self.double_free = 0

    def read(self, offset):
        if offset == SR and self.started and not self.polled:
            self.polled = True
            if self.error:
                self.reg[SR] = 1 | self.error
            elif self.complete:
                if self.fill is not None:
                    self.fill(self.round_buffers[0])
                self.reg[CR] &= ~1
                self.reg[SR] = 1 | 0x1000
        return self.reg.get(offset, 0)

    def write(self, offset, value):
        if offset == SR:
            self.reg[SR] &= ~value
        elif offset == CR and value == 4:
            self.reg[CR], self.reg[SR] = 0, 1
        else:
            self.reg[offset] = value
            if offset == VSIZE and self.reg[CR] & 1:
                self.started, self.polled = True, False
                self.reg[SR] = 0
            if offset == CR and not value & 1:
                self.reg[SR] |= 1

    def allocate(self, shape=None, dtype=None):
        buffer = Buffer(0x10000000 + len(self.round_buffers) * 0x300000, self)
        self.round_buffers.append(buffer)
        return buffer

    def owner_factory(self):
        self.round_buffers = []
        return SingleFrameCapture(self, self.status, self.allocate,
                                  lambda: self.generation, timeout=0.5)


def frame_like(value):
    return np.full(SHAPE, value, np.uint8)


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
    out = root / "sim/build/vision/c01-backend"
    shutil.rmtree(out, ignore_errors=True)
    scene = {"frame": frame_like(10)}

    def fill(buffer):
        buffer[:] = scene["frame"]

    rig = Rig(fill=fill)
    captures = C01Captures(rig.owner_factory)
    server = make_server(port=0, root=out / "service", captures=captures, engine=engine,
                         order={"bolt": 1, "nut": 1, "washer": 1})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status = get(base, "/v1/status")
        assert status["backend"] == "C01" and status["prototype"] is False

        # 正常轮：真实硬件后端 → prototype=False；capture.png + 哈希侧车；缓冲恰一次归还
        packet1 = post(base)
        validate_packet(packet1)
        assert packet1["status"] == "LOCATION_ONLY" and packet1["prototype"] is False
        sessions = out / "service" / packet1["session_id"][:8]
        round1 = sessions / f"check-{packet1['check_id']:06d}"
        png1 = (round1 / "capture.png").read_bytes()
        assert png1.startswith(b"\x89PNG\r\n\x1a\n")
        assert (round1 / "capture.sha256").read_text(encoding="ascii").strip() == \
            hashlib.sha256(png1).hexdigest()
        assert int(decode(png1)[0, 0, 0]) == 10
        assert rig.frees == 4 and rig.double_free == 0
        assert not QUARANTINE

        # 独立副本：缓冲被下一帧内容替换后，上一轮产物不变化（§5 行 1）
        scene["frame"] = frame_like(20)
        packet2 = post(base)
        round2 = sessions / f"check-{packet2['check_id']:06d}"
        assert int(decode((round2 / "capture.png").read_bytes())[0, 0, 0]) == 20
        assert png1 == (round1 / "capture.png").read_bytes(), "独立副本随下一帧变化"
        assert rig.frees == 8

        # 等待期 DMA 错误：503、无 packet.json/capture.png、缓冲恰一次归还（§5 行 3）
        rig.error = 0x20
        expect_503(base)
        failed = sessions / f"check-{packet2['check_id'] + 1:06d}"
        assert failed.exists() and not (failed / "packet.json").exists()
        assert not (failed / "capture.png").exists()
        assert rig.frees == 12
        rig.error = 0

        # 完成超时：同上（§5 行 3/6 的超时路径）
        rig.complete = False
        expect_503(base)
        assert rig.frees == 16
        rig.complete = True

        # 采集期代次变化（模拟 overlay 重载）：拒绝发布且原生缓冲按契约隔离不归还（§5 行 4）
        def fill_and_flip(buffer):
            buffer[:] = scene["frame"]
            rig.generation = "gen-B"

        rig.fill = fill_and_flip
        expect_503(base)
        assert rig.frees == 16, "代次变化后原生缓冲不得被归还"
        assert len(QUARANTINE) == 1
        rig.fill = fill

        # 新代次下恢复：新租约独立、正常发布（§5 行 4 恢复）
        scene["frame"] = frame_like(30)
        packet3 = post(base)
        round3 = sessions / f"check-{packet3['check_id']:06d}"
        assert int(decode((round3 / "capture.png").read_bytes())[0, 0, 0]) == 30
        assert rig.frees == 20

        assert not list(out.rglob("*.pending"))
    finally:
        server.shutdown()
        server.server_close()
        for owner in list(QUARANTINE):  # 测试收尾：假环境已确认复位，安全释放隔离租约
            owner.token = rig.generation
            try:
                owner.close()
            except Exception:
                pass
            QUARANTINE.remove(owner)
    print("PASS: c01 backend service lease/copy/faults/quarantine/recovery (off-board stand-in)")


if __name__ == "__main__":
    main()
