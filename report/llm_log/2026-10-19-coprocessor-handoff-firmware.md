# [2026-10-19] 协作记录：riscv_fw / docs 模块——J04 固件构建入口、交接清单与验证缺口

> 标签：#coprocessor #riscv_fw #工具链 #文档
> 平台：Codex（VS Code 插件，WSL，夜间）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：发布分支 `64a5c0f`（J04-20）、`5ff7af4`（J04-21）、`7fa977b`（J04-26）、`6a965b0`（J04-27）、`ba785f2`（J04-28）；总记录见 `2026-10-18-j04-closeout.md`

## 1. 任务与初始提示词

把 J04 从“能跑”推进到“**可交接**”：修固件构建入口、对齐状态文档、产出可执行交接清单与验证缺口，并完成 J04 收口（DoD）。

## 2. 模型第一版方案

- **J04-20 `riscv_fw/Makefile`**：新增可覆盖的 `PYTHON ?= python3`，`firmware` 独立模式同时构建 `cop_job.elf` 并跑共用判定主机测试；RV32I ELF/hex/dis 构建成功。
- **J04-21**：仅修正 C03/`design_v1`/README/plan/交接索引里过时的“J04 未实现”文案，不改冻结字段。
- **J04-26**：新增可执行交接清单 `docs/runbooks/coprocessor-j04-handoff.md`（OPEN-1..8、保守默认、影响面、P0/P1/P2 接手步骤）。
- **J04-27/28**：记录队友验证缺口并完成 J04 收口 DoD（模块齐、默认关闭核入口、独立/端到端/J02 zero 冒烟、runner、契约一致性、交接单）。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **首次 hex 构建退出 2**：Makefile 硬编码 `python`，本机只有 `python3` → 改为 `PYTHON ?= python3`。
2. **未决/UNVERIFIED**：完整回归、CDC/AXI 深测、XSim/Vivado/综合实现、bitstream 与上板均未验证；J04 完成不等于这些通过，**不代签**。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | hex 构建退出 2 | 硬编码 `python` | `PYTHON ?= python3` | ✅ `firmware` PASS |
| 2 | 文档写着“J04 未实现” | 状态过时 | 只改状态文案 | ✅ `all` PASS |
| 3 | 交接不可执行 | 缺 OPEN 项/步伐 | `runbooks/coprocessor-j04-handoff.md` | ✅ 链接/字段核对 |

## 5. 最终结论

J04 在 JL 侧收口为“**实现 + 可交接**”：独立 `cop_top` 退出 0、协处理器 `all` 退出 0、J02 zero `9225 packed words/73795 elements` 全匹配（`logits=04fd02 class=2 margin=2 cycles=472593`）、`run_iverilog.sh soc` 退出 0（first=13/1101，second=65/0001）。**硬件与综合验证未做，明确标 UNVERIFIED。**

## 6. 经验沉淀

- 构建脚本的解释器要**可覆盖**（`PYTHON ?= python3`），别硬编码；
- 交接单要列 **OPEN 项 + 保守默认 + 接手步骤**，并显式标注未验证范围；
- “实现完成”与“综合/时序/上板通过”分开记账，**不代签**。 #skill候选
