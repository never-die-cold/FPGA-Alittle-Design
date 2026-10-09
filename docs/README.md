# docs —— 人读入口（先读这个）

> 给谁看：想 5 分钟搞清楚"项目是什么、文件在哪、该怎么找东西"的人。
> 什么时候看：每次开工、或者找不到某样东西的时候。
> 详细目录职责在各目录自己的 README；本文只做导航。

## 项目三句话

1. 是什么：在 PYNQ-Z2 上用自研 RISC-V + HDMI 视觉流水线 + CNN 协处理器识别桌面紧固件，视频经采集卡进入 Windows EXE，统一显示识别框、类别、计数与工单异常（2026 嵌赛 FPGA 赛道 · AMD 自主选题）。
2. 现在到哪：按下表区分模块收口与全项目验收。自由分散且互不遮挡、传统定位 + CNN 分类路线已确定；EXE 由 watercopper 负责。
3. 计划和验收：根目录 `plan.md` 管全项目收口、分工和交付看板；`src/riscv/plan.md` 只管核专项，`src/riscv/plan_calendar.md` 只管核任务与卡点。接口按模块与核版本看对应设计契约。

| 层次 | 状态与证据 |
|:---|:---|
| 模块一 | 核＋最小 SoC 已完成收口。[核收口报告](../report/module1-closure.md) |
| 模块二 | HDMI 视觉预处理 RTL＋已验证视频链路已完成（RTL／链路级）。[RTL 与视频记录](../data/logs/2026-10-03-vision-onboard/README.md)、[真实相机链路记录](../data/logs/2026-10-07-pi-pynq/README.md) |
| 全项目 M2 | 全项目 M2 验收未完成；CNN、网络硬件输出和工业闭环不得宣称完成。验收范围见[主计划](../plan.md) §1.4；前两层收口不替代全项目验收。 |

## 目录地图（每个目录一句话）

| 目录 | 是什么 |
|:---|:---|
| `src/` | 设计源码。`riscv/` 是核与最小 SoC（RTL + plan + design_v0/design_v1）；`riscv_fw/` 裸机固件；`vision/` 图像预处理与视频链路；`coprocessor/` 未实现；`pynq_host/` PS 配置协议与 mock；`vision_client/` Windows EXE 原型 |
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
| 全项目目标、收口、分工和验收 | 根目录 `plan.md` |
| 全项目下一交付物、依赖与卡点 | 根目录 `plan.md` §3 |
| RISC-V 核专项计划与看板 | `src/riscv/plan.md`、`src/riscv/plan_calendar.md` |
| Part B 验证与验收执行清单 | `docs/partB-verify-plan.md` |
| 模块三训练与量化前期 | `docs/module3-model-training.md` |
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

- Q01：D6 覆盖结果报文；未知字段拒绝的实现缺口另批裁决，见[核查注记](vision-sync-protocol-decisions.md)。
- Q02：`run_iverilog.sh` 缺失 tb 时 continue 的风险只登记，本轮不改 fail-fast 语义。
- Q03：本地有 `partA-v0`；未取得 `archive/pi-hdmi-diagnostics-2026-10-08`，不查远端、不建替代 tag。
- Q04：[中文探索报告](方案探索报告.md)与[英文名 audit](localization-exploration-audit.md)正文一致；保留两份，权威正文待用户裁决。
- Q05：旧配图标“历史快照：BHT 尚未绘制”，见[总览](project-overview.md)；重绘另批。
- Q06：三处历史／第三方本地链接缺失见[索引](../data/logs/2026-10-09-module1-2-closeout/inventory-links.txt)；原文保留，外部 HTTP 链接未重查。
- 全量读过的文件与初始指纹见[机器索引](../data/logs/2026-10-09-module1-2-closeout/file-index.txt)，不手写重复清单。

## 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-09 | B01：区分三层收口状态并链接证据；补齐对应版本接口导航；纠正提交纪律。 |
