# [2026-10-24] 协作记录：首次上板只读预检、FCLK 阻塞与 fail-closed payload loader

> 标签：#coprocessor #PYNQ #板级 #loader #时钟
> 平台：Codex + NC（Windows Vivado 2026.1 / PYNQ-Z2）｜ 模型：GPT-5
> 相关 commit：`41ff893` `a5c2612` `d66916c` `d25fc55`

## 1. 任务与初始提示词

拿到 `cop-board-gate-21c4e751bbe8` 包后首次上板：JTAG 烧写、只读预检、记录真实阻塞；
硬件未就绪时不得把“寄存器读通”写成板级验收。要求新增 fail-closed 的 PS payload loader，
校验 manifest/SHA256/CRC32、HWH 地址/位宽与结果字段，并写清 40 MHz 时钟与 boot 顺序。

## 2. 模型第一版方案

先用 JTAG 烧写并只读预检 `IP_ID/STATUS/ERROR_CODE/RESULT_SEQ/XADC`；新增
`tools/cop_payload_loader.py`，在写 MMIO 前完成 manifest、SHA256、CRC32、HWH 地址/位宽、
DMA 单包长度与结果字段校验；新增 `payload_loader` runner 模式与 40 MHz 时钟/BOOT.BIN runbook。

## 3. 失败现象

1. 首次烧写后未复位就读 AXI：命令不返回、串口无响应；用 `xsdb rst -system` 恢复，
   重新 boot 后再烧写才完成预检。
2. 板卡 boot FSBL 给出的 **FCLK1=142.857 MHz**，而设计门禁是 40 MHz；JTAG 不应用
   bitstream 内的 PS7 配置。
3. 包内没有 PS payload/ROI loader；且 DMA `C_SG_LENGTH_WIDTH=14`，单包上限 16,383 B，
   装不下 36,032 B payload；分包会产生额外 TLAST，禁止绕过。
4. 一次性 `cop_job` 可能在 PS 配置前退出，loader 等到 `NO_ACK` 属预期 fail-closed。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 烧写后 AXI 不返回 | 未复位即访问 | `xsdb rst -system` 后重新 boot/烧写 | 只读预检完成 |
| 2 | FCLK1=142.857 MHz | boot FSBL 时钟非门禁档 | 记录 `OPEN-BOARD-CLK-1`，不改 RTL | BOARD_CLOCK UNVERIFIED |
| 3 | 36,032 B > 16,383 B | DMA 单包长度不足 | loader 在 MMIO 前拒绝，禁止分包 | `DMA_LENGTH_BLOCKED` |
| 4 | 一次性固件提前退出 | PS 配置晚于 CPU 上电 | 记录 `OPEN-LOADER-2`，由 JL 改固件 | NO_ACK 为预期 |

## 5. 最终结论

- JTAG 两次 `PROGRAM PASSED`；只读预检通过：`IP_ID=0x434F5030`、`STATUS=0x1`、
  `ERROR_CODE=0`、`RESULT_SEQ=0`、无 UNCONSUMED；XADC 约 53.5–53.8 °C。
- `payload_loader` PASS：manifest/SHA256/CRC/HWH/address/result/clock 门禁生效；
  14 位 DMA 对 36,032 B 在 MMIO 前拒绝。
- 未做 pattern/zero 推理，`BOARD` 与 `BOARD_CLOCK` 均 **UNVERIFIED**；
  阻塞为 FCLK 142.857 MHz、DMA 14 位、一次性固件（OPEN-BOARD-CLK-1 / OPEN-LOADER-1/2）。

## 6. 经验沉淀

- 触发条件：第一次把仿真/门禁产物拿到真实板卡。
- 排查步骤：先复位再访问 AXI；先只读预检再谈推理；把时钟、DMA 长度、固件驻留当作
  独立门禁，任何一项不满足都 fail-closed。
- 适用范围：所有 PYNQ/Zynq 上板；换 boot 镜像或 FCLK 配置需重跑只读预检。
#skill候选
