# 2026-10-23 协处理器首次上板：包/烧写/只读预检（PARTIAL；FCLK/loader 阻塞）

> 交接包已验证并烧入；只读预检通过到 `IP_ID/STATUS/ERROR_CODE/RESULT_SEQ`。
> **不是 40 MHz 板级通过，也没有 pattern/zero 推理结果。**
> 当前板卡 boot FSBL 给 FCLK1=142.857 MHz，而设计门禁是 40 MHz；JTAG 烧 `.bit`
> 不会应用 bitstream 内的 PS7 配置。另：包内没有 PS payload/ROI loader。
>
> `BOARD=UNVERIFIED_NEEDS_NC`；下发成功 ≠ 板级验收。

## 1. 交接包校验（2026-10-23）

| 项 | 结果 |
|---|---|
| 包 | `dist/cop-board-gate-21c4e751bbe8.tar.gz`，1,254,148 B |
| tar SHA256 | `d74189b9e1db2d0b7b0d7256a280ec166be8b35868b9cb01664a277bd8e76046`（与侧车哈希值一致；侧车路径是 JL 机器绝对路径） |
| 106 文件 | **106/106 OK**（[package-verify.txt](logs/package-verify.txt)） |
| bit SHA256 | `7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c` |
| hwh SHA256 | `cba4d12c58213897c0dbdafd327348ce5d4bd9d21dad6d5a469eb44bd03d799d` |
| VERSION | `BITSTREAM=JL_GATE_PASSED_UNVERIFIED_ON_BOARD`、`VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`、`BOARD=UNVERIFIED_NEEDS_NC`、含 `BUILD_REPRO` |
| EXPECTED | pattern `0/0/0`、zero `2/2/258`；logits `1,-3,1` / `2,-3,4`；两者 `low_conf=1` |
| Address Map | `0x40000000-0x40000FFF` = `pl/S_AXI`；`0x40010000` = DMA；`0x40020000` = dma_control |

## 2. 板卡与烧写

- PYNQ 3.1，Linux `6.6.10-xilinx-v2024.1`（Ubuntu 22.04），armv7l。
- COM4 `115200-8N1` → `xilinx@pynq`；Vivado 2026.1 JTAG 只读探测到 `arm_dap_0` + `xc7z020_1`。
- `board/scripts/program_soc.bat` + `VIVADO=D:\vivado\2026.1\Vivado\bin\vivado.bat`：
  **PROGRAM PASSED** 两次；日志 [program_cop.log](logs/program_cop.log)、
  [program_cop2.log](logs/program_cop2.log)。
- 第一次烧写后（未做 PS 复位）直接读 `0x40000000`，命令没有返回、串口失去响应；
  用 `xsdb` `rst -system` 复位恢复（[after-jtag-reset.txt](logs/after-jtag-reset.txt)），
  随后重新烧写；PL/AXI 才正常响应。**这是首次失败现象原文**。
- 复位后 PL 状态：`fpga_manager=unknown`（JTAG 配置，不走 sysfs `operating`），但
  `IP_ID` 可读即证明 4 KiB 窗口已在运行。

## 3. 只读预检结果

| 项 | 值 |
|---|---|
| IP_ID | `0x434F5030`（COP0） |
| STATUS 稳定值 | `0x1`（READY=!BUSY；无 ACCEPTED/UNCONSUMED/DONE/ERROR/TIMEOUT/BUSY） |
| STATUS 首读异常 | 每组新命令的**第一次**读偶发 `0x0`（READY=0 且 BUSY=0，不符合 A1），随后恢复 `0x1`；见 [preflight-3x.txt](logs/preflight-3x.txt)、[preflight-5x.txt](logs/preflight-5x.txt) |
| ERROR_CODE | `0` |
| RESULT_SEQ | `0` |
| UNCONSUMED | `0`（多次重复读均为 0） |
| FCLK0 / FCLK1 | **100 MHz / 142.857 MHz**（[fclk.txt](logs/fclk.txt)）；设计门禁要求 100/40 |
| XADC 温度 | 烧写前 raw 2726/2729 → 62.4–62.8 °C；本次 boot 后 raw 2654–2656 → 53.5–53.8 °C |
| 连续次数 | 9 次只读尝试：1 次挂起（复位前）+ 8 次稳定预检读；**无推理轮** |
| pattern/zero class/margin/score/logits | **NOT RUN**（无 payload/ROI loader） |
| 与 EXPECTED 一致 | **NOT RUN** |

原始串口：[first-probe-raw.txt](logs/first-probe-raw.txt)（挂起，无返回）、
[probe-after-reprogram.txt](logs/probe-after-reprogram.txt)、
[preflight-3x.txt](logs/preflight-3x.txt)、[preflight-5x.txt](logs/preflight-5x.txt)、
[postboot-status.txt](logs/postboot-status.txt)。

## 4. 阻塞项（需 JL/NC 处理）

1. **FCLK1 不是 40 MHz（最关键）**：板卡现有 boot FSBL/base overlay 把 FCLK1 配成
   142.857 MHz；JTAG 烧 `pynq_cop_40mhz.bit` 只配置 PL，不应用 bitstream 内的 PS7
   时钟/复位配置。当前 cop 逻辑运行在 142.857 MHz，不能代表 `VIVADO=PASS_40MHZ` 的
   板级结果。需要 JL/NC 提供
   - 与本设计匹配的 `boot.bin`/FSBL（FCLK0=100、FCLK1=40），或
   - 经确认的 FCLK1=40 设置流程；设置后应重新烧写/复位并复测。
2. **没有 payload/ROI loader**：包内有 `payload/provisional-model/{payload.bin,manifest.json,...}`
   和 golden，但没有 PS 侧 DMA/GPIO 装载脚本；WC 的 `PynqDmaPlane` 仍是
   `NotImplementedError`。需要 J08 loader 或等效工具，否则只能做只读预检。
3. **STATUS 首读 0x0**：每组新命令第一次读为 0、后续为 1；在 FCLK 修正前不排除
   首访问/CDC/超频瞬态。修正 40 MHz 后需重测；若仍出现，按 A1 违规上报。
4. 固件仍是单作业 `main`，预启动判定（count 0/>16/>10）无完成通知；本轮未进入
   提交/消费路径，未触发。

## 5. 能证明 / 不能证明

**能证明**

- 交接包完整（tar/106/bit/hwh/VERSION 全对）；
- 位流能通过 JTAG 配置，PS 能通过 `0x40000000` 读到 `COP0`；
- 当前空闲终态干净：`ERROR_CODE=0`、`RESULT_SEQ=0`、无 UNCONSUMED。

**不能证明**

- 40 MHz 板级时序/功能（当前实际 142.857 MHz）；
- payload/ROI 装载、ACCEPTED/终态/结果读回、CONSUME；
- pattern/zero 的 class/margin/score/logits 与预期一致；
- 温度/连续推理稳定性、现场稳定性、NC 板级验收。

## 6. 下一步

1. JL/NC 给匹配的 PS7 启动配置（FCLK1=40）或确认可安全修改时钟的流程；
2. JL/J08 给 payload/ROI loader（或确认由 WC 按 `.hwh` DMA/GPIO 实现）；
3. 重新烧写 → 复位 → 在 40 MHz 下复跑只读预检（STATUS 应稳定 `0x1`）；
4. loader 到位后提交/ACCEPTED/唯一终态/读结果/落盘后 CONSUME，对照
   `EXPECTED_OUTPUTS.tsv`，记录温度/连续次数/首错。

## 7. 边界

- 本记录是 **板卡已响应 + 只读预检**，不是 40 MHz 通过，也不是推理验收。
- PROVISIONAL 诊断模型不是发布模型；`score_q15` 不是概率。
- 未修改包内 RTL/位流；未把 `BOARD=UNVERIFIED` 改成 PASS。
