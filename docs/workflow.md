# workflow —— 开工清单、理解门槛与交付纪律

> 给谁看：全体队员 + AI agent（每次开工前必读）。
> 什么时候读：每次开新会话或新一步前，从头过一遍「必做」项再动手。
> 三份旧文档的合并：原 `kickoff_checklist.md`（§1/§3/§4）、`code_review_checklist.md`（§2）、`prep_checklist.md`（§5 历史存证）。
> 配套：目录边界与红线同时写在根 `AGENTS.md`；接口契约以 `src/riscv/design_v0.md` 为准；排期与验收以 `src/riscv/plan.md` 为准。

## §1 开工三件事（必做，缺一不可）

1. **读开工清单**：通读本文件 §1–§4；对应步骤回看 `skill/gufa-programming/SKILL.md`（古法编程流程与失效条件）。
2. **核实现状**：跑 `git rev-parse --abbrev-ref HEAD`、`git log --oneline -5`、`git status`；对照 `src/riscv/design_v0.md`（接口唯一权威）与 `src/riscv/plan.md`，在开工回复开头贴三类清单：
   - ✅ 已实现并验证
   - 🟡 已实现但未验证
   - ⬜ 未实现 / 未接入核
3. **声明本次范围**：一句话说明要改哪些文件、验证方式、预估行数。

## §2 理解门槛（看不懂的代码不许入库）

> 一句话规则：**看不懂的代码不许 commit——不管它是 AI 写的还是队友写的。**"能跑"不是入库标准，"讲得清"才是。
> 自动化执行见 `skill/understand-gate/SKILL.md`；本节约定的是标准本身。

### 作者自查（commit 前逐条打勾）

- [ ] 我能不看着代码，向队友口头讲出每个 always 块 / 每个模块在干什么（讲设计意图，不是逐行念）
- [ ] 我能回答：这个信号为什么要寄存（或不寄存）？去掉 `stall` / `flush` / 某个条件分支会发生什么？
- [ ] 每个 localparam、信号名我能解释语义，代码里没有我讲不出的魔数
- [ ] 我让 agent（或自己）出了 3 道"如果改成 XX 会怎样"的问题，并且自己答上了（防止只是背答案）
- [ ] 验证通过的证据（波形、日志、用例数）已留痕（commit message 或 `report/llm_log/`）

任何一条做不到：先问 agent 逐段讲解，直到能讲出来，再回来打勾。读不懂的地方就是知识缺口清单。

### 复核人抽查（合入前）

1. 复核人随机挑约 10 行代码，让作者当场讲意图
2. 讲得清 → 通过，复核人署名；讲不清 → 打回，作者回去补理解（不是回去改代码——代码可能没错，错的是理解）
3. 三人团队：每周例会固定 30 分钟"屎山巡检"，抽一个本周合入模块由非作者讲给全员听，讲不清的标记为答辩演练重点

## §3 每步交付纪律

- 单步只做一件事，≤100 行，先设计后写码（古法编程）
- 卡住超 30 分钟：停下来说明，不硬扛
- 每步结束汇报四件套：① 改了哪些文件；② 验证命令与原始结果；③ `git diff --check`；④ 待办 / 未接入清单（明确标注"未实现"）
- 讲解 + 2–3 道理解题，等用户回答再进下一步（古法编程要求）

## §4 收尾（commit 前）

- [ ] 涉及 RTL：全量回归 PASS（`bash sim/scripts/run_iverilog.sh all`），tb 落在仓库内（`sim/riscv/`），不得用工作区外临时文件
- [ ] 新 tb 已接入 `sim/scripts/run_iverilog.sh`（单独模式 + `all` 全量）
- [ ] 涉及接口的改动已同步 `src/riscv/design_v0.md`
- [ ] commit message 说明做了什么；AI 产出注明 prompt 要点
- [ ] 关键决策 / 理解门槛记录写进 `report/llm_log/`
- [ ] 未经用户确认理解，不得 commit

## §5 历史：开工前准备清单（已闭环，仅存证）

原 `docs/prep_checklist.md`（2026-09-11 起）。🔴 项已全部闭环：

- PYNQ 镜像烧录验证 ✅ 2026-09-20 板卡到货、SD 卡烧录、SSH 远程可用（全队共用 1 块板）
- RISC-V 工具链 ✅ 2026-09-11 跑通 elf/反汇编/hex（MSYS2 ucrt64，GCC 14.2.0）

未闭环项已移交 GitHub issues：报名状态核对、演示硬件到位（规格见 `board/hardware.md`）、三人 git 流程演练。

## 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-09-24 | `kickoff_checklist.md` + `code_review_checklist.md` + `prep_checklist.md` 三合一为本文件；目录边界与红线保留在 `AGENTS.md`，不重复 |
