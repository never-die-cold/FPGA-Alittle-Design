# [2026-10-25] 协作记录：DMA 长度位宽 14→16 与固件驻留等待

> 标签：#coprocessor #DMA #riscv_fw #上板返工 #门禁
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`b78bf80` `a9b68d9` `f69a575`

## 1. 任务与初始提示词

上板返工第 1 轮：解决两个已复现阻塞——① AXI DMA `C_SG_LENGTH_WIDTH=14`，单包上限
16,383 B，装不下 36,032 B payload，且不能分包（每笔 DMA 都会产生 TLAST）；
② 一次性 `cop_job` 在 PS 配置前退出。要求把 BD 固定为 16 位 Direct MM2S、loader 只接受
16 位 HWH，并让固件驻留等待 CFG/MODEL/ROI；新源码必须重走整机门禁后才可出包。

## 2. 模型第一版方案

`create_pynq_cop_bd.tcl` 固定 `c_sg_length_width=16`，保持 SG=0、MM2S=1、stream=64-bit；
loader 校验 HWH 精确 16 位，按 `MM2S_LENGTH[15:0]` 写长度，14 位 HWH 与 65,536 B 负例在
MMIO 前拒绝。`cop_job` 驻留等待 `CFG_VALID`（`CFG_APPLIED==CFG_SEQ`）与
`DMA_BYTES==ROI_COUNT*4096`，区分 ROI 完成与前一笔权重完成；BUSY/UNCONSUMED 仍立即拒绝，
START 仍只由固件发起。

## 3. 失败现象

1. 14 位 HWH 下 36,032 B 超过 16,383 B；分包会造成多笔 TLAST，不能作为绕过。
2. 一次性固件在 PS 配置完成前退出，loader 收到 `NO_ACK`；这是 fail-closed，不是硬件坏。
3. 新 RTL/固件尚未在 Windows Vivado 重跑，旧门禁数字不能外推到新 bit。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 36,032 B 被 14 位拒绝 | 单包长度不足 | BD 固定 16 位，loader 只接受 16 位 | `payload_loader` PASS |
| 2 | 分包会多 TLAST | 不能破坏流语义 | 明确禁止分包，65,536 B 负例拒绝 | 负例 PASS |
| 3 | PS 配置晚于 CPU 上电 | 固件需驻留 | 等待 CFG/MODEL/ROI + DMA_BYTES 匹配 | `firmware_e2e` PASS |
| 4 | 新源码未进门禁 | 旧数字不可复用 | 标 UNVERIFIED，等 Windows 重跑 | 检查点记录 |

## 5. 最终结论

```text
PASS: payload_loader requires 16-bit/65535-byte Direct MM2S length; 14-bit HWH rejects before MMIO
      and 36032-byte payload preflight passes at 16-bit
PASS: firmware_e2e waits for delayed CFG/model/ROI then CPU START/ACCEPTED/DONE/RESULT_SEQ/FW + PS CONSUME;
      J02 zero=2/2/258/1
```

`all` 与 `bram_network` 均退出 0（pattern/zero 各 73,795 元素；BRAM cycles=472594），
`EXPECTED_OUTPUTS.tsv` 保持 `0/0/0` 与 `2/2/258`。新 bit/hwh/xsa、WNS/DSP/BRAM/CDC/DRC
需 Windows 重跑，当前 **UNVERIFIED**；旧包 `d66916c49b80` 是 DMA-14/一次性固件包，不可用。

## 6. 经验沉淀

- 触发条件：DMA 单包长度小于模型 payload，或 CPU 固件先于 PS 配置启动。
- 排查步骤：先看 HWH 的 DMA 位宽与单包上限；禁止用分包绕 TLAST；固件必须驻留并等待
  配置/模型/ROI 的有效回执；换 BD 后必须重走整机门禁，旧 bit 哈希全部作废。
- 适用范围：所有 PS+PL 运行时装载模型；换 DMA IP 或长度位宽需重核 HWH。
#skill候选
