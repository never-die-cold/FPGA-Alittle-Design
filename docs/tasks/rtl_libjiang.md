# 任务文档 · RTL 线 —— LibJiang

> 分支：`dev/rtl` ｜ 目录边界：`src/riscv/`（跨目录先在群里说一声）
> 窗口：9/14 – 9/27（阶段 0 + Part A 收口）｜ 技术内容与验收标准以 [plan.md §3.2 / §4.1](../../src/riscv/plan.md) 为准
> 你是后续所有 RTL 的接手人：v0 已提前落地打底，第一要务是**读懂 + 讲解过关**，不是重写。

**状态图例**：✅ 已完成 ｜ 🟡 部分完成 ｜ ⬜ 待办 ｜ ⏸ 顺延（等 PYNQ-Z2，issue #1）

## 现状（9/14 复核，动手前先看）

| 事项 | 状态 | 说明 |
|:---|:---:|:---|
| v0 六模块 RTL（pc / if_stage / decode / alu / regfile / core_top） | ✅ | 9/11 落地，逐指令 38 用例全过 |
| 工具链闭环（C→elf→dis→hex） | ✅ | `src/riscv_fw/` 可直接用 |
| Vivado 综合基线（Fmax / 资源） | ✅ | 9/14 完成：Fmax 86.8 MHz / WNS -1.530、LUT 846 / FF 65；数据在 `data/metrics.csv`、报告在 `build/reports/` |
| 理解门槛（精读 + 逐段讲解 + 3 题） | ⬜ | **你的第一项任务**；RTL 提前落地 ≠ 已理解，讲解稿存 `report/llm_log/` |
| `muldiv.v`（M 扩展） | ⬜ | 计划中 |
| 最小 SoC 外壳（仿真） | ⬜ | 计划中 |
| `design_v0.md` 同步（muldiv 决策） | ⬜ | 计划中 |

> 结论：Part A 只剩 3 件实事——muldiv、SoC 外壳（仿真）、design_v0 同步；基线数据已入档，不用重做。

## 周 1（9/14–9/20）：吃透 + 准备

- [ ] 精读 `design_v0.md` + v0 六模块 RTL，过理解门槛（逐段讲解 + 3 道测试题；讲解稿存 `report/llm_log/`）
- [ ] COAD 4.1–4.5：能徒手画单周期 RV32I 数据通路并标注控制信号
- [ ] 蜂鸟 E203 书前 3 章速读：能说出 E203 与我们的两级结构差异
- [ ] `muldiv` 设计准备（先设计后写码）：读 design_v0.md §9，写出「移位加减」架构要点 + 接口草案，**发群里对齐后再动手**

## 周 2（9/21–9/27）：Part A 收口

- [ ] `muldiv.v`：RV32M 乘除实现 + 单指令测试（接口风格对齐现有模块）
- [ ] 最小 SoC 外壳：指令 BRAM 预载 hex + LED / UART 二选一，仿真跑通（落在 `src/riscv/`；⏸ 上板顺延，issue #1）
- [ ] 同步更新 `design_v0.md`（muldiv 接口与实现决策）
- [ ] 风险预案：M 扩展卡住 → 保住 RV32I 部分先收口，乘除后补（不影响其余验收）

## 交付物（9/27 验收按此勾）

- [ ] muldiv + 单指令测试
- [ ] SoC 外壳仿真 PASS
- [ ] design_v0.md 同步
- [ ] 理解门槛讲解稿落盘（≥1 条 llm_log，计入全员「≥2 条」）

## 每天固定动作（全员，plan.md §3.1）

- [ ] HDLBits 5 题（本窗口累计 30+，先刷完 Verilog Language）
- [ ] 理论补课 30 分钟（对照 §5 阶段 0 自测表）
- [ ] 收尾 10 分钟：commit（AI 产出注明 prompt 要点）+ 卡点/决策记 llm_log
- [ ] AI 代码走理解门槛；卡住超 30 分钟发群里

## 边界与红线

- 只动 `src/riscv/`（SoC 外壳已并入本目录）；跨目录改动先在群里说一声
- **任何人（含组长）不直接 push `main`**，一切改动走 PR（`docs/git_learning/branch_workflow.md`）
- 每晚 commit，别攒着；小步提交方便组长审理解门槛

## 关键日期

| 日期 | 事项 |
|:---|:---|
| 9/20 周日 | 上午发 PR + 下午首次周合并 + 真题摸底（2023 序列检测） |
| 9/27 周日 | Part A 验收（plan.md §3.5）+ 数字钟限时真题 + 周合并 |
