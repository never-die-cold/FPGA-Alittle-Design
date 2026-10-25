# 2026-10-25 DMA16 上板：40 MHz 时钟门禁 PASS；CPU 未执行固件（BLOCKED，JL）

> 包：`cop-board-gate-759744b99891`（tar `7160fffb…54432b`，**111/111 OK**，bit `d14a4bd0…2a1a`、
> hwh `928f0d59…9107`、xsa `755f7033…d96ec` 均与 JL 发布值一致）。
> 结论：**时钟门禁（OPEN-BOARD-CLK-1 的测量判据）板上 PASS**；随后发现 **RISC-V CPU 未执行
> 固件**（NO_ACK 根因），超出 PS 侧可诊断边界，交 JL。`BOARD`/`BOARD_CLOCK` 状态见 §6。

## 1. 环境与传输

- COM4 串口（MobaXterm 关闭后独占）；Vivado 2026.1 `hw_server`；无以太网。
- loader 所需 8 个文件经串口 base64（`cat > 文件` + Ctrl+D 方式）传到板上
  `~/cop-pkg/`，**板上 sha256 与包内 SHA256SUMS 逐项一致 8/8**：
  loader.py `d39630…`、manifest `4a4147…`、payload.bin `14a199…`、hwh `928f0d…`、
  zero/pattern input.hex `9b5ee3…`/`9bee29…`、EXPECTED `256f10…`、bit `d14a4bd0…`。
  工具：`sim/scripts/serial_send_v2.ps1`（v1 的 heredoc 方式会在大文件时溢出 tty 缓冲，
  已弃用；教训见 §7）。
- JTAG `PROGRAM PASSED`（program_dma16.log）。

## 2. 时钟门禁：两步才 PASS（重要教训）

| 步骤 | 结果 |
|---|---|
| 第一次 `loader clock --reads 20`（旧 PL 在 40 MHz 改钟后继续跑） | `measured_fclk1_mhz=40.000000`，但 20 次首读**全 0x0** → loader 正确 BLOCKED |
| 改顺序：**先 FCLK1=40，再重新配置 PL**（JTAG 重烧，PS 不复位） | 寄存器读 STATUS ×5 = `0x1` 稳定 |
| 再跑 `loader clock --reads 20` | **`measured_fclk1_mhz=40.000000`，20 次首读全部 `0x00000001`** ✅ |

**结论**：JL 的“首读 0x0=超频”假设不成立（40.000000 MHz 下仍 0x0）；真正规律是
**改钟后必须重新配置 PL**，让 cop 域复位同步器在新时钟下重新释放（改钟后 STATUS=0x0
持续存在的旧 PL 视为失效）。证据：[loader-clock.txt](loader-clock.txt)、
[probe-40mhz-reprogram.txt](probe-40mhz-reprogram.txt)、[loader-clock-pass.txt](loader-clock-pass.txt)。

## 3. NO_ACK 与 CPU 死亡证据链

1. loader `run --case zero`：预检全过（manifest/SHA/CRC/HWH/16 位 DMA）、配置回执
   `CFG_APPLIED==CFG_SEQ`、两次 DMA 成功（`DMA_BYTES` 回读一致、无 payload_error），
   然后 **`NO_ACK: firmware did not assert ACCEPTED`**（[loader-run-zero.txt](loader-run-zero.txt)）。
2. 现场快照：`STATUS=0x61`（READY+CFG_VALID+MODEL_VALID，全 GO）、`DMA_BYTES=4096`=
   `ROI_COUNT×4096`、`FW_DECISION=0x0`（[noack-diag.txt](noack-diag.txt)、[noack-diag2.txt](noack-diag2.txt)）。
3. CPU 存活探测：PS 写 `ROI_COUNT=17`（固件应走 `count>16 → finish → FW_DECISION≠0`）
   → 2 s 后 `FW_DECISION` 仍 0；cop 域本身活着（该写触发了 `CFG_VALID` 撤销，
   STATUS 0x61→0x41，OPEN-3 行为正确）（[alive-test.txt](alive-test.txt)）。
4. **决定性**：fresh Overlay 下载（CPU 重新上电）后每 0.5 s 采样 14 次、共 6.5 s：
   `FW_DECISION` 恒 `0x0`。固件等待循环 guard（`COP_POLL_LIMIT=1e6`，约 0.4–1.5 s）
   必然超时并写 CONFIG 判定——从未发生。**CPU 没有执行 cop_job 固件。**
   （[bootprobe.txt](bootprobe.txt)，脚本 `sim/build/vision/cop_bootprobe.py`）

**最可能根因（JL 确认）**：IMEM 的 `initial $readmemh("src/riscv_fw/cop_job.hex")`
是相对路径，Vivado 综合从工程目录解析；若未命中仅告警，BRAM 保留 initial 兜底值
（全 NOP），CPU 永远 NOP 滑动——所有现象吻合（guard 逻辑永不到达 finish；
PS 侧 cop 寄存器全部正常）。sim 的 `firmware_e2e` 由 TB 自己 `$readmemh` 载入，
**不能证明 bit 里带 IMEM 初值**；门禁 Tcl 只查 hex 新鲜度，不查综合告警。

## 4. 给 JL 的动作

1. 确认 bit 内 IMEM init：综合日志查 `$readmemh` 是否命中 `cop_job.hex`
   （`build_pynq_cop_gate.tcl` 从工程目录运行时相对路径大概率失效）；
   建议改为绝对路径/`add_files` 显式加入，或综合后 readback 校验 IMEM 初值。
2. 门禁 Tcl 增加 fail-closed：`$readmemh` 未命中（log warning）时判 FAIL。
3. loader `clock` 的判据补充说明：改钟后必须重新配置 PL 再测（本记录 §2 的顺序），
   否则 20 次首读会因旧 cop 域失效而全 0x0——这不是时钟问题。
4. `NO_ACK` 在 CPU 修复后应自然消失；若仍 NO_ACK，再查 core→cop 邮箱 ACK。

## 5. 三件事（本轮 WC 板级）

- **做成了**：新包全链核验（111/111 + 8 文件板上哈希）；40 MHz 时钟门禁 PASS
  （含“改钟后必须重配 PL”的顺序发现）；串口 base64 传 4 MB bit 逐字节一致；
  NO_ACK 根因收敛到“CPU 未执行固件”并给出时间序列证据。
- **拿什么证明**：本目录全部原始串口记录 + 板上 sha256 + loader 输出。
- **还差什么**：pattern/zero 推理结果——等 JL 修复 IMEM init 出新包后重跑
  `clock` → `run zero` → `run pattern`；`BOARD`/`BOARD_CLOCK` 均未到 PASS 口径。

## 6. 状态口径

- `BOARD_CLOCK`：40.000000 MHz 回读 + 20 次首读 0x1 已实测 PASS（§2），但按 JL 三态
  约定该字段由 JL 打包时写死，本轮不改包；实际证据以本目录为准。
- `BOARD=UNVERIFIED_NEEDS_NC`：无推理结果，下载/预检不等于验收。
- 温度：烧写后 XADC raw 2676 → ≈56.2 °C（[probe-40mhz-reprogram.txt](probe-40mhz-reprogram.txt)）。

## 7. 复现

```bash
# 板上（串口 COM4；sudo 密码为 PYNQ 默认，勿入日志）
loader clock --reads 20                     # 先于 PL 重配会 20x0；重配后 20x1
loader run --package /home/xilinx/cop-pkg --case zero --measurement ...
# 串口传文件
powershell -File sim/scripts/serial_send_v2.ps1 -PackageRoot <pkg> [-Files ...]
```

教训：交互式 shell 的 heredoc 逐行 readline 撑不住 115200 连续灌入（丢字节且
`B64EOF` 失配卡死，需 Ctrl+C 恢复）；`cat > f` + Ctrl+D 块读取可靠。
