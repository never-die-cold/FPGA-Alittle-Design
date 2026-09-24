# docs —— 人读入口（先读这个）

> 给谁看：想 5 分钟搞清楚"项目是什么、文件在哪、该怎么找东西"的人。
> 什么时候看：每次开工、或者找不到某样东西的时候。
> 详细目录职责在各目录自己的 README；本文只做导航。

## 项目三句话

1. 是什么：在 PYNQ-Z2 上做一颗自研三级流水 RISC-V 软核 + HDMI 视觉直通流水线 + 轻量 CNN 协处理器，构成片上视觉分析仪（2026 嵌赛 FPGA 赛道 · AMD 自主选题）。
2. 现在到哪：M1 Part A 完成——v0 两级流水核（RV32IM）仿真全过，CoreMark v0 跑分 1.506 CoreMark/MHz；下一步是 Part B 三级流水 + 转发（9/25–9/28）。
3. 计划和验收：看 `src/riscv/plan.md`；接口契约看 `src/riscv/design_v0.md`（唯一权威）。

## 目录地图（每个目录一句话）

| 目录 | 是什么 |
|:---|:---|
| `src/` | 设计源码。`riscv/` 是核心（RTL + plan + design_v0）；`riscv_fw/` 裸机固件；`vision/`、`coprocessor/`、`pynq_host/` 是 M2+ 占位 |
| `sim/` | 验证。`riscv/` 放 tb；`scripts/run_iverilog.sh` 一键回归；`arch_test/` 第三方套件（脚本拉取，不入库） |
| `build/` | Vivado 可复现构建（build.tcl + constraints + 综合报告） |
| `board/` | 上板。`smoke_test/` 工程、`setup.md` 复现指南、`logs/` 上板实测记录（只追加） |
| `data/` | 测试数据。`metrics.csv` 指标汇总；`logs/` 仿真与构建日志；`evidence/` 证据；`golden/` 黄金参考 |
| `report/` | 设计报告 + `llm_log/` 大模型协作记录（纠错轨迹，评委材料） |
| `skill/` | 技能包（understand-gate 等，换题可复用） |
| `docs/` | 本目录：过程文档（工作流、上手、调研、资源） |
| `.github/` | Issue/PR 模板 |

## 找东西（信息归属规则）

| 要找什么 | 去哪里 |
|:---|:---|
| 仿真 / Vivado 构建日志 | `data/logs/` |
| 上板实测记录 | `board/logs/` |
| 协作记录 / 决策过程 | `report/llm_log/` |
| 计划、排期、验收 | `src/riscv/plan.md`；专项计划在 `docs/` 对应文档 |
| 接口定义（唯一权威） | `src/riscv/design_v0.md` |
| 指标数值 | `data/metrics.csv` |
| 证据（golden、源码溯源） | `data/evidence/`、`data/golden/` |
| 学习资料 | `docs/resources.md` |

## 新队友路径

1. 根 `README.md`——作品是什么、要交什么
2. 本文件——目录与归属
3. `docs/onboarding.md`——Git / Markdown / Agent 操作
4. `docs/workflow.md`——开工三件事、理解门槛、收尾四件套
5. 按分工读 `src/riscv/plan.md`（排期）与 `src/riscv/design_v0.md`（契约）

## 日常三条规矩（浓缩版）

1. 开工：读 `docs/workflow.md` 开工三件事，先贴"已实现/未实现"清单再动手。
2. 入库：看不懂的代码不许 commit——先通过理解门槛（`docs/workflow.md` §2）。
3. 收尾：AI 产出立即 commit（注明 prompt 要点）；设计决策写 `report/llm_log/`；跑过的命令必须能从仓库内脚本复现。

## 写作规范（防 AI 味，全员遵守）

1. 正文只写当前事实；改了什么记在文末"变更记录"表，不打日期补丁进正文。
2. 一条规则只写一处，其他地方用链接，不复制粘贴。
3. 开头 3 行内说清：是什么、给谁看、什么时候读。
4. 状态用文字（已完成/进行中/未开始），少用 emoji 和加粗。
5. 表格用于枚举和对照；叙事用短段落。

## 旧路径对照（2026-09-24 整理）

| 旧路径 | 新位置 |
|:---|:---|
| `docs/kickoff_checklist.md` | `docs/workflow.md` |
| `docs/code_review_checklist.md` | `docs/workflow.md` §2 |
| `docs/prep_checklist.md` | `docs/workflow.md` §4（历史清单） |
| `docs/repo_structure.md` | 本文件"目录地图" + 各目录 README |
| `docs/amd_track_awards.md` | `docs/track_research.md` §1 |
| `docs/track_guides_2026_summary.md` | `docs/track_research.md` §2 |
| `docs/coremark_tb_contract.md` | `docs/coremark.md` |
| `docs/coremark_plan.md` | `docs/coremark.md` 附录 A |

历史快照声明：`report/llm_log/` 与 `src/riscv/done/` 按"历史不改写"铁律保留原样，其中的旧链接是历史快照，以本表为准。
