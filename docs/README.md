# docs —— 人读入口（5 分钟版）

> 给谁看：评委、新队友、答辩准备、或者“这个文件到底在哪”的时候。
> 先读：根 [`README.md`](../README.md) 知道作品是什么；本文件只做导航，不重复状态。
> 状态唯一权威：[`plan.md`](../plan.md) §3。

## 1. 五分钟路线

1. 根 [`README.md`](../README.md)：作品目标、架构与提交物。
2. [`docs/project-map.md`](project-map.md)：目录地图、数据流、找东西、禁止事项。
3. [`plan.md`](../plan.md)：当前状态、验收与卡点。
4. 论文级总览：[`docs/project-overview.md`](project-overview.md)、[`docs/project-summary-2026-10-27.md`](project-summary-2026-10-27.md)。
5. 动手前读 [`docs/workflow.md`](workflow.md)；要追证据时，从 [`data/logs/README.md`](../data/logs/README.md) 或 [`data/evidence/README.md`](../data/evidence/README.md) 进入。

## 2. 提交物与过程材料

| 类型 | 在哪 |
|:---|:---|
| 作品技术文档 | [`tech-report/`](tech-report/README.md)（PDF 由 `build_tech_report.py` 生成） |
| 答辩海报 | [`poster/`](poster/README.md) |
| 架构图 | [`img/`](img/)（由 `make_project_diagrams.py` 生成） |
| 跨模块冻结契约 | [`contracts/`](contracts/README.md)（C01/C02/C03/C04、检查、同步、CoreMark） |
| 操作手册（运行book，被契约引用的现役件） | `runbooks/` |
| 大模型协作过程记录（加分项） | [`../report/llm_log/`](../report/llm_log) |
| 历史快照（不改写） | `docs/archive/`（仅保留被现行报告引用的两篇） |

**规则**：历史文档不改写；当前文档只在一处维护，其他地方链接。2026-10-29 提交瘦身：过程性文档（旧执行单、外包原文、旧分析稿、file-guide 生成器）移出仓库，原文见 git 历史 commit 88ac1c4。

## 3. 目录地图

| 目录 | 是什么 |
|:---|:---|
| `src/` | 设计源码：RISC-V 核、视觉 RTL、CNN、固件、PS 软件 |
| `sim/` | testbench 与一键仿真/构建入口 |
| `build/` | Vivado 可复现构建脚本 + 综合/实现报告 |
| `board/` | 上板指南、冒烟工程、实测记录 |
| `data/` | 指标、运行日志、证据、黄金参考 |
| `report/` | 设计报告 + `llm_log/` 协作记录 |
| `tools/` | 本地辅助脚本（cop_payload_loader 等） |
| `skill/` | Skill 包（协作纪律沉淀，加分项） |
| `models/`、`results/` | 外包交付的模型与实验结果；结构例外，不移动 |
| `docs/` | 本目录：报告/海报/契约/手册/导航 |
| `others/` | 本地非仓库文件（构建产物/YOLO/VCD；gitignore，不入库） |

## 4. 找东西

| 要找什么 | 去哪里 |
|:---|:---|
| 目录/数据流/禁止事项 | [`project-map.md`](project-map.md) |
| 全项目状态/下一交付物/卡点 | [`plan.md`](../plan.md) §3 |
| 指标及原始证据 | [`data/metrics.csv`](../data/metrics.csv) |
| 仿真/构建/上板原始日志 | [`data/logs/README.md`](../data/logs/README.md) |
| 源码/bit 溯源与哈希 | [`data/evidence/README.md`](../data/evidence/README.md) |
| 上板步骤与记录 | [`board/README.md`](../board/README.md) |
| 协作记录/决策轨迹 | [`report/llm_log/`](../report/llm_log) |
| 核契约 v0/v1 | [`src/riscv/design_v0.md`](../src/riscv/design_v0.md)、[`src/riscv/design_v1.md`](../src/riscv/design_v1.md) |
| 视觉契约 | [`src/vision/design_v0.md`](../src/vision/design_v0.md) |
| CNN 契约 | [`src/coprocessor/design_v0.md`](../src/coprocessor/design_v0.md) |
| CNN 协处理器状态与交接 | [`contracts/coprocessor-handoff-v0.md`](contracts/coprocessor-handoff-v0.md) |
| CNN 训练流程 | [`runbooks/module3-model-training.md`](runbooks/module3-model-training.md) |
| 仓库卫生规则 | [`repo-hygiene.md`](repo-hygiene.md) |

## 5. 当前入口（按角色）

- 全员：[`workflow.md`](workflow.md)（开工三件事/理解门槛/收尾四件套）。
- 核/协处理器：[`src/riscv/README.md`](../src/riscv/README.md)、[`src/coprocessor/README.md`](../src/coprocessor/README.md)、[`runbooks/coprocessor-j04-handoff.md`](runbooks/coprocessor-j04-handoff.md)；核收口报告 [`report/module1-closure.md`](../report/module1-closure.md)。
- 视觉/上板：[`src/vision/README.md`](../src/vision/README.md)、[`board/README.md`](../board/README.md)、[`contracts/c01-capture-implementation-baseline.md`](contracts/c01-capture-implementation-baseline.md)。
- 模型/数据：[`runbooks/module3-model-training.md`](runbooks/module3-model-training.md)、[`runbooks/offline-inspection.md`](runbooks/offline-inspection.md)。
- 前端：[`src/web_client/README.md`](../src/web_client/README.md)；板端服务：[`src/pynq_host/README.md`](../src/pynq_host/README.md)。
- 交付/答辩：[`plan.md`](../plan.md) §3、[`tech-report/`](tech-report/README.md)、[`poster/`](poster/README.md)、[`report/`](../report)。

## 6. 写作规范（防 AI 味）

1. 正文只写当前事实；改了什么记文末“变更记录”，不打日期补丁进正文。
2. 一条规则只写一处，其他地方用链接，不复制粘贴。
3. 开头 3 行内说清：是什么、给谁看、什么时候读。
4. 状态用文字（已完成/进行中/未开始），少用 emoji 和加粗。
5. 表格用于枚举和对照；叙事用短段落。
6. 历史文档加状态行，不改写原文。

## 7. 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-29 | 提交瘦身：docs 收敛为契约/手册(现役)/报告/海报/导航；旧执行单与外包原文见 git 历史 |
| 2026-10-19 | 重写为 5 分钟导航；docs 分为 contracts/runbooks/research/archive；file-guide 生成物改为按需生成 |
| 2026-10-12 | 导航同步整数参考、FILE/LIVE 软件与 C01 |
| 2026-10-09 | B01：区分三层收口状态并链接证据 |
