# 2026-10-26 新 bit 上板：时钟门禁 PASS、DMA 路径未通过（板卡需断电）

> 执行：本机（NC 线）｜包：`build/board-package-j02`（本机新构建 bit `566b512a…`）
> 结论：**时钟/固件 PASS；AXI DMA 首笔超时，且失败后板卡进入不可恢复状态。**

## 1. 本机新构建（门禁正式 PASS）

```text
IMEM POST-SYNTH GATE PASSED: first_word=00008117 nonzero=1 cells=8
PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=2.771 DSP=136 BRAM36=69.0 CDC_ALLOWLIST=CDC-15=73,CDC-3=12,CDC-6=7 DRC=0
```

产物：bit `566b512abd63140fc9137e3c49c3d2a74b46520cf323139e914672aa35379032`。

构建踩坑：Vivado 导出 `PYTHONHOME`（自带 3.13）会污染门禁里的 Python 3.12 子进程
（`SRE module mismatch`）。本机用 `build/_gate_env.tcl` 清空该变量后通过；提交脚本未改。

## 2. 上板记录（`clock`，stock loader）

```text
board_sequence=set_fclk,reconfigure_pl,wait_stable,pulse_fclkreset1,status_check
measured_fclk1_mhz=40.000000
status_first_reads=0x00000001 ×20
firmware_smoke=PASS status=0x00000001 fw_decision=0x00001003
```

→ **40 MHz 回读正确、20/20 首读 READY、固件在被执行**。IMEM 修复在本机构建上同样成立。

## 3. 失败：AXI DMA MM2S 超时（两条入口都失败）

- stock loader `run --case zero` → `BLOCKED: AXI DMA MM2S timeout`；
- 板端 fast runner（C 极短脉冲）`--case roi_001` / `--case zero` 同样超时；
- 连 21:40 已 PASS 过的 known-good 包，之后也超时 → **不是包的问题，是板卡状态**。

寄存器现场：`DMACR=0x10003`、`DMASR=0x0`、`DMASA/DMALEN` 已写入（36032 B）。
DMASR 既非 Halted 也非 Idle，说明 DMA 在等流端 TREADY（cop 侧没有继续收）。

## 4. 三个已查清的 PYNQ 坑（重要，可复用）

1. **同目录不能放 `.xsa`**：`embedded_device.is_xsa()` 只看 `.bit` 旁边有没有 `.xsa`；
   有就把位流当 XSA 解析，报 `UnknownInputFileExtension … .bit is not a valid input`。
   打包器已改成把 xsa 放到 `xsa/` 子目录，不进 `payload/`。
2. **`Overlay(download=True)` 对同一位流是空操作**：PL 没有被重新配置，
   `DMACR` 保留上一次的 `0x10003` 即为证据。要真重配必须换一个位流文件名。
3. **stock loader 的 `prepare_board` 会 pulse SLCR `FPGA_RST_CTRL`**：本板回读为 0，
   可能连带复位 FCLK0/AXI；另一会话已因它在板上挂死过一次。
   → 上板只走 `cop_board_fast_run.py`（自带 C 极短脉冲，不碰 SLCR）。

## 5. 当前状态与下一次尝试（单次、不重试）

板卡在第一次 DMA 超时后不可恢复：SSH banner reset、ping 不通，需断电。

断电后**只做一次**：

```bash
sudo -E /usr/local/share/pynq-venv/bin/python3 \
  payload/tools/cop_board_fast_run.py --package /home/xilinx/cop-pkg-trained566b \
  --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30
```

判据：`class 2 / margin 53 / score 6837 / logits -12,-30,41`。
若仍超时：**不要重试**，直接记录并能断则断——重试会把板卡再次锁死。

## 6. 证据文件

`clock.txt`、`zero.txt`（stock loader）、`zero-fast.txt`、`trained-roi001.txt`、`sha256sum.txt`
均为原始输出，未编辑。
