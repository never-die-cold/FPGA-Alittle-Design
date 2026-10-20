# docs —— 人读入口（5 分钟版）

> 给谁看：新队友、答辩准备、或者“这个文件到底在哪”的时候。
> 先读：根 [`README.md`](../README.md) 知道作品是什么；本文件只做导航，不重复状态。
> 状态唯一权威：[`plan.md`](../plan.md) §3。

## 1. 五分钟路线

1. 根 [`README.md`](../README.md)：作品目标、架构、里程碑、提交物。
2. [`docs/project-map.md`](project-map.md)：目录地图、数据流、找东西、禁止事项。
3. [`plan.md`](../plan.md)：当前状态、分工、验收与卡点。
4. 按分工读模块 README 与契约；动手前读 [`docs/workflow.md`](workflow.md)。
5. 要复现证据时，从 [`data/logs/README.md`](../data/logs/README.md) 或 [`data/evidence/README.md`](../data/evidence/README.md) 进入。

## 2. 当前 / 历史 / 草案

| 类型 | 判定 | 例子 |
|:---|:---|:---|
| 当前 | 无历史标记，且被本文或 `project-map.md` 列为入口 | `plan.md`、`workflow.md`、`onboarding.md`、`project-closeout-three-person-checklist.md`、各模块 README/契约 |
| 历史快照 | 首行有“历史快照（日期）”标记 | `archive/three-day-plan.md`、`archive/partB-*`、`archive/partC-*`、旧 review/交接单 |
| 草案/建议稿 | 标题或状态行注明“草案/建议” | `contracts/inspection-v0-contract.md`、`contracts/c01-capture-status-contract.md` |
| 外包原文 | `docs/outsource/fastener-vision-2026-10-07/`，原字节保留 | 不改写；项目维护版另见 `outsource/fastener-handoff.md` |
| 归档 | `docs/archive/` | 一次性执行单、过期计划；不改写原文 |

**规则**：历史文档不改写；当前文档只在一处维护，其他地方链接。

## 3. 目录地图

| 目录 | 是什么 |
|:---|:---|
| `src/` | 设计源码：RISC-V 核、视觉 RTL、CNN、固件、PS 软件、EXE |
| `sim/` | testbench 与一键仿真/构建入口 |
| `build/` | Vivado 可复现构建脚本 + 综合/实现报告 |
| `board/` | 上板指南、冒烟工程、实测记录 |
| `data/` | 指标、运行日志、证据、黄金参考 |
| `report/` | 设计报告 + `llm_log/` 协作记录 |
| `skill/` | Skill 包 |
| `models/`、`results/` | 外包交付的模型与实验结果；结构例外，不移动 |
| `docs/` | 本目录：导航（README/project-map/repo-hygiene/workflow/onboarding） |
| `docs/contracts/` | 跨模块接口/语义契约（C01/C03/C04、检查、同步、CoreMark） |
| `docs/runbooks/` | 执行单与操作手册（上板、NC、训练、复现、数据采集） |
| `docs/research/` | 赛题调研、资源、方案对比、数据集审计 |
| `docs/archive/` | 历史快照（旧计划、旧交接、旧 review） |

## 4. 找东西

| 要找什么 | 去哪里 |
|:---|:---|
| 目录/数据流/禁止事项 | [`project-map.md`](project-map.md) |
| 全项目状态/下一交付物/卡点 | [`plan.md`](../plan.md) §3 |
| 到收尾还剩什么（无日期待办） | [`closeout-todo.md`](closeout-todo.md) |
| 指标及原始证据 | [`data/metrics.csv`](../data/metrics.csv) |
| 仿真/构建/上板原始日志 | [`data/logs/README.md`](../data/logs/README.md) |
| 源码/bit 溯源与哈希 | [`data/evidence/README.md`](../data/evidence/README.md) |
| 上板步骤与记录 | [`board/README.md`](../board/README.md) |
| 协作记录/决策轨迹 | [`report/llm_log/`](../report/llm_log) |
| 核契约 v0/v1 | [`src/riscv/design_v0.md`](../src/riscv/design_v0.md)、[`src/riscv/design_v1.md`](../src/riscv/design_v1.md) |
| 视觉契约 | [`src/vision/design_v0.md`](../src/vision/design_v0.md) |
| CNN 契约 | [`src/coprocessor/design_v0.md`](../src/coprocessor/design_v0.md) |
| CNN 协处理器状态与交接 | [`contracts/coprocessor-handoff-v0.md`](contracts/coprocessor-handoff-v0.md) |
| CNN 协处理器 J04 实现交接与 OPEN | [`runbooks/coprocessor-j04-handoff.md`](runbooks/coprocessor-j04-handoff.md) |
| 仓库卫生规则 | [`repo-hygiene.md`](repo-hygiene.md) |
| 逐文件索引（按需生成） | `python docs/file-guide/tools/generate.py --scope source --date YYYY-MM-DD` → `build/file-guide/` |

## 5. 当前入口（按角色）

- 全员：[`workflow.md`](workflow.md)（开工三件事/理解门槛/收尾四件套）、[`onboarding.md`](onboarding.md)、[`closeout-todo.md`](closeout-todo.md)（本轮之后还剩什么）。
- 核/协处理器：[`src/riscv/plan.md`](../src/riscv/plan.md)、[`src/riscv/plan_calendar.md`](../src/riscv/plan_calendar.md)、[`src/coprocessor/README.md`](../src/coprocessor/README.md)、[`runbooks/coprocessor-j04-handoff.md`](runbooks/coprocessor-j04-handoff.md)。
- 视觉/上板：[`src/vision/README.md`](../src/vision/README.md)、[`board/README.md`](../board/README.md)、[`contracts/c01-capture-implementation-baseline.md`](contracts/c01-capture-implementation-baseline.md)。
- 模型/数据：[`runbooks/module3-model-training.md`](runbooks/module3-model-training.md)、[`outsource/fastener-handoff.md`](outsource/fastener-handoff.md)。
- EXE/服务：[`src/pynq_host/README.md`](../src/pynq_host/README.md)、[`src/vision_client/README.md`](../src/vision_client/README.md)。
- 交付/答辩：[`docs/project-closeout-three-person-checklist.md`](project-closeout-three-person-checklist.md)、[`report/`](../report)。

## 6. 写作规范（防 AI 味）

1. 正文只写当前事实；改了什么记文末“变更记录”，不打日期补丁进正文。
2. 一条规则只写一处，其他地方用链接，不复制粘贴。
3. 开头 3 行内说清：是什么、给谁看、什么时候读。
4. 状态用文字（已完成/进行中/未开始），少用 emoji 和加粗。
5. 表格用于枚举和对照；叙事用短段落。
6. 历史文档加状态行，不改写原文。

## 7. 旧路径对照（仍有效的）

| 旧路径 | 新位置 |
|:---|:---|
| `docs/kickoff_checklist.md` | `docs/workflow.md` |
| `docs/code_review_checklist.md` | `docs/workflow.md` §2 |
| `docs/prep_checklist.md` | `docs/workflow.md` §5（历史） |
| `docs/repo_structure.md` | `docs/project-map.md` + 各目录 README |
| `docs/amd_track_awards.md` | `docs/research/track_research.md` §1 |
| `docs/track_guides_2026_summary.md` | `docs/research/track_research.md` §2 |
| `docs/coremark_tb_contract.md` / `coremark_plan.md` | `docs/contracts/coremark.md` |
| `docs/file-guide/index.html` 等生成物 | 按需生成到 `build/file-guide/`，不再入库 |

## 8. 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-19 | 新增[收口待办](closeout-todo.md)（无日期版，含冻结项与伪通过判据）；J04 状态拆成 J04a/J04b，交接单迁到 `runbooks/` |
| 2026-10-19 | 仓库整理：重写为 5 分钟导航；docs 分为 contracts/runbooks/research/archive；日志快照去重并加 manifest/恢复脚本；file-guide 生成物改为按需生成；合并 dev/riscv 的 CNN 协处理器交接入口 |
| 2026-10-18 | 新增 CNN 协处理器 v0 薄交接索引；原 10/13 CNN/DDR 文档保留为历史证据 |
| 2026-10-12 | 导航同步整数参考、FILE/LIVE 软件与 C01；Q01 标明已修复 |
| 2026-10-09 | B01：区分三层收口状态并链接证据；补齐对应版本接口导航 |
