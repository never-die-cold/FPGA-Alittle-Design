# 任务文档 · 基准线 —— waltercooper

> 分支：`dev/bench` ｜ 目录边界：`src/riscv_fw/`、`data/`（动 `report/llm_log` 等共享文件先群里说）
> 窗口：9/14 – 9/27 ｜ 技术内容与验收标准以 [plan.md §3.4](../../src/riscv/plan.md) 为准
> 你的产出决定「CPI 降 ≥25%」这条指标能否被量化证明：先把尺子造出来，再谈优化。

**状态图例**：✅ 已完成 ｜ 🟡 部分完成 ｜ ⬜ 待办

## 现状（9/14 复核，动手前先看）

| 事项 | 状态 | 说明 |
|:---|:---:|:---|
| 工具链闭环（C→elf→dis→hex） | ✅ | `src/riscv_fw/` 已有 Makefile 与 README；**但你要独立复现一遍**，卡点补进 README |
| `data/metrics.csv` 骨架 | ✅ | 表头 + Fmax/资源 2 行（9/14 Vivado 基线）；CPI 行仍空 |
| 测量条件 / 填报约定 | 🟡 | `data/README.md` 有约定；「日志 → 表格」操作说明未写 |
| benchmark / CPI harness | ⬜ | 计划中 |
| 两次合并证据汇总 | ⬜ | 9/20 后开始 |

## 周 1（9/14–9/20）：复现 + 摸底

- [ ] 按 `src/riscv_fw/README.md` 独立复现工具链闭环（C → elf → 反汇编 → hex），把卡点补进 README（变成新人手册）
- [ ] 调研 Dhrystone / CoreMark / Embench 统计口径，产出 1 页《CPI 怎么测》笔记（`data/scripts/` 或 llm_log）
- [ ] RISC-V 手册第 2 章：给定汇编能手算机器码、给定机器码能反汇编（可用 `sim/tools/verify_rv32i.py` 自测）
- [ ] 通读 README + [proposal_upgrade.md](../proposal_upgrade.md)：建立作品全貌（文档与答辩素材的来源）

## 周 2（9/21–9/27）：benchmark + 度量工具

- [ ] benchmark C 程序 v0.1：循环 / 数组 / 函数调用 / 位运算 / 乘法混编（Dhrystone 思路），C 源码 + 反汇编归档
- [ ] CPI 统计 harness 脚本骨架：仿真侧统计 retired 指令数 / 周期数（`data/scripts/`）
- [ ] `data/metrics.csv` 填报规范：日志 → 表格的流程（测量条件必填）——在 `data/README.md` 基础上补操作说明
- [ ] 两次合并（9/20、9/27）的证据与 llm_log 汇总整理

## 交付物（9/27 验收按此勾）

- [ ] 工具链复现手册定稿
- [ ] benchmark v0.1（C 源码 + 反汇编）
- [ ] CPI harness 骨架
- [ ] metrics 填报规范

## 每天固定动作（全员，plan.md §3.1）

- [ ] HDLBits 5 题（本窗口累计 30+）
- [ ] 理论补课 30 分钟（对照 §5 阶段 0 自测表）
- [ ] 收尾 10 分钟：commit（AI 产出注明 prompt 要点）+ 卡点/决策记 llm_log
- [ ] AI 代码走理解门槛；卡住超 30 分钟发群里

## 边界与红线

- 只动 `src/riscv_fw/`、`data/`；改 README / plan.md / llm_log 前先在群里说一声
- 数据铁律：先测基线再谈优化；测量条件必填；报告数值必须能追溯到 `data/` 原始文件
- **任何人（含组长）不直接 push `main`**，一切改动走 PR（`docs/git_learning/branch_workflow.md`）

## 关键日期

| 日期 | 事项 |
|:---|:---|
| 9/20 周日 | 上午发 PR + 下午首次周合并 + 真题摸底（2023 序列检测） |
| 9/27 周日 | Part A 验收 + 数字钟限时真题 + 周合并 |
