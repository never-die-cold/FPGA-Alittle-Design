# 2026-10-08 协作记录：断联中手动轮残包误记录（理解题推演发现）与记录资格时间点

> 标签：#vision #bug修复 #skill候选
> 平台：ZCode ｜ 模型：GLM-5.3-Flash
> 相关 commit：dev/exe 本批（rounds.py 采纳点语义 + test_vision_rounds 定向断言）

## 1. 任务与初始提示词

用户在理解门槛第 3 题（"为什么记录要同时要求手动触发+当前有效"）答不出，要求 agent 讲解。
agent 在推演该问题时发现：当前实现把"该轮是手动触发"的标记写在**发动请求那一刻**
（`last_round_manual = manual` 在 try 之前），存在一个未被任何测试覆盖的漏洞。

## 2. 模型第一版方案（有漏洞）

```python
self.last_trigger = now
manual = self.manual_pending
self.manual_pending = False
self.last_round_manual = manual   # ← 发动点就标记
try: packet = POST /v1/check ...
except: fails += 1; return          # ← 失败时标记已被污染
...
self.packet = packet
```
记录判定 = `current and last_round_manual and accept(packet)`。

## 3. 失败现象（推演复现，未等到实机）

场景：自动轮询已采纳报文 P（零件在位置 A）→ 操作员挪动零件、按 c 触发新检查 →
恰在此时板卡断联 → c 触发的请求失败 → **P 仍在 1s 年龄窗内**（D3 单次失败不立即撤框）、
屏幕上仍显示 P 的框 → `last_round_manual=True`（污染）→ EXE 把**挪动前的旧结果 P**
写成一条批次档案。批次记录是永久留档、可能作为验收证据——写入"我们自己都没拿到新结果"
的旧数据，正是 plan.md §1.3 红线要防的事。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 理解题 3 的推演（用户答"不知道"触发讲解） | 记录资格的"手动"标记写在了发动点而非采纳点；失败轮会留下污染的标记 | `last_round_manual = manual` 移到报文被采纳之后（session 校验通过、`self.packet = packet` 处） | ✅ test_vision_rounds 断联段新增定向断言：断联中手动触发→失败轮→`not last_round_manual` |

## 5. 最终结论

记录资格时间点语义 = **采纳点**：只有"这一次手动轮真的换来了新报文"才具备批次记录资格；
残留旧报文即使仍在显示窗口内，也不冒充"这次检查"的结果。
回归 7/7 + 打包 E2E（--trigger-frame 手动记录恰好一条）PASS；证据 `data/logs/2026-10-08-exe-anomalies/`。

## 6. 经验沉淀

#skill候选
- 触发条件：给"动作"打标记（手动/自动、来源、资格）时，标记写在动作的**发动点**还是**完成点**
  有语义差别；恢复/失败路径会把发动点标记留在错误状态上。
- 排查步骤：对每个"标记+可能失败的后续动作"组合问一句——"动作失败后，这个标记还成立吗？"；
  资格类标记一律放在**结果被确认采纳**之后。
- 适用范围：换题换板成立（请求重试、事务标记、回执状态的通用不变量）。
