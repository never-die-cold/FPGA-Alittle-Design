# [2026-09-20] 协作记录：Part A 古法编程起步——RV32M 接口契约 + sb/sh 写数据对齐 + IF 停顿保持

> 标签：#riscv #架构决策 #bug修复 #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`dd42cd2`（分支起点）之后的 Part A 第 1–3 步改动（`design_v0.md` / `core_top.v` / `if_stage.v`）＋本文档同批入库，哈希待提交后回填

## 1. 任务与初始提示词

以「古法编程」为基本流程，完成 `plan.md` 技术路线 Part A（两级流水基线核 v0）。我在项目里是 **RTL 线主责（逻辑开发主力）**，目录边界 `src/riscv/`，目标分支 `dev/rtl`：

> 按古法编程完成技术路线 Part A —— 两级流水基线核 v0（RTL 线）……先读 `skill/gufa-programming/SKILL.md`、`skill/understand-gate/SKILL.md`、`src/riscv/plan.md`、`src/riscv/design_v0.md` 与现有 RTL……生成的可综合 RTL 一律放 `src/riscv/`，不要改其他线的目录……单步 ≤100 行，每步自检 + 讲解 + 出 2–3 道理解题，我确认通过后才走下一步。

Codex 讲解偏底层后，我又在 OpenCode 里要求「按新手视角重讲」：

> 帮我解释主要设计里面的所有内容，具体信息可以参考 VS Code 里 `FPGA-Alittle-Design` 板块 `plan.md` 二级流水的所有内容……我现在是一名只刷了一点 Verilog 题目的新手，解释不要太深奥了。

## 2. 模型第一版方案

Codex 先做只读盘点，发现若干缺口（`dev/rtl` 落后 main、`muldiv.v`/`soc_top.v` 缺失、2 位 `muldiv_op` 装不下 8 条 RV32M、IF 停顿未保存同步 BRAM 返回的指令、`sb/sh` 写数据未对齐、本机无 Vivado），给出 **13 步拆步清单**（每步均限制在 `src/riscv/`）：

1. `design_v0.md`：M 编码/握手/停顿恢复契约；2 `core_top.v` 字节/半字写数据对齐；3 `if_stage.v` 停顿保存与恢复；4–6 `muldiv.v`（骨架→迭代乘法→迭代除法）；7 `decode.v` M 译码；8 `core_top.v` M 启动/停顿/单次写回；9 `imem.v` 同步指令 BRAM；10 `dmem.v` 异步读/字节写 RAM；11 `soc_top.v` 连接；12 上板时钟封装；13 全量回归 + CPI/Fmax 证据 + 提交总闸。

第 1–3 步已实施：

- **第 1 步 `design_v0.md`**：`muldiv_op` 由 2 位扩为 3 位并直接复用 `funct3`（`000`~`111` 唯一对应 8 条 RV32M）；新增 `muldiv_valid` 区分普通 R 型与 M 指令；乘除单元采用 `start/busy/done` 握手，`done` 为唯一写回拍；`core_top` 用 `muldiv_pending` 粘滞标志防止被暂停的同一条 M 指令重复启动；补除零（商全 1、余数=被除数）与 `INT_MIN/-1`（商 `0x8000_0000`、余 0）两条边界。
- **第 2 步 `core_top.v`**：`dmem_wdata` 按 `mask_sel` 铺数据——`sb`→`{4{rdata2[7:0]}}`、`sh`→`{2{rdata2[15:0]}}`、`sw`→`rdata2`；`dmem_be` 仍按地址选通道。
- **第 3 步 `if_stage.v`**：新增 `instr_hold`/`valid_hold`/`stall_q`，在进入停顿时保存当前指令与有效位，多拍运算期间保持，避免同步指令 BRAM 在停顿后返回的下一条指令覆盖当前 M 指令；正常运行仍直接取 `imem_rdata`，不额外增加流水级。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **用户提示词被截断**：任务消息结尾停在「范围与验收以 `plan.md §4.1` 为」，Codex 未擅自补全，主动停在拆步确认点并请我补充剩余约束。
2. **讲解深度与读者不匹配**：Codex 第 1 步的术语式讲解（`funct3`、握手时序、组合译码）对 Verilog 新手过深，我反馈「太深奥」后转到 OpenCode 用生活类比重讲，才完成理解并作答。这是一次真实的「有代码、缺讲解」协作缺口。
3. **契约层三处隐患在自检中暴露**：2 位 `muldiv_op` 编码不足（`mul`/`mulhu` 等被迫共用码）；IF 停顿只保持 PC 未保持指令；`sb/sh` 写数据未做通道对齐。
4. **无 Vivado 环境**：WSL 侧只有 Icarus / Verilator / RISC-V 工具链，`build/` 的历史 Fmax（86.8 MHz）**不能当成本次实测**；Part A 的基线 CPI / Fmax 仍缺（未验证即不声称）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 2 位 `muldiv_op` 与 8 条 RV32M 冲突 | 4 种编码装不下 8 条指令，`mul`/`mulhu` 等会撞码 | 扩为 3 位 = `funct3`，加 `muldiv_valid`、`start/busy/done`、`muldiv_pending` | ✅ 契约冻结；我 3 道理解题通过（补测后） |
| 2 | `sb/sh` 在非零偏移写错字节 | `be` 选通道正确，但 `dmem_wdata` 未按字节/半字铺数据 | `core_top.v` 依 `mask_sel` 复制低字节/低半字 | ✅ 定向测试（`sb` 偏移 3、`sh` 偏移 2、`sw`）+ 38 用例回归 PASS |
| 3 | IF 多拍停顿期间指令被覆盖 | 同步 BRAM 停顿后仍返回下一条，需显式保存当前指令 | `if_stage.v` 加 `instr_hold`/`valid_hold`/`stall_q` | ✅ 连续停顿定向测试 PASS；程序冒烟 + 38 用例回归 PASS |
| 4 | 「这些解释还是太深奥了」 | 术语密度超出新手读者 | 转 OpenCode 用「门铃/便签/竖式手算」等类比重讲 | ✅ 我能复述并作答（第 1 题一次答对） |

## 5. 最终结论

Part A 按古法编程拆成 13 步，**第 1–3 步完成并通过理解门槛**：RV32M 接口契约冻结（3 位 `funct3` + `muldiv_valid` + `start/busy/done` + `pending` + 两条边界）、`sb/sh` 写数据通道对齐、IF 停顿保存/恢复。验证：`tb_core_smoke` PASS（`tohost=13`、`tohost_exit=0`）、RV32I 38 用例回归 PASS、`sb/sh` 与 IF 停顿定向测试 PASS、`git diff --check` 通过。改动位于 `src/riscv/{design_v0.md,core_top.v,if_stage.v}`，分支 `dev/rtl`；Vivado 未运行，基线 CPI/Fmax 待后续窗口补。后续第 4–13 步继续同流程推进。

## 6. 经验沉淀

- 触发条件：AI 小步交付 RTL 时，团队成员是 Verilog 新手；或 AI 讲解与大块代码同时倾倒。
- 排查步骤：
  1. 契约先冻结再写码：位宽/握手/边界这样「改了要返工」的东西，先写进设计文档并出题确认理解；
  2. 同步 BRAM 的停顿必须显式保存「当前指令」，不能只保持 PC（容易漏的隐藏级）；
  3. 写通路记住分工——`be` 选通道、`dmem_wdata` 摆数据，`sb/sh` 必须把低字节/低半字铺满所有通道；
  4. 讲解过深要换**类比**（门铃、便签、竖式手算），不是降低结论或替用户作答；必要时用另一个模型/工具补讲。
- 适用范围：换模块、换板卡仍成立；「实现用 Codex、补课用 OpenCode」的双工具分工可作为团队通用流程。 #skill候选
