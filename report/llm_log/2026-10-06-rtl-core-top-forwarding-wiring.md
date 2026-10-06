# [2026-10-06] 协作记录：core_top 模块——转发来源接线简化（降 mux 深度 / Fmax）

> 标签：#riscv #流水线 #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `85b94a5`；本模块改动（`src/riscv/core_top.v` + `tb_core_v1_hazard.v`）与本文档同批提交

## 1. 任务与初始提示词

配合 id_ex_stage 的降深度，继续缩短 v1 核的关键路径——把 `forwarding` 实例的候选来源按**物理三级结构**裁剪，减小旁路 mux 的组合深度，同时**不放宽任何真实 RAW 语义**。

## 2. 模型第一版方案

`core_top` 中 `forwarding` 实例的接线由“EX/MEM/WB 三源并列”改为：

```verilog
.ex_valid(mem_valid && !mem_mem_read), .ex_we(mem_reg_write), .ex_ready(1'b1),
.ex_rd(mem_rd), .ex_data(mem_result),
.mem_valid(1'b0), .mem_we(1'b0), .mem_ready(1'b0), .mem_rd(5'd0), .mem_data(32'd0),
.wb_valid(1'b0),  .wb_we(1'b0),  .wb_rd(5'd0),      .wb_data(32'd0),
```

即：**唯一的在途生产者**由 ID+EX 的较老槽结果（`mem_result`）提供；load-use 由 1 拍停顿处理（停顿时消费者回退读 regfile），因此不再并列接入 MEM/WB 旁路源。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **必须证明裁剪不会漏掉真实 RAW**：load-use 场景下停顿时**不能**走转发；普通 ALU RAW 必须走旁路零停顿。为此在整核 tb 增加断言（见 §4）。
2. **未决**：核 OOC 频率提升待验证线 Vivado 复测；SoC 40/125 MHz 本轮未跑；本 RTL 侧不宣称 WNS。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 转发 mux 候选过多、路径深 | 三级结构下唯一在途生产者只需 EX 源 | mem/wb 源置 0，ex 源取 `mem_result` | ✅ `v1_hazard_fwd/nofwd` PASS |
| 2 | load-use 不能走转发 | 停顿时 `rs1_sel` 必须为 RF(00) | `tb_core_v1_hazard` 增 `load_rf_checks` 断言 | ✅ PASS（`load data did not enter forwarding mux`） |
| 3 | ALU RAW 必须旁路零停顿 | 命中时 `rs1_sel/rs2_sel==2'b11` 且无停顿 | tb 增 `alu_bypass_checks` 断言 | ✅ PASS |

## 5. 最终结论

`core_top` 转发接线简化为单一 EX 源 + load-use 停顿；整核 tb 新增“停顿时不走转发、ALU RAW 走旁路”双断言，`v1_hazard_fwd/nofwd` 与全量 `run_iverilog.sh all` 均 PASS（仅视觉门禁的 2 个预期 `injected` FAIL）。**核 OOC 频率提升待验证线 Vivado 复测**。

## 6. 经验沉淀

- 转发候选应按**物理流水结构**裁剪，不能照搬逻辑三源；三级 + load-use 停顿下，唯一在途生产者可只留一个源。
- 用整核 tb 断言把语义锁死：「停顿时 `sel=RF`（不走转发）」「ALU RAW `sel=EX`（旁路零停顿）」。
- 同 id_ex 记录：Fmax 改动一律标注“待 Vivado 验证”。 #skill候选
