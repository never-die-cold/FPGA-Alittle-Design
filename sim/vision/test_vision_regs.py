"""离板配置协议自检；mock 帧事件显式推进，不伪装为 MMIO/板上验收。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from vision_regs import VisionRegs


class Mock:
    def __init__(self):
        self.mem = [0] * 16
        self.snapshot = None
        self.active = [0] * 11

    def read(self, off):
        return self.mem[off // 4]

    def write(self, off, value):
        i = off // 4
        if i == 11 and value & 1:
            if self.mem[11]:
                raise RuntimeError("SLVERR: busy")
            self.snapshot = self.mem[:11]
            self.mem[11] = 1
        elif i < 11:
            self.mem[i] = value

    def frame(self):
        if self.snapshot is not None:
            self.active = self.snapshot
            self.snapshot = None
            self.mem[11] = 0
            self.mem[12] = (self.mem[12] + 1) & 0xFFFFFFFF


def main():
    m = Mock()
    v = VisionRegs(0, {"read": m.read, "write": m.write})
    v.apply_preset("GAUSS_SNAPSHOT")
    v.set_box(10, 20, 300, 400, 255)
    epoch = v.commit(wait=False)
    assert epoch == 1 and v.status()["busy"] and m.active == [0] * 11
    v.set_box(50, 60, 500, 600, 128)
    try:
        v.commit(wait=False)
        raise AssertionError("busy commit accepted")
    except RuntimeError:
        pass
    m.frame()
    v.wait_applied(epoch)
    assert m.active[1:6] == [10, 20, 300, 400, 255]
    epoch = v.commit(wait=False)
    try:
        v.wait_applied(epoch, timeout=0.005)
        raise AssertionError("missing frame did not time out")
    except TimeoutError:
        pass
    m.frame()
    v.wait_applied(epoch)
    assert m.active[1:6] == [50, 60, 500, 600, 128]
    m.mem[12] = 0xFFFFFFFF
    assert v.commit(wait=False) == 0
    m.frame()
    v.wait_applied(0)
    assert v.status() == {"busy": False, "applied_config_id": 0}
    print("PASS: PS configuration staging/commit/ack/busy/timeout/epoch wrap mock protocol")


if __name__ == "__main__":
    main()
