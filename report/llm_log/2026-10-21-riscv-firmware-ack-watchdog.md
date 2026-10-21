# [2026-10-21] 协作记录：固件改用 ACCEPTED 回执看门狗与 UNCONSUMED 拒绝

> 标签：#riscv_fw #coprocessor #固件 #看门狗 #握手
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`8730cc9`

## 1. 任务与初始提示词

按裁决 A/B 修改 `src/riscv_fw/cop_job.c`：删除 START 前清终态与 READY 等待；
终态未清（UNCONSUMED）时新 START 整笔拒绝；用 sticky `ACCEPTED` + 独立软件看门狗判定
`NO_ACK`；轮询 `DONE|ERROR|TIMEOUT` 并支持 `HW_TIMEOUT`；读结果必须校验 `RESULT_SEQ`，
只有“取结果→校验→落盘成功”后才写 CONSUME；ERROR 先读 ERROR_CODE 再消费。

## 2. 模型第一版方案

把提交拆成 `submit → 等 ACCEPTED → 等终态 → 取结果/校验 → 消费` 五段：
`UNCONSUMED` 返回 `STALE_RESULT`；ACCEPTED 超时返回 `NO_ACK`；终态轮询超时返回
`HW_TIMEOUT`；`RESULT_SEQ` 必须大于上一轮已接受值，否则判旧结果；消费写是唯一的清灯点。

## 3. 失败现象

旧固件以 READY 为等待条件，并在 START 前清终态：在 A1/A2 下 READY 可能被错过，
而提前清终态会抹掉尚未消费的证据。固件入口只构建 ELF 并跑主机侧规则测试，
没有在真实 MMIO 硬件上执行整条流程。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 旧流程等 READY | READY 仅建议性、可错过 | 改等 sticky ACCEPTED + 软件超时 | `firmware` PASS |
| 2 | START 前清终态 | 违反消费方 W1C 语义 | UNCONSUMED 时整笔拒绝 START | `firmware` PASS |
| 3 | 未校验序号就取结果 | 旧结果风险 | 读 `RESULT_SEQ` 并要求递增后才接受 | `firmware` PASS |
| 4 | 改动 35 行 | 未超 ≤100 | 单笔提交 `8730cc9` | 已提交 |

## 5. 最终结论

`bash sim/scripts/run_coprocessor_iverilog.sh firmware` PASS：C02 arithmetic goldens 与
工单 PASS/FAIL/RECHECK、低置信、10/16 策略均通过。固件流程与 A/B 在代码和主机侧规则上一致；
真实 MMIO 硬件上的 ACCEPTED/超时/序号行为仍 **UNVERIFIED**。

## 6. 经验沉淀

- 触发条件：固件把“硬件当前忙/闲”当成命令是否被受理的判据。
- 排查步骤：受理用 sticky 回执，等待用软件超时；终态只由消费方清；取结果前先校验序号，
  落盘成功后才清灯，失败保留证据。
- 适用范围：任何 PS 提交、PL 执行、PS 消费的任务模型；换 PCIe/中断同样成立。
#skill候选
