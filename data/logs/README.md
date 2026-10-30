# data/logs —— 运行记录索引

> 给谁看：查一次仿真、构建、上板或代码审查原始证据的人。
> 规则：一次运行一个目录；目录名 `YYYY-MM-DD-topic`；每个目录必须有 `README.md`。
> 模板：[`_template/README.md`](_template/README.md)。新增目录后运行 `python sim/scripts/index_runs.py --write` 刷新本索引。
> 所有 run README 均为历史快照：只追加、不改写；当前状态只看根目录 [plan.md](../../plan.md) §3.1。

## 硬规则

1. 原始日志只追加，不改写；需要更正时新加一条记录。
2. 每个目录的 `README.md` 至少写：日期、commit、命令、结果、产物、边界/未完成项。
3. 证据分级：**A** 被 `data/metrics.csv` 或 `report/` 引用；**B** 支撑结论但未直接引用；**C** 过程/尝试/草稿。
4. 源码或输入快照由 `SNAPSHOT-MANIFEST.json` + `SNAPSHOT.md` 管理；能由 Git blob 恢复的副本不再重复存放。
5. 恢复快照：`python sim/scripts/restore_snapshot.py --run <目录> --check`，需要写回时加 `--restore`。
6. 目录里不要放 `.vvp`、`.dcp`、`__pycache__`、Vivado 工程缓存；这些是生成物。
7. 当前目录缺 README 的标记为 `PROVENANCE GAP`；补说明时只写能核实的事实，未知处写“待核”。

<!-- RUN-INDEX:START -->
## 目录索引（55 个运行，自动生成）

| 目录 | 日期 | 文件数 | 大小 | 说明 |
|:---|:---:|---:|---:|:---|
| `c01-capture-e2a602d6e0da49a2b6da072abca47c70` | — | 83 | 3.3 MB | c01-capture-e2a602d6e0da49a2b6da072abca47c70 |
| `2026-10-28-washer-collection` | 2026-10-28 | 98 | 2.4 MB | 2026-10-28 CNN 继续训练与本地实验隔离 |
| `2026-10-28-standing-nut` | 2026-10-28 | 154 | 6.9 MB | 2026-10-28 五螺母、两竖立姿态诊断 |
| `2026-10-28-r6-holdout-layout04` | 2026-10-28 | 58 | 1.6 MB | Frozen r6: new placement of the existing specimens |
| `2026-10-28-multitarget-board-r6` | 2026-10-28 | 141 | 3.8 MB | Multi-target result-slot fix and frozen CNN r6 on-board comparison |
| `2026-10-28-mixed-standing-r6` | 2026-10-28 | 30 | 1.5 MB | 2026-10-28 CNN r6 新混合摆放对照 |
| `2026-10-27-startup-clock-repair` | 2026-10-27 | 70 | 5.4 MB | 2026-10-27 启动竞争与 MMCM 工具修复 |
| `2026-10-27-reboard-status` | 2026-10-27 | 10 | 60 KB | 2026-10-27 重新上板状态检查 |
| `2026-10-27-real-data-layout-02` | 2026-10-27 | 11 | 18 KB | r6 训练必需的第二组 ROI |
| `2026-10-27-product-coexist` | 2026-10-27 | 123 | 20.4 MB | 2026-10-27 共存位流与真实检查链 |
| `2026-10-27-git-integration` | 2026-10-27 | 14 | 33 KB | 2026-10-27 提交前定向检查 |
| `2026-10-27-fresh-board-start` | 2026-10-27 | 54 | 5.7 MB | 2026-10-27 新启动与真实场景模型诊断 |
| `2026-10-27-concurrent-agent-audit` | 2026-10-27 | 43 | 3.4 MB | 2026-10-27 并发会话审计与板端诊断 |
| `2026-10-26-trained-payload` | 2026-10-26 | 16 | 280 KB | 2026-10-26 训练权重导出为 INT8 payload：RTL 仿真 PASS（未上板） |
| `2026-10-26-build` | 2026-10-26 | 25 | 1.2 MB | 2026-10-26 构建线（Agent A）证据 |
| `2026-10-26-board` | 2026-10-26 | 56 | 1.1 MB | 2026-10-26 上板记录：首次硬件 CNN 诊断网 zero/pattern PASS（PROVISIONAL） |
| `2026-10-25-dma16-board` | 2026-10-25 | 15 | 31 KB | 2026-10-25 DMA16 上板：40 MHz 时钟门禁 PASS；CPU 未执行固件（BLOCKED，JL） |
| `2026-10-23-board-bringup` | 2026-10-23 | 18 | 49 KB | 2026-10-23 协处理器首次上板：包/烧写/只读预检（PARTIAL；FCLK/loader 阻塞） |
| `2026-10-22-board-top-sync` | 2026-10-22 | 30 | 43 KB | 2026-10-22 board-top 同步：整机门禁 PASS、bit/hwh 与 Windows 复现性缺口 |
| `2026-10-18-j03-closeout` | 2026-10-18 | 1 | 1 KB | J03 离板收口索引（2026-10-18） |
| `2026-10-17-exe-ring` | 2026-10-17 | 52 | 87 KB | EXE 环接通：PC↔PYNQ 网络上 LIVE 服务全链（2026-10-17） |
| `2026-10-15-improvements-fast` | 2026-10-15 | 57 | 588 KB | 改进建议快速批次：执行与证据（2026-10-15） |
| `2026-10-15-c01-entry-surrogate-step2` | 2026-10-15 | 7 | 18 KB | C01 入口端到端替身（第 2–3 步，2026-10-15） |
| `2026-10-14-n03-return-review` | 2026-10-14 | 31 | 34 KB | N03返板包离板复核 |
| `2026-10-13-ddr-single-frame` | 2026-10-13 | 28 | 25 KB | C01 单帧 DDR 驱动与失败实验（2026-10-13） |
| `2026-10-13-cnn-arithmetic` | 2026-10-13 | 61 | 17.2 MB | CNN 整数计算链离板证据（2026-10-13） |
| `2026-10-12-pr-review` | 2026-10-12 | 38 | 4.0 MB | 2026-10-12 PR #69/#70/#71 审查证据 |
| `2026-10-12-nc-offline` | 2026-10-12 | 36 | 357 KB | 2026-10-12 NC离板续工证据 |
| `2026-10-12-cnn-mac-step1` | 2026-10-12 | 14 | 76 KB | CNN MAC 第一步（2026-10-12） |
| `2026-10-11-c01-capture-rtl` | 2026-10-11 | 251 | 10.9 MB | C01 捕获 RTL / 集成候选证据（2026-10-11） |
| `2026-10-10-offline-inspection` | 2026-10-10 | 48 | 9 KB | 2026-10-10 离板检查验证记录 |
| `2026-10-10-model-reference` | 2026-10-10 | 39 | 19 KB | 2026-10-10 模型逐层参考：原始验证记录 |
| `2026-10-09-exe-hud-v4` | 2026-10-09 | 23 | 884 KB | 2026-10-09 HUD v4（Pillow 文本引擎 + 布局定稿 + 接入产品） |
| `2026-10-07-pi-pynq` | 2026-10-07 | 17 | 2.9 MB | 相机经 PYNQ 黑屏诊断与恢复（2026-10-07） |
| `2026-10-07-partC-postopt` | 2026-10-07 | 48 | 1.4 MB | Part C PC/flush 优化后复验与上板（2026-10-07） |
| `2026-10-07-module1-closure` | 2026-10-07 | 268 | 1.5 MB | 2026-10-07 模块一收口复验 |
| `2026-10-06-vision-sync-schema` | 2026-10-06 | 7 | 10 KB | 2026-10-06 视频/结果同步协议落码证据（schema v1.1 + EXE 轮次叠加） |
| `2026-10-06-partC-verify` | 2026-10-06 | 67 | 1.9 MB | Part C 验证证据（2026-10-06） |
| `2026-10-06-partB-t2-board` | 2026-10-06 | 23 | 403 KB | Part B T2 SoC 构建与上板验证（2026-10-06） |
| `2026-10-05-partB-v1-onboard` | 2026-10-05 | 50 | 2.5 MB | Part B v1（三级流水 + 转发）Windows 复验与上板证据（2026-10-05） |
| `2026-10-05-partB-v1-cycle-breakdown` | 2026-10-05 | 5 | 8 KB | Part B v1 CoreMark 分类周期证据 |
| `2026-10-05-partB-v1-coremark-cpi` | 2026-10-05 | 6 | 16 KB | Part B v1 D3.1b：CoreMark 双档 CPI |
| `2026-10-05-partB-radix4-cycle-breakdown` | 2026-10-05 | 5 | 9 KB | Part B Radix-4 CoreMark 双档实测（2026-10-05） |
| `2026-10-03-vision-onboard` | 2026-10-03 | 26 | 1.7 MB | 模块二上板证据（2026-10-03） |
| `2026-10-03-picorv32-compare` | 2026-10-03 | 25 | 876 KB | PicoRV32 vs 自研 v0 核 Fmax 对比实测（验证线，M4 前置提前完成） |
| `2026-10-02-vision-offboard` | 2026-10-02 | 81 | 2.6 MB | 模块二离板冲刺证据（2026-10-02） |
| `2026-10-01-vision-m2-sprint` | 2026-10-01 | 16 | 105 KB | 2026-10-01-vision-m2-sprint |
| `2026-09-30-scaler-retiming` | 2026-09-30 | 5 | 30 KB | 2026-09-30-scaler-retiming |
| `2026-09-28-partA-closure` | 2026-09-28 | 14 | 209 KB | 2026-09-28-partA-closure |
| `2026-09-26-soc-onboard` | 2026-09-26 | 11 | 267 KB | Part A SoC 上板验证证据（2026-09-26） |
| `2026-09-23-coremark-script-regression` | 2026-09-23 | 6 | 26 KB | CoreMark 脚本接入回归（2026-09-23） |
| `2026-09-23-coremark` | 2026-09-23 | 3 | 4 KB | CoreMark v0（两级核）32 迭代跑分证据 |
| `2026-09-20-pynq-z2-smoke-vivado` | 2026-09-20 | 5 | 45 KB | PYNQ-Z2 LED smoke test 验证证据（2026-09-20） |
| `2026-09-20-fwd-baseline` | 2026-09-20 | 3 | 8 KB | 转发专项 v0 对照基线（2026-09-20） |
| `2026-09-20-arch-test` | 2026-09-20 | 4 | 13 KB | riscv-arch-test 接入证据（2026-09-20） |
<!-- RUN-INDEX:END -->

## 相关入口

- 证据区索引：[`data/evidence/README.md`](../evidence/README.md)
- 指标汇总：[`data/metrics.csv`](../metrics.csv)
- 目录地图与阅读顺序：[`docs/project-map.md`](../../docs/project-map.md)
- 上板记录：[`board/logs/`](../../board/logs/)
