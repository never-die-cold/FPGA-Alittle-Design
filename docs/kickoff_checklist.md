# 开工前必读 / 必做清单（RTL 线）

> 用法：每次开新会话或开始新一步前，AI agent 必须从头过一遍本清单，逐项打勾后才能动手。
> 配套：根目录 `AGENTS.md` 已强制指向本文件；契约以 `src/riscv/design_v0.md` 为准，
> 排期与验收以 `src/riscv/plan.md` 为准。

## 0. 目标板硬约束（PYNQ-Z2，规划内存/接口前必看）

- 主芯片：Xilinx **XC7Z020-1CLG400C**（即 Zynq-7020）。
- 片上资源：BRAM 4.9 Mb ≈ **630 KB**（140 个 36Kb 块）；LUT 53,200 / FF 106,400；DSP 220。
- **512MB DDR3 挂在 PS（ARM）侧，不在 PL 上。** 自研核是纯 PL 软核，默认只能用**片上 BRAM**；
  想用 DDR 必须额外搭 AXI 通路（后续大工程，现阶段不碰）。
- 结论：M1 的 IMEM/DMEM 用片上 BRAM；**32KB×2（约 16 个 36Kb 块，约 11%）在 PYNQ-Z2 上很宽裕**，
  剩余 BRAM 留给模块二（视觉）、模块三（CNN 协处理器）。
- 拟定统一内存口径（待第 8 步确认后冻结；改动须先更新 `design_v0.md` 并留 `report/llm_log/` 决策记录）：
  - IMEM `8192×32 = 32KB`，同步读；DMEM `8192×32 = 32KB`，异步读 + 字节写；
  - 地址范围 `0x8000_0000–0x8000_7FFF`，数组索引 `addr[14:2]`；`tohost` 留在 `0x8000_3FF0`。
  - **DMEM 必须保持异步读**（`design_v0.md` §9 决策 1），否则 v0「无 RAW 停顿、CPI≈1」锚点被破坏。
- 估算 BRAM 占用时按 PYNQ-Z2 口径说明是否宽裕（不要泛泛写「Zynq」，也不要假设能用 DDR）。

## A. 读文档（必做）

- [ ] 通读 `src/riscv/design_v0.md`（接口唯一权威，含 §5 信号表、§6 真值表）
- [ ] 对应章节看 `src/riscv/plan.md`（§3.2 RTL 线任务、§4.1 Part A 验收）
- [ ] 若本步属古法编程某一步，回看 `skill/gufa-programming/SKILL.md` 的流程与失效条件

## B. 核实现状（必做，禁止凭记忆）

- [ ] `git rev-parse --abbrev-ref HEAD`：确认在 `dev/rtl`
- [ ] `git log --oneline -5`：确认最新提交
- [ ] `git status`：确认工作区干净或列出未提交改动
- [ ] 对照契约，产出三类清单并贴在开工回复开头：
  - [ ] ✅ 已实现并验证
  - [ ] 🟡 已实现但未验证
  - [ ] ⬜ 未实现 / 未接入核

## C. 本次范围声明（必做）

- [ ] 本次要改哪些文件（列全，含验证文件与脚本）
- [ ] 是否触及目录边界；若超出预授权范围，先说明
- [ ] 验证方式（编译 / 仿真 / 波形 / lint）与预期结果
- [ ] 预估改动行数（单步 ≤100 行，超标先拆步）

## D. 验证可复现检查（必做）

- [ ] 验证用 tb 落在仓库内（`sim/riscv/`），**不得**用 `/tmp` 临时文件
- [ ] 新 tb 已接入 `sim/scripts/run_iverilog.sh`（含单独模式 + `all` 全量回归）
- [ ] 跑过的命令与原始输出（PASS/FAIL）能原样复现
- [ ] 涉及接口的改动已同步更新 `src/riscv/design_v0.md`

## E. 动手纪律（全程）

- [ ] 单步只做一件事，≤100 行，先设计后写码
- [ ] 每步讲解 + 出 2–3 道理解题，等用户回答再进下一步
- [ ] 卡住超 30 分钟：停下来说明，不硬扛
- [ ] 每步结束汇报四件套：改动文件 / 验证结果 / `git diff --check` / 待办清单

## F. 收尾（commit 前）

- [ ] 全量回归 PASS（`bash sim/scripts/run_iverilog.sh all`）
- [ ] 走 `skill/understand-gate/SKILL.md`：逐段讲解 + 3 题，用户确认理解后才 commit
- [ ] commit message 说明做了什么；AI 产出注明 prompt 要点
- [ ] 关键决策/理解门槛记录写进 `report/llm_log/`
