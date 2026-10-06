# [2026-10-06] 协作记录：id_ex_stage 模块——B 分支目标独立加法（旁路通用立即数 mux）

> 标签：#riscv #流水线 #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/id_ex_stage.v`）随本轮 PC/flush 降深度同批提交

## 1. 任务与初始提示词

分支目标地址路径过深：原本经“通用立即数选择 + JALR/imm mux”得到 `redirect_target`，再在上层 `redirect_target + 4`。要求为 **B 型分支**提供**专用立即数旁路 + 独立 PC 加法**，缩短 `instr → 目标 → pc_reg` 路径，并**保持语义不变**（负偏移、bit1、32 位回绕）。

## 2. 模型第一版方案

```verilog
wire [31:0] branch_imm = {{19{instr[31]}}, instr[31], instr[7],
                          instr[30:25], instr[11:8], 1'b0};
assign branch_target      = in_pc + branch_imm;             // 直接拼接 B 立即数
assign branch_target_next = in_pc + (branch_imm + 32'd4);   // 独立 PC 加法
```

新增输出 `branch_target`、`branch_target_next` 供 `core_top` 的预测/恢复使用；`redirect_target`（JALR/通用）保持原样。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；**未决**：新增加法器会增加 LUT，收益与代价须以 Vivado 确认。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 从已选 `redirect_target` 再加 4，链路深 | 用独立 PC 加法算“下一个 PC” | `branch_target_next = in_pc + (branch_imm+4)` | ✅ ID+EX **12304 例 PASS** |
| 2 | 负偏移 / bit1 / 回绕不能错 | 完整 32 位运算 | 保留全宽加法 | ✅ B 偏移全覆盖 |

## 5. 最终结论

B 分支目标由**专用立即数旁路**直接生成，`branch_target = in_pc + branch_imm`，后继地址用独立加法 `in_pc + (branch_imm+4)`，不再从 `redirect_target` 二次相加；语义等价（12304 例）。**时序收益与新增 LUT 待 Vivado 复测。**

## 6. 经验沉淀

- 关键分支目标用**专用立即数旁路**，避免绕通用 `imm`/`JALR` mux；
- “下一个 PC”应**独立加法**（`in_pc + (imm+4)`），而不是在已选目标上再 `+4`（避免叠加选择链）；
- 完整 32 位运算，保留负偏移/bit1/回绕。 #skill候选
