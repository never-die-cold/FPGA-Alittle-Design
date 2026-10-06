# [2026-10-05] 协作记录：muldiv 模块——Radix-4 快速乘法

> 标签：#riscv #RV32M #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`3a6ad00`（本模块改动）；配套性能/分类记录见 `2026-10-05-partB-fast-multiply-options.md`、`2026-10-05-partB-radix4-coremark.md`、`2026-10-05-partB-v1-cycle-breakdown.md`

## 1. 任务与初始提示词

按 `2026-10-05-partB-fast-multiply-options.md` 的拍板，把 `muldiv` 乘法从 Radix-2（32 次迭代）改为 **Radix-4（16 次迭代）**。硬约束：**外部端口、`start/busy/done` 握手、单次写回语义、除法行为不变**，只改内部乘法数据通路。

## 2. 模型第一版方案

- 新增 `product_addend`：按 `multiplier[1:0]` 选择 `0 / 1× / 2× / 3×` 被乘数——`00→0`、`01→multiplicand`、`10→multiplicand<<1`、`11→multiplicand+(multiplicand<<1)`；累加进 `product_acc`。
- 每拍被乘数 `<<2`、乘数 `>>2`（一次吃两位）。
- 完成条件按运算区分：`op_r[2]`（除法）仍 `count==31`；乘法提前到 `count==15`。
- 符号/高半积（`mul/mulh/mulhsu/mulhu`）、除法与端口全部保持不变。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；Radix-4 引入额外倍数选择与更宽加法，**LUT/布线增加、Fmax 风险中等**。
2. **Vivado 未跑**：本机无 Vivado/XSim，Radix-4 的时序（WNS≥0）与资源报告均未验证，不能记“时序验收通过”。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | Radix-4 需覆盖 0/1/2/3 倍被乘数 | 需生成 2× 与 3× | addend mux + `3×=x+(x<<1)` | ✅ 八种 RV32M + 边界定向测试 PASS |
| 2 | 乘法提前 1 拍完成会不会破坏除法 | 除法仍 32 拍，完成拍必须按 op 区分 | 完成条件 `op_r[2] ? count==31 : count==15` | ✅ 除法回归 + RV32IM 整核 PASS |
| 3 | 接口不能变 | 只改内部数据通路 | 外部端口零变化 | ✅ 模块级握手/边界 tb PASS |

## 5. 最终结论

`muldiv` 乘法 Radix-4 落地，外部接口不变。同 CoreMark、同统计窗口、只切转发实测：**Radix-4+fwd `cycles=17,114,141 / retired=10,106,386 / CPI=1.693399`**，**Radix-4+nofwd `19,057,438 / 1.885683`**。相对旧 fwd，固定转发的乘法节省 `4,812,368` 拍（**21.95%**）；Radix-4 工作点转发收益 **10.20%**；相对原始 nofwd 的组合降幅 **28.30%**。数值预测与实测一致；arch-test 3×2 与 `run_iverilog.sh all` 全 PASS（退出码 0）。**Vivado 时序/资源待验。**

## 6. 经验沉淀

- Radix-4 一句话：「每拍吃乘数两位，用 0/1/2/3 倍被乘数查表累加」，`3× = x + (x<<1)`；完成拍按运算类型区分；**只改内部、不动对外握手/端口**。
- 性能收益必须**分类记账**：快速乘法 21.95%、同工作点转发 10.20%、组合 28.30% 三者不得混记。
- 预测与实测一致只证明功能仿真；**未过 Vivado WNS 前的收益都只是仿真结论**。
- #skill候选
