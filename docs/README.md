# docs —— 人读入口（先读这个）

> 给谁看：想 5 分钟搞清楚"项目是什么、文件在哪、该怎么找东西"的人。
> 什么时候看：每次开工、或者找不到某样东西的时候。
> 详细目录职责在各目录自己的 README；本文只做导航。

## 项目三句话

1. 是什么：在 PYNQ-Z2 上用自研 RISC-V + HDMI 视觉流水线 + CNN 协处理器识别受控工位的紧固件，视频经采集卡进入 Windows EXE，统一显示识别框、类别、计数与工单异常（2026 嵌赛 FPGA 赛道 · AMD 自主选题）。
2. 现在到哪：按下表区分模块收口与全项目验收。OpenCV/HOG/小 CNN 离线原型和外包材料已接收，正式板端定位/ROI、INT8 模型和工业闭环未验收。自由分散且互不遮挡、传统定位 + CNN 分类路线已确定；EXE 由 watercopper 负责。
3. 计划和验收：根目录 `plan.md` 管全项目收口、分工和交付看板；`src/riscv/plan.md` 只管核专项，`src/riscv/plan_calendar.md` 只管核任务与卡点。接口按模块与核版本看对应设计契约。

| 层次 | 状态与证据 |
|:---|:---|
| 模块一 | 核＋最小 SoC 已完成收口。[核收口报告](../report/module1-closure.md) |
| 模块二 | HDMI 视觉预处理 RTL＋已验证视频链路已完成（RTL／链路级）。[RTL 与视频记录](../data/logs/2026-10-03-vision-onboard/README.md)、[真实相机链路记录](../data/logs/2026-10-07-pi-pynq/README.md) |
| 模块三 | CNN算子/整网控制器、诊断整数黄金与控制器OOC已有；实体缓存/MMIO/DMA、正式模型与板端输出仍缺。[协处理器交接索引](coprocessor-handoff-v0.md) |
| 全项目 M2 | 全项目 M2 验收未完成；CNN、网络硬件输出和工业闭环不得宣称完成。验收范围见[主计划](../plan.md) §1.4；前两层收口不替代全项目验收。 |

## 目录地图（每个目录一句话）

| 目录 | 是什么 |
|:---|:---|
| `src/` | 设计源码。`riscv/` 是核与最小 SoC；`riscv_fw/` 冒烟/基准固件；`vision/` 预处理与捕获状态 RTL；`coprocessor/` C02整数参考、CNN算子与整网控制器；`pynq_host/` 配置、DDR单帧候选驱动、FP32文件检查、MOCK/FILE-LIVE骨架；`vision_client/` 视频/LIVE展示与记录原型 |
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
| 每个项目文件的用途与相互关系 | [逐文件说明](file-guide/README.md)、[可搜索页面](file-guide/index.html)、[完整CSV](file-guide/files.csv) |
| 仿真 / Vivado 构建日志 | `data/logs/` |
| 上板实测记录 | `board/logs/` |
| 协作记录 / 决策过程 | `report/llm_log/` |
| 全项目目标、收口、分工和验收 | 根目录 `plan.md` |
| 全项目下一交付物、依赖与卡点 | 根目录 `plan.md` §3 |
| 当前源码与文档状态核对 | [实现/文档清单](implementation-document-audit-2026-10-12.md)；[三人执行清单](project-closeout-three-person-checklist.md) |
| 原彩色捕获与DDR取帧边界 | [C01基线](c01-capture-implementation-baseline.md)、[帧槽所有权候选](c01-ddr-frame-ownership-v0.md) |
| RISC-V 核专项计划与看板 | `src/riscv/plan.md`、`src/riscv/plan_calendar.md` |
| Part B 验证与验收执行清单 | `docs/partB-verify-plan.md` |
| 模块三训练与量化前期 | `docs/module3-model-training.md` |
| CNN 协处理器契约、状态与 WC/NC 交接 | [协处理器交接索引](coprocessor-handoff-v0.md) |
| 外包视觉交接包、接收差异与复现缺口 | [交接索引](outsource/fastener-handoff.md) |
| 视频/结果同步协议决策单 | `docs/vision-sync-protocol-decisions.md` |
| RISC-V v0 接口（基线唯一权威） | [src/riscv/design_v0.md](../src/riscv/design_v0.md) |
| RISC-V v1 接口（Part B/C 唯一权威） | [src/riscv/design_v1.md](../src/riscv/design_v1.md) |
| HDMI 视觉预处理接口 | [src/vision/design_v0.md](../src/vision/design_v0.md) |
| 指标数值 | `data/metrics.csv` |
| 证据（golden、源码溯源） | `data/evidence/`、`data/golden/` |
| 学习资料 | `docs/resources.md` |

## 新队友路径

1. 根 `README.md`——作品是什么、要交什么
2. 本文件——目录与归属
3. `docs/onboarding.md`——Git / Markdown / Agent 操作
4. `docs/workflow.md`——开工三件事、理解门槛、收尾四件套
5. 先读根目录 `plan.md`（全项目），再按分工读模块自己的计划与契约；核专项在 `src/riscv/plan.md`

## 日常三条规矩（浓缩版）

1. 开工：读 `docs/workflow.md` 开工三件事，先贴"已实现/未实现"清单再动手。
2. 入库：看不懂的代码不许 commit——先通过理解门槛（`docs/workflow.md` §2）。
3. 收尾：通过理解门槛且获提交授权后才可 commit（注明 prompt 要点）；设计决策写 `report/llm_log/`；跑过的命令必须能从仓库内脚本复现。

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

## 本轮只登记的事项（2026-10-09）

- Q01：当时登记结果报文白名单缺口，已随 PR #67 修复；当前 v1.2 允许 LIVE 分类/判定字段并继续严格拒绝未知字段，见[协议注记](vision-sync-protocol-decisions.md)。
- Q02：`run_iverilog.sh` 缺失 tb 时 continue 的风险只登记，本轮不改 fail-fast 语义。
- Q03：本地有 `partA-v0`；未取得 `archive/pi-hdmi-diagnostics-2026-10-08`，不查远端、不建替代 tag。
- Q04：[中文探索报告](方案探索报告.md)与[英文名 audit](localization-exploration-audit.md)正文一致；保留两份，权威正文待用户裁决。
- Q05：旧配图标“历史快照：BHT 尚未绘制”，见[总览](project-overview.md)；重绘另批。
- Q06：三处历史／第三方本地链接缺失见[索引](../data/logs/2026-10-09-module1-2-closeout/inventory-links.txt)；原文保留，外部 HTTP 链接未重查。
- 全量读过的文件与初始指纹见[机器索引](../data/logs/2026-10-09-module1-2-closeout/file-index.txt)，不手写重复清单。

## 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-12 | 导航同步整数参考、FILE/LIVE软件与C01；Q01标明已修复，旧索引/配图仍保留历史性质 |
| 2026-10-18 | 新增 CNN 协处理器 v0 薄交接索引；原 10/13 CNN/DDR 文档保留为历史证据。 |
| 2026-10-09 | B01：区分三层收口状态并链接证据；补齐对应版本接口导航；纠正提交纪律。 |
