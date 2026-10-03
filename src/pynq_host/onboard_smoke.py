#!/usr/bin/env python3
"""onboard_smoke —— vision overlay 上板分阶冒烟（板端 ~/vision 下运行）

用法（串口/ssh，PYNQ 自带 pynq 包）：
  python3 onboard_smoke.py load    # 阶段1: 装载 overlay，读 ip_dict
  python3 onboard_smoke.py regs    # 阶段2: axi_regs 读回（无需视频输入）
  python3 onboard_smoke.py video   # 阶段3: commit/确认 R12 递增（需 HDMI 源在出图）
  python3 onboard_smoke.py all     # 三阶连跑
  python3 onboard_smoke.py watch [秒=60]   # 断连重连观测：周期 commit 产生 R12 确认心跳，
                            # 运行中拔/插 HDMI，期望 STREAM → STALL/BUSY → STREAM
                            # （STALL=commit 超时；BUSY=在途提交被拒，非断流，单独计数）
  python3 onboard_smoke.py watch-mock      # 离板逻辑自测：假后端脚本化 2s 拔/4s 插，应 PASS(W)
退出码 = 首个失败阶段号（watch/watch-mock 为 9，全过 0）。阶段3 无视频时必然失败（commit 超时），
属预期现象，不是回归——先接好 HDMI 源（1280x720）再跑 video/all。
每阶段打印一行 `PASS(n):` / `FAIL(n):`，watch 打印 `EVENT/WATCH-SUMMARY`，可直接贴回串口记录存证。
判定口径：R12 是配置提交确认号（design_v0 §3.3），无提交不自增——"在流"判据为
commit 在帧首被确认（R12 递增到期望值），断流即 commit 超时；不是相邻读数比较。
"""
import sys

# sim/scripts/create_hdmi_bd.tcl 明确分配：pipe/s_axi/reg0 @ 0x40000000 (64K)
AXI_REGS_BASE = 0x40000000
VIDEO_TIMEOUT_S = 2.0  # 720p30 帧周期 ~33ms，2s 覆盖足够；无视频则在此超时


def _ip_props(ol, name):
    """PYNQ 版本间 ip_dict 条目可能是 dict 或 ContiguousRingBuffer 兼容对象。"""
    props = ol.ip_dict[name]
    getter = props.get if hasattr(props, "get") else (lambda k, d=None: getattr(props, k, d))
    return int(getter("phys_addr", 0)), int(getter("addr_range", 0))


def stage_load():
    from pynq import Overlay
    ol = Overlay("vision.bit")
    if not ol.is_loaded():
        raise RuntimeError("overlay reports not loaded")
    pipe_names = [n for n in ol.ip_dict if "pipe" in n]
    if not pipe_names:
        raise RuntimeError(f"ip_dict 无 pipe 条目: {list(ol.ip_dict)}")
    for n in pipe_names:
        phys, rng = _ip_props(ol, n)
        print(f"  ip_dict: {n} @ 0x{phys:08X} range 0x{rng:X}")
    name = pipe_names[0]
    phys, _ = _ip_props(ol, name)
    if phys != AXI_REGS_BASE:
        raise RuntimeError(f"{name} 基址 0x{phys:08X} != 契约 0x{AXI_REGS_BASE:08X}，vision_regs 需回填")
    print(f"PASS(1): overlay 装载，axi_regs 段 {name} @ 0x{phys:08X} 与 BD 分配一致")
    return ol


def stage_regs():
    from vision_regs import VisionRegs
    v = VisionRegs(base=AXI_REGS_BASE)
    st = v.status()
    print(f"  R11 busy={st['busy']} R12 applied_config_id={st['applied_config_id']}")
    # R0 读改写回环：只动 staging 区不 commit，不影响显示路径
    r0 = v.get_enable()
    v.set_enable(osd=1)
    assert v.get_enable() == (r0 | 0x4), "R0 bit2 写读不一致"
    v._write(0, r0)
    assert v.get_enable() == r0
    print(f"PASS(2): MMIO 读写回环一致，R0=0x{r0:X}（staging 未提交，已还原）")


def stage_video():
    from vision_regs import VisionRegs
    v = VisionRegs(base=AXI_REGS_BASE)
    before = v.status()["applied_config_id"]
    id1 = v.commit(timeout=VIDEO_TIMEOUT_S)
    id2 = v.commit(timeout=VIDEO_TIMEOUT_S)
    after = v.status()["applied_config_id"]
    assert (id1, id2, after) == (before + 1, before + 2, before + 2), \
        f"确认编号不连续: {before}->{id1}->{id2}->R12={after}"
    print(f"PASS(3): 视频在流，两次提交均帧首确认 R12 {before} -> {after}")
    return v


def stage_watch(seconds, backend=None):
    """断连重连观测：周期 commit 为心跳——R12 是配置确认号，无提交不自增。

    在流 = commit 在帧首被确认（R12 达到期望值，≤1 帧周期）；
    断流 = commit 超时（挂起提交在流恢复后帧首补确认）；
    BUSY = 在途提交未消费时重复提交被拒（R11 busy，vision_regs.commit 抛
    RuntimeError），非断流，单独计数供存证。其余异常不算 STALL，直接抛给
    FAIL(W)——MMIO 类硬故障不能伪装成断流（上板挂死教训）。
    print 全部带 flush，nohup/重定向可实时 tail。backend 供 watch-mock 注入。
    """
    import time
    from vision_regs import VisionRegs
    v = VisionRegs(base=AXI_REGS_BASE, backend=backend)
    last = None
    saw_stream = saw_stall = saw_busy = False
    t0 = time.time()
    while time.time() - t0 < seconds:
        ok = False
        state = "STALL"
        try:
            expected = v.commit(timeout=1.0)
            ok = v.status()["applied_config_id"] == expected
            state = "STREAM" if ok else "STALL"
        except TimeoutError:
            state = "STALL"
        except RuntimeError:
            state = "BUSY"
            saw_busy = True
        saw_stream |= ok
        saw_stall |= not ok
        if state != last:
            print(f"EVENT({time.time() - t0:.1f}s): {state}", flush=True)
            last = state
        time.sleep(0.5)
    print(f"WATCH-SUMMARY: saw_stream={saw_stream} saw_stall={saw_stall} "
          f"saw_busy={saw_busy} end_stream={last}", flush=True)
    if not saw_stream:
        raise RuntimeError("全程未观测到视频流（确认 HDMI 源 1280x720 在出图再跑）")
    if saw_stall and last != "STREAM":
        # last 是状态字符串，真值判断恒真——必须显式比较（首轮实现曾用 not last，致
        # 收尾停在 STALL/BUSY 也 PASS，由理解门槛问答抓出）
        raise RuntimeError(f"观测到断流/busy 未恢复（end={last}）")
    print(f"PASS(W): 观测 {seconds}s 完成（{'断流后已恢复' if saw_stall else '持续在流'}）",
          flush=True)


def _fake_replug_backend():
    """watch-mock 假硬件：按真实 R12 语义建模（design_v0 §3.3）。

    - R12 只在帧首消费一次 pending 提交时 +1 并清 busy，无提交则冻结（不随帧自增）；
    - 帧首 tick 时钟驱动（33ms/帧）：任意寄存器读先推进状态机，流断则 tick 停，恢复后补 latch。
    脚本化 2s 拔线、4s 插回。
    """
    import time

    class _Fake:
        def __init__(self):
            self.regs = [0] * 16
            self.t0 = time.monotonic()
            self._last = self.t0

        def _stream(self):
            t = time.monotonic() - self.t0
            return t < 2.0 or t > 4.0

        def _tick(self):
            if self.regs[11] & 1 and self._stream():
                now = time.monotonic()
                if now - self._last >= 0.033:
                    self.regs[12] = (self.regs[12] + 1) & 0xFFFFFFFF
                    self.regs[11] = 0
                    self._last = now

        def read(self, off):
            self._tick()
            return self.regs[off // 4]

        def write(self, off, val):
            self.regs[off // 4] = val & 0xFFFFFFFF

    fake = _Fake()
    return {"read": fake.read, "write": fake.write}  # VisionRegs 后端约定：dict 带 read/write


STAGES = {"load": (stage_load,), "regs": (stage_load, stage_regs),
          "video": (stage_load, stage_regs, stage_video)}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("watch", "watch-mock"):
        try:
            if cmd == "watch":
                stage_watch(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
            else:
                stage_watch(6, backend=_fake_replug_backend())
        except Exception as e:
            print(f"FAIL(W): {type(e).__name__}: {e}", flush=True)
            return 9
        return 0
    if cmd not in STAGES:
        print(__doc__)
        return 2
    for n, stage in enumerate(STAGES[cmd], 1):
        try:
            stage()
        except Exception as e:
            print(f"FAIL({n}): {type(e).__name__}: {e}")
            return n
    return 0


if __name__ == "__main__":
    sys.exit(main())
