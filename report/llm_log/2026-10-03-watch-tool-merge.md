# 板端监视工具合一：watch_video → onboard_smoke.py watch

日期：2026-10-03。分支 codex/vision-offboard。AI 产出（ZCode/GLM）。

## 决策

两套板端监视工具并存（onboard_smoke.py watch = commit 确认号口径判据工具；
watch_video.py = 轻量在位监视）由用户拍板：**保留 onboard_smoke.py watch** 作为
判据/存证工具，把 watch_video 的两个优点（flush、BUSY 区分）并入后删除之。

## 改动

1. watch 子命令新增 BUSY 状态：TimeoutError→STALL（帧首未确认）、RuntimeError→BUSY
   （在途提交被拒，非断流，`saw_busy` 单独计数）；判定逻辑（saw_stream/end_stream）不变。
2. `except Exception` 收窄为上述两类：MMIO 类硬故障不再伪装成 STALL，
   直接抛到 FAIL(W)（10/03 PS 总线挂死教训：软件分类不能掩盖总线级故障）。
3. watch 路径 print 全部 flush=True：stdout 重定向文件时块缓冲导致事件行不实时落盘
   （watch.log/watch2.log 因挂死后页缓存未刷盘而无数据的教训）。
4. `watch_video.py` 删除；ONBOARD.md / src/pynq_host/README.md / make_board_pkg.sh /
   data/logs/2026-10-03-vision-onboard/README.md 引用同步（历史日志记录行不改）。

## 理解门槛三题（用户作答，全过）

1. BUSY 折进 saw_stall 是否算错——不算：saw_stall 语义是「本轮未帧首确认」，
   BUSY 轮确未确认；真断流与 busy 的区分靠 saw_busy 字段 + 事件行顺序。
   **用户同时抓出实现 bug**：`last` 由 bool 改状态字符串后 `not last` 恒假，
   收尾停在 STALL/BUSY 也 PASS，FAIL 分支成死代码。已修为 `last != "STREAM"`。
2. 收窄异常为什么对——只把预期超时记 STALL、预期忙拒绝记 BUSY；PS 总线挂死
   本身不会变成可捕获的 Python 异常，收窄的价值是不掩盖可见的 MMIO 硬故障。
3. flush 为什么实质——终端行缓冲 vs 重定向块缓冲；无 flush 时挂住/强杀丢缓冲；
   flush 只交到 OS，冻结/断电仍可能丢页缓存（watch.log/watch2.log 即证）。
   用户并核实 watch6.log 仅一行、取回方式无文档记载，不作断言。

## 验证证据

```
$ python onboard_smoke.py watch-mock
EVENT(0.0s): STREAM / EVENT(3.0s): STALL / EVENT(3.5s): BUSY / EVENT(4.1s): STREAM
WATCH-SUMMARY: saw_stream=True saw_stall=True saw_busy=True end_stream=STREAM
PASS(W): 观测 6s 完成（断流后已恢复）  exit=0

$ python -（注入前 1s 在流、此后不恢复的假后端）
EVENT(0.0s): STREAM / EVENT(2.0s): STALL
WATCH-SUMMARY: ... end_stream=STALL
EXPECTED FAIL: 观测到断流/busy 未恢复（end=STALL）   ← 修复前此分支不可达

$ git diff --check   （干净）
```

## 遗留

- BUSY/FAIL 分支的真机覆盖待下次上板（断连重连复测时顺带）。
- 附带发现（交 RTL 线）：`src/riscv/id_ex_stage.v:20` `decode u_decode (.*);`
  为 SystemVerilog 隐式端口连接，Vivado 默认模式 Synth 8-2716 报错，
  Part B 门禁综合需 `read_verilog -sv` 或展开显式端口。
