# [2026-09-22] 协作记录：Part A 第 7B 步——muldiv 接入两级流水核，RV32IM 整核首次跑通

> 标签：#riscv #架构决策 #验证 #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `726d4e5`（7A）；本记录与 7B 代码同批提交（哈希回填）

## 1. 任务与初始提示词

承接第 7A 步（`decode.v` 译码），进入第 7B 步核内接入：

> 在 `core_top.v` 例化 `muldiv`，接入 `start/busy/done`、PC/IF 停顿和单次写回。……

本轮还首次执行了新落库的 `AGENTS.md` 开工三件事（读开工清单、核实现状三类清单、声明范围），并据此把测试落在仓库内、接入一键回归（不再用 `/tmp`）。

## 2. 模型第一版方案

- **`src/riscv/core_top.v`**：例化 `muldiv`；接通 3 位 `muldiv_op` 与 `muldiv_valid`；用 `muldiv_pending` 防止同一条指令重复启动；`stall = muldiv_valid && !muldiv_done`；`rf_we = reg_write && (!muldiv_valid || muldiv_done)`；`wb_sel=2'b11` 选择 `muldiv_result`。
- **新增 `sim/riscv/tb_core_muldiv.v`**：预载真实 `hello.hex`，整核执行 `divu/remu/mul`，检查 `tohost=142879`、`tohost_exit=0`。
- **`sim/scripts/run_iverilog.sh`**：新增 `rv32im` 模式并纳入 `all` 全量回归。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **全目录 Verilator lint 被既有警告拦住**：`soc_top.led` 未驱动（尚未完成的 SoC 外壳，非本步引入）；改为对 `core_top` 层次单独 lint（通过）。
2. **写使能布尔式理解偏差**：我一度认为寄存器堆总写使能 = `reg_write && muldiv_valid && done`；Codex 指出这样普通 `add/lw/jal` 在 `done=0` 时会失去写回，补测后纠正为 `reg_write && (!muldiv_valid || done)`。
3. **存储容量契约冲突（8A 前置发现）**：`design_v0.md` 写 IMEM `4096×32`、DMEM `4K×32`，`plan.md` 写“DMEM 4KB→32KB”，而现有 tb 实际用 `4096×32`——三处不一致，必须先冻结契约才能改存储器。
4. **未决项**：Vivado/XSim 未运行；`soc_top` 未完成，不得声称已上板；RV32M arch-test 尚未接入。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 能否只用 `muldiv_busy` 控 `stall` | `busy` 是寄存器，启动拍尚未拉高，PC/IF 会提前推进 | `stall = muldiv_valid && !muldiv_done` | ✅ 启动拍即冻结 |
| 2 | 有 `busy` 为何还要 `muldiv_pending` | 完成拍 `busy=0` 但 M 指令仍在执行级，会重复发 `start` | 粘滞 `pending`，`done` 清除 | ✅ 不再重复启动 |
| 3 | 总写使能写成 `reg_write && muldiv_valid && done` | 普通指令 `done=0` 会失去写回 | `rf_we = reg_write && (!muldiv_valid || done)` | ✅ 补测通过 |
| 4 | 完成拍 `wb_data` 误选 `alu_y` | `mul x5,7,3` 会写 10 而非 21 | `wb_sel=2'b11` 选 `muldiv_result` | ✅ 补测通过 |

## 5. 最终结论

第 7B 步完成：`muldiv` 已接入两级流水核，**RV32IM 固件首次在 `core_top` 上跑通**。验证：`bash sim/scripts/run_iverilog.sh rv32im` → `PASS: RV32IM core tohost=142879 exit=0`；`all` 全量回归（RV32I 冒烟 / 38 项自检 / 转发气泡 / RV32M 模块 / RV32IM 整核）全 PASS；`core_top` 层次 Verilator lint 通过；`git diff --check` 通过。状态：✅ RV32M 单元、模块测试、译码、整核接入完成且可复现；🟡 Vivado 综合/XSim 未跑；⬜ `soc_top` 未完成、arch-test 未接、未上板。

## 6. 经验沉淀

- 触发条件：把“多拍功能单元”接入“组合译码 + 单拍写回”的流水核。
- 排查步骤：
  1. 停顿用**组合的 valid**（`valid && !done`）而不是寄存器 `busy`，覆盖住 `start` 已发、`busy` 未置的启动拍；
  2. 用 `pending` 粘滞标志防止完成拍重复启动；
  3. 寄存器堆总写使能 `reg_write && (!muldiv_valid || done)`——兼顾普通指令与 M 指令单次写回；
  4. `wb_data` 必须按 `wb_sel` 选对来源，写使能对 ≠ 写数据对；
  5. 文档契约（容量/地址/时序）不一致时先停下冻结，再动 RTL。
- 适用范围：换模块 / 换板卡 / 换工具链均成立；“valid 而非 busy 控停顿 + pending 防重启 + done 门控写回”可作通用接入范式。 #skill候选
