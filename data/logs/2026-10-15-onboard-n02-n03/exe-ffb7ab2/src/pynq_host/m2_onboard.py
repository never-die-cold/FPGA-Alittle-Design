#!/usr/bin/env python3
"""m2_onboard —— 模块二上板分步自检（板端运行，PC 上仅语法检查）

用法（板端，vision.bit / vision.hwh / vision_regs.py 同目录）：
    python3 m2_onboard.py env      # 环境与文件检查
    python3 m2_onboard.py load     # 下载 overlay，打印 ip_dict 与基址核对
    python3 m2_onboard.py smoke    # R11/R12 读回 + 短超时 commit（兼测视频在位）
    python3 m2_onboard.py demo     # vision_demo 演示序列（需 HDMI IN 有视频）

判据：PASS = 该步通过；NOVIDEO = overlay/寄存器正常但无输入视频（exit 3）；
FAIL = 实际错误（exit 1）。上板日志与离板日志同一门禁口径归档。
"""
import os
import sys

AXI_REGS_BASE = 0x40000000  # create_hdmi_bd.tcl: assign_bd_address 0x40000000/64K


def _fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def cmd_env():
    print(f"python={sys.version.split()[0]}")
    try:
        import pynq
        print(f"pynq={pynq.__version__}")
    except Exception as e:
        _fail(f"pynq import: {e}")
    here = os.path.dirname(os.path.abspath(__file__))
    for f in ("vision.bit", "vision.hwh", "vision_regs.py"):
        p = os.path.join(here, f)
        print(f"{f}: {'OK' if os.path.isfile(p) else 'MISSING'} "
              f"({os.path.getsize(p) if os.path.isfile(p) else 0} B)")
    print("PASS: env")


def cmd_load():
    from pynq import Overlay
    here = os.path.dirname(os.path.abspath(__file__))
    ol = Overlay(os.path.join(here, "vision.bit"))
    print("ip_dict:")
    for name, meta in ol.ip_dict.items():
        base = meta.get("phys_addr", meta.get("base_addr", 0))
        rng = meta.get("addr_range", meta.get("size", 0))
        print(f"  {name} @ 0x{base:08X} range 0x{rng:X}")
    segs = [n for n, m in ol.ip_dict.items()
            if m.get("phys_addr", m.get("base_addr")) == AXI_REGS_BASE]
    if not segs:
        _fail(f"ip_dict 中无 0x{AXI_REGS_BASE:08X} 段——布局与预期不符")
    print(f"axi_regs 段: {segs[0]} @ 0x{AXI_REGS_BASE:08X}")
    print("PASS: load")


def cmd_smoke():
    from vision_regs import VisionRegs
    v = VisionRegs(base=AXI_REGS_BASE)
    print(f"R11 busy={v.read_reg(11) & 1} R12 applied={v.read_reg(12)}")
    v.apply_preset("GRAY")
    try:
        cfg = v.commit(timeout=1.0)
    except TimeoutError:
        print("NOVIDEO: commit 未在帧首确认——寄存器通路 OK 但无输入视频"
              "（查 HDMI IN 源/线材）")
        sys.exit(3)
    st = v.status()
    print(f"commit 配置号={cfg} status={st}")
    if st["applied_config_id"] != cfg:
        _fail(f"R12={st['applied_config_id']} != 提交号 {cfg}")
    print("PASS: smoke（视频在位，帧首整组应用已确认）")


def cmd_demo():
    import vision_demo
    vision_demo.main()
    print("PASS: demo 序列完成")


if __name__ == "__main__":
    cmds = {"env": cmd_env, "load": cmd_load,
            "smoke": cmd_smoke, "demo": cmd_demo}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(2)
    cmds[sys.argv[1]]()
