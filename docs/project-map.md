# 项目地图：5 分钟找到你要的东西

> 给谁看：第一次接手、或者被满仓库日志淹没的人。
> 先读：根 [`README.md`](../README.md) 知道作品是什么；本文件只回答“文件在哪、哪个是当前版本、什么不能改”。
> 维护：目录/入口变化时更新本文件；状态只维护在 [`plan.md`](../plan.md) §3.1，本文件不复制状态细节。

## 1. 一句话

在 PYNQ-Z2 上用自研 RISC-V 核 + HDMI 视觉预处理 + INT8 CNN 协处理器做紧固件识别与工单检查；板端结果经网口到 Windows EXE 展示，视频走 HDMI + USB 采集卡。

## 2. 当前该看哪

- 全项目目标、分工、收口时间、验收：[`plan.md`](../plan.md)（唯一权威）。
- 当前状态、下一交付物、卡点：[`plan.md`](../plan.md) §3.1/§3.2。
- 模块一核：[`src/riscv/plan.md`](../src/riscv/plan.md)、[`src/riscv/design_v1.md`](../src/riscv/design_v1.md)、[`report/module1-closure.md`](../report/module1-closure.md)。
- 模块二视觉：[`src/vision/README.md`](../src/vision/README.md)、[`src/vision/design_v0.md`](../src/vision/design_v0.md)。
- 模块三 CNN：[`src/coprocessor/README.md`](../src/coprocessor/README.md)、[`src/coprocessor/design_v0.md`](../src/coprocessor/design_v0.md)。
- 指标：[`data/metrics.csv`](../data/metrics.csv)。
- 所有运行日志：[`data/logs/README.md`](../data/logs/README.md)；所有证据：[`data/evidence/README.md`](../data/evidence/README.md)。

## 3. 目录地图

```text
├── src/                设计源码（RTL / 固件 / PS 软件 / EXE）
│   ├── riscv/          RV32IM 核、流水线/转发/BHT、最小 SoC、契约
│   ├── vision/         HDMI 预处理、捕获状态、AXI、OSD
│   ├── coprocessor/    INT8 CNN 算子/整网控制器/整数参考
│   ├── riscv_fw/       裸机固件、CoreMark、测试程序；hex/dis 入库
│   ├── pynq_host/      PS 侧配置、定位/ROI、检查服务、FILE/LIVE 骨架
│   └── vision_client/  Windows EXE：UVC、轮次叠加、记录/CSV
├── sim/                testbench 与仿真入口
│   ├── riscv/          RISC-V tb
│   ├── vision/         视觉 tb 与视觉 Python 测试
│   ├── coprocessor/    CNN tb 与整数参考测试
│   ├── arch_test/      riscv-arch-test 目标配置（套件由脚本拉取，不入库）
│   ├── scripts/        一键回归/构建/OOC/上板辅助脚本
│   └── tools/          RV32I 编解码自测等
├── build/              Vivado 可复现构建脚本 + 综合/实现报告
├── board/              上板指南、冒烟工程、上板记录
├── data/               测试数据、指标、运行日志、证据、黄金参考
│   ├── logs/           一次运行一个目录（索引见 logs/README.md）
│   ├── evidence/       源码/构建输入快照、bit 溯源、黄金（索引见 evidence/README.md）
│   └── golden/         测试答案/参考向量
├── docs/               人读文档与导航
│   ├── contracts/      跨模块接口/语义契约
│   ├── runbooks/       上板/NC/训练/复现执行单
│   ├── research/       赛题调研、资源、方案对比
│   ├── archive/        历史快照（不改写）
│   └── file-guide/     逐文件索引生成器（输出到 build/）
├── report/             设计报告 + llm_log 协作记录
├── skill/              Skill 包（换题可复用）
├── models/             FP32/HOG 原型权重（结构例外，见下）
└── results/            外包实验的逐图评估与训练记录（结构例外，见下）
```

### 两个结构例外

`models/`、`results/` 不在赛题推荐目录里，但它们是外包交付拆分后的稳定入口，且被 `data/evidence/2026-10-10-fastener-handoff/installed.csv` 的 48/48 完整性校验和代码默认路径引用。**不要为了“结构好看”移动它们**；已在根 README 和 `data/README.md` 注明例外。

## 4. 数据流（一张图）

```text
相机 HDMI → 板卡视觉流水线 ─┬→ HDMI OUT → 采集卡 → EXE 显示
                            └→ 分析路径 → ROI/CNN → 结果
RISC-V 核 ── 调度/计数/工单判定 ── PS 服务 ── 网口 ── EXE
```

口径：仿真、实现、离板、实机是四种不同证据；文件存在不等于接口已接入，更不等于验收通过。

## 5. 找东西

| 要找什么 | 去哪里 |
|:---|:---|
| 全项目状态/下一交付物/卡点 | [`plan.md`](../plan.md) §3 |
| 某个指标及原始证据 | [`data/metrics.csv`](../data/metrics.csv) |
| 某次仿真/构建/上板的原始输出 | [`data/logs/README.md`](../data/logs/README.md) |
| 某个 bit/结论的输入与哈希 | [`data/evidence/README.md`](../data/evidence/README.md) |
| 某次运行的输入快照恢复了没 | 该 run 的 `SNAPSHOT.md`；命令 `python sim/scripts/restore_snapshot.py --run <run> --check` |
| 上板步骤与实测记录 | [`board/README.md`](../board/README.md)、[`board/logs/`](../board/logs) |
| 团队协作/决策过程 | [`report/llm_log/`](../report/llm_log) |
| 开工纪律/理解门槛 | [`docs/workflow.md`](workflow.md)、[`AGENTS.md`](../AGENTS.md) |
| 仓库卫生规则 | [`docs/repo-hygiene.md`](repo-hygiene.md) |
| 接口契约 | [`docs/contracts/`](contracts/README.md) |
| 执行单/操作手册 | [`docs/runbooks/`](runbooks/README.md) |
| 调研/背景 | [`docs/research/`](research/README.md) |
| 历史快照 | [`docs/archive/`](archive/README.md) |
| 逐文件索引（按需生成） | `python docs/file-guide/tools/generate.py --scope source --date YYYY-MM-DD`，输出在 `build/file-guide/`，不入库 |

## 6. 什么绝对不能改

| 对象 | 原因 |
|:---|:---|
| `data/logs/`、`data/evidence/` 里的原始日志/哈希/图片 | 是验收证据；只追加，不改写 |
| `*.dis`、`*.hex` | 是测试证据；改源码后重新生成，不手改 |
| `design_v0.md`/`design_v1.md` 契约 | 接口唯一权威；先改契约再改 RTL/软件 |
| `pre-cleanup-2026-10-19` 等历史 tag | 证据引用 commit/hash；不改写、不强推 |
| `models/`、`results/` 路径 | 破坏外包交付完整性校验和代码默认值 |

## 7. 阅读顺序

1. 根 [`README.md`](../README.md)：作品是什么、要交什么。
2. 本文件：目录与找东西。
3. [`plan.md`](../plan.md)：当前状态、分工、验收。
4. 按分工读模块 README + 契约；跑测试前读 [`docs/workflow.md`](workflow.md)。
5. 要复现某条证据时，从 `data/logs`/`data/evidence` 的 README 进入，不靠文件名猜。

## 8. 文档状态约定

- **当前**：没有状态标记，或被 `docs/README.md` 列为当前入口。
- **历史快照**：首行有 `> 状态：历史快照（日期）；当前入口见 ...`，内容不改写。
- **建议稿/草案**：标题或状态行注明“建议/草案”，不得当冻结契约引用。
