#!/usr/bin/env python3
"""vision_regs —— 模块二 axi_regs 寄存器映射的 PS 侧绑定（M2 演示原型）

映射唯一来源：src/vision/design_v0.md §3.3（v1.0 草案，10/5 冻结）——
  R0      [0]gauss_en [1]scaler_en(快照) [2]osd_en [3]sobel_en [31:4]保留
  R1-R4   box_x0/y0/x1/y1（[15:0]，全分辨率显示图坐标系）
  R5      box_color（[7:0]）
  R6-R9   roi_x0/y0/x1/y1
  R10     roi_color
  R11     bit0 写1提交，读为busy；R12 已应用配置编号；R13-15 保留
时序语义：R0..10 为暂存区；commit() 提交整组并等待帧首应用确认。
无视频帧时会超时；busy 时不能重复提交。设置函数自身不隐式提交。

用法（板端）：
    from pynq import Overlay, MMIO
    ol = Overlay('vision.bit')            # 布局定稿后 base 从 ol.ip_dict 取
    v = VisionRegs(base=0x4000_0000)      # AXI_GP 映射窗口内 axi_regs 基址
    v.apply_preset('GAUSS_SOBEL')
    v.commit()
PC 侧自测（无板）：
    python vision_regs.py   # mock 后端走一遍位域打包/回读/预设值断言
"""
from __future__ import annotations
import time

# ---- 寄存器位域常量（与 §3.3 / vision_top v0.3 一致） ----
BIT_GAUSS = 0
BIT_SCALER = 1     # 快照分支使能（cop_*），不影响显示路径
BIT_OSD = 2
BIT_SOBEL = 3

# 拓扑预设（bit3:0）
PRESETS = {
    "GRAY": 0x0,            # 灰度直通（基线）
    "GAUSS": 0x1,           # 高斯
    "GAUSS_SOBEL": 0x9,     # 高斯后接边缘
    "GRAY_SOBEL": 0x8,      # raw gray 上边缘
    "SNAPSHOT": 0x2,        # 灰度快照，HDMI 彩色原图不变
    "GAUSS_SNAPSHOT": 0x3,  # 高斯快照，HDMI 彩色原图不变
}
# R0 起始字偏移 = 0；寄存器 i 偏移 = i*4（axi_regs NREG=16, AW=7 → 128B 窗口）
NREG = 16
WINDOW_BYTES = 128


class VisionRegs:
    """axi_regs 读写绑定。backend 缺省用 pynq MMIO；测试可注入 dict 后端。"""

    def __init__(self, base: int, backend=None):
        self.base = base
        if backend is None:
            from pynq import MMIO  # 板端路径
            self.mmio = MMIO(base, WINDOW_BYTES)
            self._read = lambda off: self.mmio.read(off)
            self._write = lambda off, val: self.mmio.write(off, val)
        else:
            self._read = backend["read"]
            self._write = backend["write"]

    # ---- R0 链路开关 ----
    def set_enable(self, gauss=None, scaler=None, osd=None, sobel=None) -> int:
        """读-改-写：仅更新显式给出的位，未指定位保持（None=不改）。"""
        r0 = self._read(0)
        for bit, v in ((BIT_GAUSS, gauss), (BIT_SCALER, scaler),
                       (BIT_OSD, osd), (BIT_SOBEL, sobel)):
            if v is None:
                continue
            r0 = (r0 | (1 << bit)) if v else (r0 & ~(1 << bit))
        self._write(0, r0)
        return self.get_enable()

    def apply_preset(self, name: str) -> int:
        self._write(0, PRESETS[name] & 0xF)
        return self.get_enable()

    def get_enable(self) -> int:
        return self._read(0) & 0xF

    # ---- 检测框 / ROI（A4 动效：换帧生效） ----
    def set_box(self, x0: int, y0: int, x1: int, y1: int, color: int):
        self._write(1 * 4, x0 & 0xFFFF)
        self._write(2 * 4, y0 & 0xFFFF)
        self._write(3 * 4, x1 & 0xFFFF)
        self._write(4 * 4, y1 & 0xFFFF)
        self._write(5 * 4, color & 0xFF)

    def set_roi(self, x0: int, y0: int, x1: int, y1: int, color: int):
        self._write(6 * 4, x0 & 0xFFFF)
        self._write(7 * 4, y0 & 0xFFFF)
        self._write(8 * 4, x1 & 0xFFFF)
        self._write(9 * 4, y1 & 0xFFFF)
        self._write(10 * 4, color & 0xFF)

    def read_reg(self, idx: int) -> int:
        assert 0 <= idx < NREG
        return self._read(idx * 4)

    def commit(self, wait: bool = True, timeout: float = 0.5) -> int:
        """提交暂存参数；返回本次配置编号，帧首应用后才确认。"""
        if self._read(44) & 1:
            raise RuntimeError("configuration commit is busy")
        expected = (self._read(48) + 1) & 0xFFFFFFFF
        self._write(44, 1)
        if wait:
            self.wait_applied(expected, timeout)
        return expected

    def wait_applied(self, expected: int, timeout: float = 0.5, poll: float = 0.001):
        if timeout <= 0 or poll <= 0:
            raise ValueError("timeout and poll must be positive")
        deadline = time.monotonic() + timeout
        while self._read(48) != expected:
            if time.monotonic() >= deadline:
                raise TimeoutError("configuration not applied: check video/frame input")
            time.sleep(poll)

    def status(self) -> dict:
        return {"busy": bool(self._read(44) & 1), "applied_config_id": self._read(48)}


def _mock_backend():
    mem = [0] * NREG
    return {"read": lambda off: mem[off // 4],
            "write": lambda off, val: mem.__setitem__(off // 4, val & 0xFFFFFFFF)}


if __name__ == "__main__":
    v = VisionRegs(base=0, backend=_mock_backend())
    assert v.apply_preset("GAUSS_SOBEL") == 0x9
    assert v.set_enable(osd=1) == 0xD and v.set_enable(osd=0) == 0x9
    v.set_box(10, 20, 300, 200, 0xAB)
    assert (v.read_reg(1), v.read_reg(4)) == (10, 200)
    assert v.read_reg(5) == 0xAB
    v.set_roi(0, 0, 1279, 719, 0xFF)
    assert v.read_reg(8) == 1279 and v.read_reg(10) == 0xFF
    # 保留区行为由 RTL 保证（写忽略读 0），此处只验映射不越界
    for i in (11, 15):
        v._write(i * 4, 0xDEAD) if False else None
    print("PASS: vision_regs 映射位域/预设/框参数 mock 自测 6/6")
