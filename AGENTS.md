# AGENTS.md —— 每次开工前必读（硬性）

> 适用：本仓库所有分支，RTL 线（`dev/rtl`）优先。
> 目的：杜绝三类事故——① 用临时文件验证、结论不可复现；② 跨目录越界后卡住等授权；
> ③ 凭记忆把「未实现 / 未接入」说成「已完成」。
> **未完成下面「开工三件事」，不得开始任何编码或改动。**

## 一、开工三件事（缺一不可）

1. **读开工清单**：完整阅读 `docs/workflow.md`，逐项执行其中的「必做」项。
2. **核实现状**：先跑 `git rev-parse --abbrev-ref HEAD`、`git log --oneline -5`、`git status`；
   再对照 `src/riscv/design_v0.md`（接口唯一权威）与 `src/riscv/plan.md`，
   在开工回复开头贴出一份三类清单：
   - ✅ 已实现并验证
   - 🟡 已实现但未验证
   - ⬜ 未实现 / 未接入核
3. **声明本次范围**：一句话说明本次要改哪些文件、验证方式、预估行数。

## 二、硬红线

### 1. 目录边界（预先授权，不必每次再问）
- 默认只改 `src/riscv/`。
- 以下跨目录改动**直接执行、无需停下征得同意**，但必须在本步汇报里列明：
  `sim/riscv/`、`sim/scripts/`、`sim/arch_test/`、`data/logs/`、`data/evidence/`、
  `report/llm_log/`、`src/riscv/design_v0.md`、`src/riscv/plan.md`、`docs/`。
- 超出上述范围 → 先说明再改，不要默默动手。

### 2. 可复现性（最关键）
- **禁止**用 `/tmp` 或工作区外的临时文件作为验证依据——会被清理、不可复现。
- 任何「已验证」的结论，必须能由**仓库内的 tb + 脚本入口一键复现**。
- 涉及 RTL 的每一步：写/改 testbench → 接入 `sim/scripts/run_iverilog.sh` 回归 → 跑出 PASS 证据。
- 不允许声称「已验证」却拿不出可复现的 tb。

### 3. 交付纪律
- 遵循**古法编程**（`skill/gufa-programming/SKILL.md`）：单步 ≤100 行、先设计后写码、
  每步出 2–3 道理解题并**等用户回答**。
- 每步结束固定汇报：① 改了哪些文件；② 验证命令与原始结果；③ `git diff --check`；
  ④ 待办 / 未接入清单（明确标注「未实现」）。
- 未经用户确认理解，**不得 `git commit`**（见 `skill/understand-gate/SKILL.md`）。

## 三、参考入口

- 详细清单：`docs/workflow.md`
- 计划与验收：`src/riscv/plan.md` §3.2 / §4.1
- 接口契约：`src/riscv/design_v0.md`
- 工作流技能：`skill/gufa-programming/SKILL.md`、`skill/understand-gate/SKILL.md`
