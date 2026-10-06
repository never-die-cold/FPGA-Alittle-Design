# [2026-10-06] 协作记录：id_ex_stage 模块——分支比较与 ALU 解耦（降深度 / Fmax）

> 标签：#riscv #流水线 #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `85b94a5`；本模块改动（`src/riscv/id_ex_stage.v` + `tb_id_ex_stage.v`）与本文档同批提交

## 1. 任务与初始提示词

验证线报告：v1 核 OOC 约 **80/81 MHz**，低于 v0 基线 **86.8 MHz**，核 OOC 最差路径集中在 **IF/ID 保持 + 分支/跳转 → PC**。要求**缩短分支相关组合路径、但不改语义**。本轮目标：让分支条件**不再借道 ALU 标志**。

## 2. 模型第一版方案

`id_ex_stage` 内新增独立比较器，分支条件直接由源操作数计算：

```verilog
wire branch_eq  = (rs1_value == rs2_value);
wire branch_lt  = ($signed(rs1_value) < $signed(rs2_value));
wire branch_ltu = (rs1_value < rs2_value);
wire cond_taken = (branch_type==3'd1)? branch_eq : (branch_type==3'd2)? ~branch_eq :
                  (branch_type==3'd3)? branch_lt : (branch_type==3'd4)? ~branch_lt :
                  (branch_type==3'd5)? branch_ltu : (branch_type==3'd6)? ~branch_ltu : 1'b0;
```

ALU 只保留 `alu_y`（`zero/lt/ltu` 输出置空），分支裁决不再串在 ALU 结果之后。`branch_taken/jump_taken/redirect_target/ex_result` 逻辑不变。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 语义需与“借道 ALU 标志”完全等价，尤其 **有符号/无符号比较**（`blt/bge vs bltu/bgeu`）——已用定向用例覆盖。
2. **未决**：核 OOC 频率提升必须由**验证线 Vivado 复测**确认；SoC（40/125 MHz）本轮未跑。本 RTL 侧**不宣称任何 WNS**。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 分支条件依赖 ALU 标志，路径深 | 可用独立比较器直接算条件，等价且更浅 | 新增 `eq/lt/ltu` 比较器，ALU 只出 `alu_y` | ✅ `tb_id_ex_stage` 16 用例 PASS |
| 2 | 有/无符号边界 | `$signed` 与无符号比较需分别正确 | 补 beq/bne/blt/bge/bltu/bgeu 定向用例 | ✅ PASS |
| 3 | 不能改语义 | 直接比较与 ALU 标志等价 | 无对外行为变化 | ✅ `v1_fwd/v1_nofwd` 气泡与结果不变；全量回归 PASS |

## 5. 最终结论

`id_ex_stage` 分支比较与 ALU 解耦：ALU 只算 `alu_y`，`cond_taken` 用直接比较器，缩短“指令→译码→ALU 标志→分支→PC”链。功能等价（16 用例 + 双档 + 整核回归 PASS）；旁证：`bench_v0_1` 转发档周期由 3447→**2423**（分支相关停顿减少）。**核 OOC 频率提升待验证线 Vivado 复测**；SoC 未跑。

## 6. 经验沉淀

- 分支条件**不必借道 ALU 标志**：直接用独立比较器比较 `rs1/rs2`，语义等价且能缩短关键路径。
- 有符号/无符号比较必须分别覆盖 `blt/bge` 与 `bltu/bgeu` 边界。
- Fmax 类改动一律标注“待 Vivado 验证”，**不能把仿真 PASS 当成时序提升**。 #skill候选
