# [2026-10-06] 协作记录：id_ex_stage 模块——输出 branch_valid（供 BHT 判定）

> 标签：#riscv #流水线 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/id_ex_stage.v`）随 Part C 同批提交

## 1. 任务与初始提示词

BHT 需要区分两件事：**当前是不是分支指令**（用于 lookup/命中统计）与**分支方向是否 taken**（用于预测比对/更新）。因此 `id_ex_stage` 增出 `branch_valid`。

## 2. 模型第一版方案

```verilog
assign branch_valid = (branch_type != 3'd0);
assign branch_taken = branch_valid && cond_taken;
```

`branch_valid` 供 `core_top` 的 `branch_resolve = ex_accept && branch_valid` 与 BHT lookup 使用；`branch_taken` 语义不变（仍是“是分支且条件成立”）。

## 3. 失败现象（真实偏差与未决项，如实记录）

无功能失败；`tb_id_ex_stage` 16 用例 PASS。无未决 RTL 项（时序由验证线统一复测）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 预测需要“是分支”与“方向”两个独立信号 | 原只有 `branch_taken` 合成量 | 增出 `branch_valid`，`branch_taken=branch_valid&&cond_taken` | ✅ id_ex 16 用例 PASS；整核四档一致 |

## 5. 最终结论

`id_ex_stage` 现在同时输出 `branch_valid`（是否分支）与 `branch_taken`（是否 taken），语义与 `cond_taken` 组合正确；支撑 BHT 的 lookup 与命中统计。

## 6. 经验沉淀

- 预测类逻辑需要**“是否为分支”与“分支方向”两个独立信号**；把二者合成一个会在预测/统计处被迫反推，易错。
- #skill候选
