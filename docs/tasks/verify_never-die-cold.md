# 任务文档 · 验证线（组长）—— never-die-cold

> 分支：`dev/verify` ｜ 目录边界：`sim/`；归档可写 `data/logs/`、`data/evidence/`（`metrics.csv` 仍归基准线）
> 窗口：9/14 – 9/27 ｜ 技术内容与验收标准以 [plan.md §3.3 / §2.1–2.2](../../src/riscv/plan.md) 为准
> 双重身份：验证线执行人 + 全队合并把关人（PR 审核、9/20 与 9/27 两次合并、9/27 出口检查）

**状态图例**：✅ 已完成 ｜ 🟡 部分完成 ｜ ⬜ 待办

## 现状（9/14 复核，动手前先看）

| 事项 | 状态 | 说明 |
|:---|:---:|:---|
| `sim/scripts/run_iverilog.sh` 一键回归 | ✅ | 两个 tb 均 PASS（9/11 iverilog；9/14 XSim 复核对拍一致） |
| v0 回归基线归档 `data/logs/v0_baseline_2026-09-14/` | ✅ | PR #12 已归档：iverilog/XSim 双 PASS 对拍 + 复跑方法 + 原始日志 |
| `sim/README.md` | 🟡 | 双工具复核与调用方式已写；缺「六模块验证观察点」与「两档回归跑法」 |
| 转发专项 tb / arch-test / 命中率统计 | ⬜ | 计划中（Part B/C 的先行件） |
| tb 方法学 + 波形阅读 | ⬜ | 本周补 |

## 周 1（9/14–9/20）：基线固化 + 方法学

- [x] 跑通 `sim/scripts/run_iverilog.sh`，输出与结果归档 `data/logs/v0_baseline_2026-09-14/`（后续「优化不改语义」的对照证据）——✅ PR #12
- [ ] tb 方法学 + 波形阅读（[resources.md](../resources.md) §9.2 / UG900）：能从波形数出气泡个数
- [ ] 精读 `design_v0.md`；为 v0 六个模块各写一句「验证观察点」（放 `sim/README.md` 或 llm_log）
- [ ] 理解门槛样板：首个真实 PR 走一遍「讲解 + 3 题 + llm_log 存档」全流程
- [ ] HDLBits 侧重时序电路（计数器 / 移位 / FSM）

## 周 2（9/21–9/27）：测试先行

- [ ] **转发专项 tb 框架**：back-to-back RAW 序列（R-type 连续相关、lw→add 等）+ load-use 停顿判据——按 design_v0 契约先写，先在 v0 上跑出对照数据（v0 应出现气泡/停顿，供 v1 对比）
- [ ] riscv-arch-test 接入：编译 / 比对 signature 机制跑通，至少 1 组 RV32I 子集纳入回归
- [ ] `run_iverilog.sh` 升级：支持「v0 回归集合 + 转发专项」两档
- [ ] 更新 `sim/README.md`（跑法 / 判据 / 证据路径）

## 组长附加职责（与验证线并行）

- [ ] 审每个 PR 按 [code_review_checklist.md](../code_review_checklist.md) 走理解门槛（逐段讲解 + 3 道测试题）；未通过不 merge
- [ ] 9/20、9/27 下午主持合并：审 PR → 合并 → 通知全员 `git pull origin main`
- [ ] 9/27 主持 plan.md §3.5 出口检查：逐项勾，缺口记 llm_log
- [ ] 守红线：`main` 只经 PR 合并；跨目录改动先在群里确认

## 交付物（9/27 验收按此勾）

- [x] v0 回归基线归档（PR #12）
- [ ] 转发 tb 框架 + v0 对照数据
- [ ] arch-test 首组跑通
- [ ] 理解门槛样板（首个 PR 全流程记录）
- [ ] 两次周合并（9/20、9/27）完成并留 PR 记录

## 每天固定动作（全员，plan.md §3.1）

- [ ] HDLBits 5 题（本窗口累计 30+）
- [ ] 理论补课 30 分钟（对照 §5 阶段 0 自测表）
- [ ] 收尾 10 分钟：commit（AI 产出注明 prompt 要点）+ 卡点/决策记 llm_log
- [ ] AI 代码走理解门槛；卡住超 30 分钟发群里

## 关键日期

| 日期 | 事项 |
|:---|:---|
| 9/20 周日 | 上午各线发 PR + 下午首次周合并 + 真题摸底（2023 序列检测） |
| 9/27 周日 | Part A 验收（你主持 §3.5）+ 数字钟限时真题 + 周合并 |
