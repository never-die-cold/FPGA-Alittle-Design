# [2026-10-21] 协作记录：裁决 A/B——READY 降级、ACCEPTED 回执与消费式 W1C

> 标签：#coprocessor #控制面 #契约 #握手 #时序
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`a0d3d99` `3c277e9` `ddaf5a7` `7c99107` `0560608`

## 1. 任务与初始提示词

JL 前置裁决 A/B：READY 降级为 `!BUSY` 的建议性提示，永不作等待条件；命令受理改为 sticky
`ACCEPTED`（W1C）；终态由 PS 侧一笔 `CONSUME` 原子清除 DONE/ERROR/TIMEOUT/RESULT_VALID/
ACCEPTED/ERROR_CODE；终态互斥；`UNCONSUMED` 时新 START 整笔拒绝且零副作用；`RESULT_SEQ`
单调递增，PS 必须校验序号。要求补 T1–T7 独立证据，并让 C03、K1、`design_v1` 三处一致。

## 2. 模型第一版方案

先落契约：C03 新增 §14（A1/A2，保留原文并标注“已由 A1/A2 修订”）、K1 重写握手段、
`design_v1` 新增 §17.5。位号不重排：`CTRL[6]=CONSUME`、`STATUS[11]=ACCEPTED`、
`STATUS[12]=UNCONSUMED`；同拍多事件按 `TIMEOUT > ERROR > DONE` 保证互斥。
RTL：`cop_task_ctrl` 增 `accepted_pulse_o`，`RESULT_SEQ` 只在最后目标提交时 +1 且
SOFT_RESET 不回退；`cop_ctrl_regs` 实现 READY/ACCEPTED/互斥终态/CONSUME/ERROR_CODE；
`cop_top` 接受受理脉冲并开放 PS 的 CONSUME；核侧 gate 用 UNCONSUMED 拒绝 START。

## 3. 失败现象

1. `all` 在 `tb_cop_top.v:134` 按旧断言 FAIL、退出 1：它仍要求 SOFT_RESET 把 `RESULT_SEQ`
   清零，与 A2 的单调递增冲突。
2. 新寄存器语义下 `cop_top` 首跑退出 1：TRACE 显示第一轮已结束（starts=1、busy=0），
   但 TB 卡在后续流程。
3. RTL+TB 合计 112 行，超过单次 commit ≤100 行的纪律。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 旧断言要求软复位清 `RESULT_SEQ` | 与 A2 冲突，不是放宽判据 | 期望改为保留 `seq==1`，保留原 FAIL 记录 | `cop_top` PASS |
| 2 | `cop_top` 首轮后卡住 | TB 写地址遗漏，第二次 START 未发出 | 修 TB 地址，不放宽超时 | `cop_top` PASS |
| 3 | 112 行超过 ≤100 | 提交拆分 | RTL `ddaf5a7`、TB `7c99107` | 两笔均 ≤100 |
| 4 | 只有“大 PASS”不足以证明裁决 | 需要逐条证据 | 每条 `$display("PASS Tn: ...")` + `decision_ab` 入口 | T1–T7 全 PASS |

## 5. 最终结论

三处一致：C03 §14、K1、`design_v1` §17.5。T1–T7 逐条 PASS：

```text
PASS T1: READY pulse may be missed; ACCEPTED still advances submit flow
PASS T2: terminal TIMEOUT does not suppress READY=!BUSY
PASS T3: DONE/ERROR/TIMEOUT remain mutually exclusive
PASS T4: one CONSUME atomically clears terminals/result/receipt/error code
PASS T5: unconsumed START is rejected with zero register side effects
PASS T6: RESULT_SEQ increments and a late reader detects stale sequence
PASS T7: software guard reports NO_ACK when ACCEPTED never arrives
```

`run_coprocessor_iverilog.sh decision_ab` 退出 0；`all` 最终退出 0，`pattern`/`zero`
各 73,795 元素逐元素匹配。仍 UNVERIFIED：完整 CDC/AXI 扫描、物理 bank/结果 DMA、
综合/时序、板级。

## 6. 经验沉淀

- 触发条件：把“建议性状态/脉冲”当成握手条件，或由生产方清消费方尚未取走的终态。
- 排查步骤：先把语义写进契约（增补章节、保留历史），再改 RTL，最后为每条裁决写独立断言；
  旧断言与新语义冲突时改期望、保留失败记录，而不是放宽判据。
- 适用范围：任何生产/消费型 sticky 状态机；换 AXI 中断或 DMA done 同样成立。
#skill候选
