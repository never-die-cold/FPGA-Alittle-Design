# [2026-09-29] 协作记录：Part B R2–R5——v1 三级流水积木模块（转发/冒险/两边界）模块级落地

> 标签：#riscv #流水线 #验证 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `fe80857`（R1 decode 源使用标志）；本轮四个新模块 + 测试 + 回归接入与本文档同批提交

## 1. 任务与初始提示词

按古法编程 + `AGENTS.md`，把 v1 契约里的新模块**逐模块**实现，每步 ≤100 行、模块级 tb 先行并接入 `run_iverilog.sh all`：

> R2 `forwarding` 转发选择器 → R3 `hazard` 冒险/停顿/重定向 → R4 `mem_wb_stage` 边界寄存器 → R5 `id_ex_stage` 组合译码/执行外壳。

## 2. 模型第一版方案

- **`forwarding.v`**：组合式操作数旁路。单个 `select_src` 函数按 §8.2 命中式生成 `{sel,data}`，优先级 `EX>MEM>WB>RF`；`x0` 恒 0；`enable`/`uses_rs*` 门控；输出 `rs1_fwd/rs2_fwd` 与 `rs1_sel/rs2_sel`。
- **`hazard.v`**：组合式 `data_stall / front_stall / ex_accept / redirect / if_flush / mem_in_valid`；`raw_dep = c_valid && p_valid && p_we && p_rd!=0 && (raw_rs1||raw_rs2)`；转发开时只对 load-use 停 1 拍，关时对所有真实 RAW 停到提交；`redirect` 含 `ex_accept` 门控（陈旧分支不 redirect）。
- **`mem_wb_stage.v`**：ID+EX/MEM+WB 边界寄存器，`valid` 门控、气泡可覆盖旧槽、复位清 `valid`。
- **`id_ex_stage.v`**：纯组合译码/执行外壳，例化 `decode`+`alu`，算 `branch_taken/jump_taken/redirect_target`（JALR 清 bit0）、`ex_result`（按 `wb_sel` 选 ALU/PC+4/M）、`ex_store_data` 取转发后的 `rs2`；**无 `clk`，不增加第四级**。
- **`run_iverilog.sh`**：新增 `forwarding/hazard/mem_wb/id_ex` 四个模式并纳入 `all`。
- **验收 tb 归属**：`tb_forwarding.v`/`tb_hazard.v` 由**验证线**按冻结端口表预写（2026-09-29，作为该模块验收门禁）；本轮 rebase 到远端时与之 add/add 冲突，**采用验证线版本**，RTL 线自带的简易 tb 舍弃。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **转发组合环风险**：转发网络不能从消费者自身 ALU 输出反馈到自身输入；R2 用“全状态函数逐候选求值”只匹配较老的 EX/MEM/WB 来源来规避。
2. **未接入顶层**：四个新模块**尚未接入 `core_top`**，因此全量回归的 CPI/性能与 Part A 完全一致（CoreMark 仍 `CPI=2.105`）——这是预期，不能据此声称 v1 已提速或已三级化。
3. **CoreMark 长回归**：约 2100 万周期、跑数分钟，必须等 golden 判据，不能中断。
4. **无 Vivado**：新模块的综合、时序与资源未测。
5. **与验证线验收 tb 撞名**：rebase 时 `tb_forwarding.v`/`tb_hazard.v` 与远端 add/add 冲突；验证线预写的 tb 含契约参考模型与互斥不变量断言（更严），改用它后本线 RTL 已实测通过。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 转发是否会组合环 | 候选来源须全部来自较老指令，不能含自身 ALU 输出 | `select_src` 只匹配 EX/MEM/WB 来源 | ✅ 无组合环；验证线验收 tb `forwarding unit checks (25 cases)` PASS |
| 2 | 伪 RAW / x0 | 一切 RAW 判据以 `uses_rs*` 与 `x0` 门控 | `hazard`/`forwarding` 均加使用位与 x0 门控 | ✅ 验证线验收 tb `hazard unit checks (16020 cases)` PASS |
| 3 | ID+EX 是否变成第四级 | 组合外壳、无 `clk`，经 `mem_wb_stage` 边界提交 | `id_ex_stage` 纯组合 | ✅ 6 用例 PASS |
| 4 | 边界抖动是否覆盖已提交槽 | 边界以 `valid` 为准、气泡可覆盖、复位清 `valid` | `mem_wb_stage` 设计 | ✅ 3 captures PASS |

## 5. 最终结论

本轮新增并模块级验证四个 v1 积木：`forwarding`（验证线验收 tb，25 用例）、`hazard`（验证线验收 tb，含参考模型与互斥不变量，16020 用例）、`mem_wb_stage`(3 captures)、`id_ex_stage`(6) 全部 PASS，并接入 `run_iverilog.sh`。全量回归 PASS：IMEM/DMEM/RV32I/38 项/转发/decode/forwarding/hazard/mem_wb/id_ex/muldiv/RV32IM(`tohost=142879`)/CoreMark(`CPI=2.105`，未变)/benchmark v0.1(`CPI=2.859`)/SoC(`tohost=13,LED=1101`)/soc_check(`tohost=534f4301`)。**待办**：v1 `core_top` 把四个模块接入并与三级边界/停顿/redirect 联调（届时 CPI 才会变化、才有 v1 性能数据）；Vivado 综合/时序；`v1_fwd`/`v1_nofwd` 对照档。

## 6. 经验沉淀

- 触发条件：按已冻结契约逐模块实现流水线积木（转发/冒险/边界）。
- 排查步骤：
  1. 转发候选**只来自较老来源**，绝不从消费者自身 ALU 输出组合反馈，避免组合环；
  2. 一切 RAW 判据以 `uses_rs*` 与 `x0` 门控，防止伪停顿/伪转发；
  3. 边界寄存器以 `valid` 为准：气泡必须能覆盖旧槽、复位清 `valid`，副作用全部由 valid 门控；
  4. **未接入顶层前**，全量回归性能不变是正常的，不能冒充提速；
  5. 每个模块先写模块级 tb 并接入 `all`，再谈集成。
- 适用范围：任何流水线的转发/冒险/边界模块；"单模块 tb + `all` 回归"可复用。 #skill候选
