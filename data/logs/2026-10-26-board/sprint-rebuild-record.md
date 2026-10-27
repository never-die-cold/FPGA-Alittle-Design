# 冲刺重建记录（Agent B 独立完成线，2026-10-26 23:0X–00:2X）

> 用户授权"全开冲刺"后：A 已停，B 在本机完成了构建线+上板线全链。
> 红线变更经用户明示（"不管是 vivado 还是什么都可以做"）。

## S1/S2 补丁（本机，已生效）

1. `build/create_pynq_cop_bd.tcl`：空参 `assign_bd_address` 后**显式钉死三段**：
   - `*SEG_pl_reg0` → 0x40000000 / 4K
   - `*SEG_dma_Reg` → 0x40010000 / 64K
   - `*SEG_dma_control_Reg` → 0x40020000 / 64K
   匹配不足 3 段即 error（防静默漂移）。
2. `build/build_pynq_cop_gate.tcl`：bit/hwh copy 后加 **HWH 三基址 tripwire**
   （`C_BASEADDR` 三值缺失即 FAIL），再写 xsa。

## S3 重建（本机 Vivado 2026.1 batch，COP_PYTHON=Python312 实体）

四轮快速迭代：#1 死于 MS Store python3 空壳 stub；#2 死于 `get_bd_addr_spaces ps7/M_AXI_GP0`
（该空间在本版 Vivado 名为 `ps7/Data`，其调试打印反而给出全部段名）；#3 同因；
**#5 全绿**（日志 `data/logs/2026-10-26-build/gate-rebuild-5.log`）：

```
IMEM PRECHECK PASSED: first_word=00008117
IMEM MATERIALIZE PASSED: source_words=4094 depth=8192
HWH BASE GATE PASSED: COP=0x40000000 DMA=0x40010000 GPIO=0x40020000
PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=2.230 DSP=136 BRAM36=69.0 CDC_ALLOWLIST=CDC-15=73,CDC-3=12,CDC-6=7 DRC=0
```

## S4 重打包（`~/cop-pkg-edge-20261026/repack_edge.py`，双包同步）

- 新哈希：bit `f4720ff8…e611`、hwh `78272422…56c9`、xsa `5337d7cc…cea4`
- 双包 SHA256SUMS 复算 12/12 PASS（口径：清单排除自身与 FILES.txt）
- 打包内 hwh 三基址本地 grep 三确认 ✅

## 板卡故障叠加层（本轮新增事实）

- 复跑 fast-run（gate566b 与 imem 包）均 `AXI DMA MM2S timeout`；
  SLCR 转储显示该启动内 `FPGA1_CLK_CTRL=0x00000000`（FCLK1 被门控）+
  IO_PLL/ARM_PLL CTRL 读值异常——**pynq 3.1 `Clocks` 写入在此板行为损坏**
  （B4 的新 loader clock 含 Clocks 写入，是当晚首个写入者，头号嫌疑）。
- 处置：已 `sudo reboot` 清态；**重启后串口完全静默 + 网络不回**（>7 分钟），
  需现场检查电源/复位。B 线全部就绪，等板。

## 等板卡恢复后的执行序列（已定稿）

1. `loader clock --reads 20 --smoke-timeout 2`（新包，含正确钉死基址 hwh）
2. 正常 loader `run` 四例：zero / pattern / roi_001 / frame（每例独立 Overlay，
   固件单作业限制天然满足；fast-start 仅作 fallback）
3. 期望全 matches_expected=true（TSV 见包）；JSON/串口/哈希全留档
