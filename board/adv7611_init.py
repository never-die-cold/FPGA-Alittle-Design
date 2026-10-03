#!/usr/bin/env python3
# External ADV7611 receiver example only. PYNQ-Z2 HDMI is wired directly to PL;
# do not run this script for the PYNQ-Z2 on-board HDMI connectors.
"""adv7611_init —— PYNQ-Z2 HDMI IN（ADV7611）I2C 初始化 + EDID（上板验线用，M2）

状态：**骨架，上板验线时启用**。寄存器值表须对照 ADI 官方推荐脚本逐条核对后
置 RUN=True（Ultra-Vision 同芯片先例：docs/track_research.md §1.4）。目标格式
（决策单 D3 已拍板）：720p60 输入，RGB 444 24bit SDR 输出，DVI 模式（无 HDCP）。

I2C 布局（8bit 写地址 -> 7bit）：
  IO  0x98 -> 0x4C    CP  0x8C -> 0x46    HDMI 0x34 -> 0x1A
  DPLL 0x88 -> 0x44   KSV 0xA4 -> 0x52    EDID 0x6C -> 0x36    REP 0x64 -> 0x32
挂载总线（PS I2C 还是经 PL）待原理图复核（决策单 D2 条件）——bus_id 上板时确认。

流程：上电复位 -> HPD 置高 -> 写 EDID（本文件生成，校验和自洽）-> ADI 推荐寄存
  序列 -> 读 0xF4/0xF5 锁相状态自检。板端运行；PC 上可跑 EDID 生成自检：
  python adv7611_init.py --selftest
"""
import sys

# ---- ADI 推荐寄存器序列（720p60 RGB444 24bit SDR）——待与官方脚本逐条核对后启用 ----
# 格式：(io_map 写地址, 寄存器, 值, 备注)
REG_SEQ = [
    # (0x98, 0x01, 0x15, "fixed（ADI 推荐脚本常量，核对后启用）"),
    # (0x98, 0x02, 0xF2, "fixed：DDC 主从使能 + TRI-state 配置"),
    # (0x98, 0x03, 0x42, "fixed：音频/中断默认"),
    # ... 完整表上板日对照 ADI ADV7611 RECOMMENDED PRN（720p）补齐
]
RUN = False   # 核对完置 True 才真正下发

IO_MAP_7BIT = 0x4C
EDID_RAM_7BIT = 0x36


def build_edid_720p60() -> bytes:
    """128 字节 EDID v1.3：DVI 数字口，DTD = 1280x720@60（74.25MHz）。
    纯规格推导（VESA E-EDID），校验和自洽，可 PC 自检。"""
    b = bytearray(128)
    b[0:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"          # header
    b[8:10] = b"\x50\x4e"                                  # 厂商 "PN"（PYNQ 自拟）
    b[10:12] = (0x7611).to_bytes(2, "little")              # 产品码
    b[12:16] = b"\x01\xa0\x01\x01"                         # 周序列号
    b[17] = 1                                              # EDID v1.3
    b[18] = 0                                              # revision
    b[20] = 0x80                                           # 数字输入（DVI）
    b[21], b[22] = 128 // 2 - 1, 72 // 2 - 1               # 尺寸 ±cm
    b[23] = 0x78                                           # gamma
    b[24] = 0x29                                           # 特性：RGB4:4:4 + 时序支持
    # chromaticity/established/standard timing 留默认 0（演示源走 DTD）
    # 首个 DTD @ offset 54：1280x720@60（各时序量按 CTA-861 口径，单位=像素时钟/10kHz）
    pc = 7425                                              # 74.25MHz -> 7425
    b[54], b[55] = pc & 0xFF, pc >> 8                      # 像素钟
    b[56] = 1280 & 0xFF
    b[57] = 0x04 | ((1280 >> 8) << 4) & 0xF0               # Hactive low8 + Hblank high4
    hb = 1650 - 1280
    b[58] = hb & 0xFF
    b[59] = 0x20 | ((hb >> 8) << 4) & 0xF0                 # Hblank low8 + Vblank high4... (简化占位)
    vb = 750 - 720
    b[60] = (720 & 0xFF)
    b[61] = ((vb >> 4) & 0xF0) | 0x00
    b[62] = vb & 0xFF
    b[63] = 720 & 0xFF
    b[64] = (720 >> 8) << 4
    b[65] = (720 >> 8) & 0x0F
    b[66] = 0x00                                           # Hfront
    b[67] = 0x20                                           # Hsync width 40
    b[68:72] = b"\x1e\x00\x00\x80"                         # V 前沿/宽 + 极性（占位，验线时核对）
    b[74] = 0x01                                           # DTD 数量
    b[125] = 0                                             # 扩展块数
    b[126] = 0
    b[127] = (-sum(b[:127])) & 0xFF                        # 校验和
    return bytes(b)


def _selftest():
    ed = build_edid_720p60()
    assert len(ed) == 128 and sum(ed) % 256 == 0
    assert ed[0:8] == b"\x00\xff\xff\xff\xff\xff\xff\x00"
    pc = ed[54] | (ed[55] << 8)
    assert pc == 7425, f"pixel clock word {pc} != 7425"
    print(f"PASS: EDID 128B, checksum ok, 720p60 DTD pixel-clock word = {pc} (74.25MHz)")


def init(bus_id: int = 2):
    """板端执行：写 EDID + 推荐序列 + 锁相自检。RUN=False 时不写任何寄存器。"""
    from smbus2 import SMBus  # 板端 PYNQ 镜像自带
    assert RUN, "寄存器值表未核对，禁止下发（见文件头）"
    ed = build_edid_720p60()
    with SMBus(bus_id) as bus:
        for off in range(0, 128, 16):
            bus.write_i2c_block_data(EDID_RAM_7BIT, off, list(ed[off:off + 16]))
        for (dev, reg, val, _note) in REG_SEQ:
            bus.write_byte_data(dev >> 1, reg, val)
        # 锁相自检：IO map 0xF4/0xF5（5V/HDMI 状态）读回——具体判据验线时定
        st = bus.read_byte_data(IO_MAP_7BIT, 0xF5)
        print(f"ADV7611 init done, status 0xF5 = {st:#04x}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print("板端运行入口 init(bus_id)；当前骨架状态，先 --selftest 验 EDID")
