# data/logs —— 运行记录索引

> 给谁看：查一次仿真、构建、上板或代码审查原始证据的人。
> 规则：一次运行一个目录；目录名 `YYYY-MM-DD-topic`；每个目录必须有 `README.md`。
> 模板：[`_template/README.md`](_template/README.md)。新增目录后运行 `python sim/scripts/index_runs.py --write` 刷新本索引。

## 硬规则

1. 原始日志只追加，不改写；需要更正时新加一条记录。
2. 每个目录的 `README.md` 至少写：日期、commit、命令、结果、产物、边界/未完成项。
3. 证据分级：**A** 被 `data/metrics.csv` 或 `report/` 引用；**B** 支撑结论但未直接引用；**C** 过程/尝试/草稿。
4. 源码或输入快照由 `SNAPSHOT-MANIFEST.json` + `SNAPSHOT.md` 管理；能由 Git blob 恢复的副本不再重复存放。
5. 恢复快照：`python sim/scripts/restore_snapshot.py --run <目录> --check`，需要写回时加 `--restore`。
6. 目录里不要放 `.vvp`、`.dcp`、`__pycache__`、Vivado 工程缓存；这些是生成物。
7. 当前目录缺 README 的标记为 `PROVENANCE GAP`；补说明时只写能核实的事实，未知处写“待核”。

<!-- RUN-INDEX:START -->
## 目录索引（121 个运行，自动生成）

| 目录 | 日期 | 文件数 | 大小 | 说明 |
|:---|:---:|---:|---:|:---|
| `v0_baseline_2026-09-14` | — | 3 | 9 KB | v0 核回归基线（2026-09-14） |
| `local-vivado-originals` | — | 7 | 449 KB | local-vivado-originals |
| `cnn-ooc-da63cadcd3db4a9e9f826cf2e4949e68` | — | 15 | 827 KB | cnn-ooc-da63cadcd3db4a9e9f826cf2e4949e68 |
| `cnn-ooc-a96a8b86f6264e50af90da61e3dc3aa9` | — | 12 | 791 KB | cnn-ooc-a96a8b86f6264e50af90da61e3dc3aa9 |
| `cnn-ooc-5c9bc74c61e7445ca8c56b2f49389102` | — | 14 | 1.1 MB | cnn-ooc-5c9bc74c61e7445ca8c56b2f49389102 |
| `cnn-ooc-4065cdcc415b43fbbc713dbeeceddbfb` | — | 14 | 1.0 MB | cnn-ooc-4065cdcc415b43fbbc713dbeeceddbfb |
| `cnn-ooc-1cefffc05185438195b8803d87fc11df` | — | 13 | 797 KB | cnn-ooc-1cefffc05185438195b8803d87fc11df |
| `cnn-ooc-106904d01e0045089b9d1688ddce6e85` | — | 10 | 27 KB | cnn-ooc-106904d01e0045089b9d1688ddce6e85 |
| `c01-capture-e2a602d6e0da49a2b6da072abca47c70` | — | 82 | 3.3 MB | c01-capture-e2a602d6e0da49a2b6da072abca47c70 |
| `c01-capture-19af0b2c829447b89d442a6f4f09f8f3` | — | 78 | 2.7 MB | c01-capture-19af0b2c829447b89d442a6f4f09f8f3 |
| `2026-10-21-cop-a2-round` | 2026-10-21 | 97 | 647 KB | 2026-10-21 COP_SIM A1/A2：消费握手、一轮与异常矩阵 |
| `2026-10-21-board-gate-sync` | 2026-10-21 | 21 | 32 KB | 2026-10-21 board-gate 同步：K4/K5、固件 E2E 与真接口控制面 |
| `2026-10-20-repo-hygiene` | 2026-10-20 | 5 | 9 KB | 根目录生成物归位与卫生检查修复 |
| `2026-10-20-pr-merge-sync` | 2026-10-20 | 9 | 134 KB | PR #86 合并前验证与三人分支同步 |
| `2026-10-20-cop-sim-round` | 2026-10-20 | 91 | 642 KB | 2026-10-20 COP_SIM：服务 + EXE 一轮与异常矩阵 |
| `2026-10-19-worktree-inventory` | 2026-10-19 | 33 | 6.4 MB | Worktree 与大缓存清理前抢救记录（2026-10-19） |
| `2026-10-19-j04-closeout` | 2026-10-19 | 20 | 124 KB | J04 离板冒烟证据（JL Linux + Windows 复跑） |
| `2026-10-19-deepseek-independent-review` | 2026-10-19 | 7 | 4 KB | DeepSeek 工作结果独立轻量核查 |
| `2026-10-19-cop-synth` | 2026-10-19 | 3 | 396 KB | cop_top OOC 综合与实现（2026-10-19） |
| `2026-10-18-j03-closeout` | 2026-10-18 | 1 | 1 KB | J03 离板收口索引（2026-10-18） |
| `2026-10-17-exe-scope-redesign` | 2026-10-17 | 7 | 853 KB | EXE 识别范围表改版：交互设计与两轮布局评审（2026-10-17） |
| `2026-10-17-exe-ring` | 2026-10-17 | 52 | 87 KB | EXE 环接通：PC↔PYNQ 网络上 LIVE 服务全链（2026-10-17） |
| `2026-10-16-c01-park-first-board` | 2026-10-16 | 73 | 1.4 MB | C01 park 驱动暖机清除与保护复制：首次板端打通（2026-10-16） |
| `2026-10-15-onboard-n02-n03` | 2026-10-15 | 98 | 5.9 MB | 2026-10-15-onboard-n02-n03 |
| `2026-10-15-n03-package-independent-verify` | 2026-10-15 | 13 | 26 KB | N03 实验包：离板 SHA256 / 配对独立复核（2026-10-15） |
| `2026-10-15-improvements-fast` | 2026-10-15 | 56 | 586 KB | 改进建议快速批次：执行与证据（2026-10-15） |
| `2026-10-15-cnn-watchdog-step2` | 2026-10-15 | 23 | 101 KB | CNN watchdog 最后周期锁存（2026-10-15） |
| `2026-10-15-cnn-geometry-step1` | 2026-10-15 | 22 | 131 KB | CNN 输出尺寸位宽优化：第 1 步（2026-10-15） |
| `2026-10-15-cnn-geometry-independent-review` | 2026-10-15 | 16 | 9 KB | CNN 输出尺寸位宽优化（第 1 步）：独立复核（2026-10-15） |
| `2026-10-15-cnn-fast-batch-independent-verify` | 2026-10-15 | 41 | 9 KB | 快速批次 CNN/视觉声明：第二人独立复核（2026-10-15） |
| `2026-10-15-c01-idle-sticky-step1` | 2026-10-15 | 9 | 22 KB | C01 停机期粘滞错误位：含桩覆盖（第 1 步，2026-10-15） |
| `2026-10-15-c01-entry-surrogate-step2` | 2026-10-15 | 7 | 18 KB | C01 入口端到端替身（第 2–3 步，2026-10-15） |
| `2026-10-15-c01-direct-capture-stage` | 2026-10-15 | 19 | 1.1 MB | C01 capture 阶段直接诊断与停机 SR 位语义实测定性（2026-10-15 深夜） |
| `2026-10-15-board-start` | 2026-10-15 | 38 | 1.1 MB | 2026-10-15 返板起点：N01 与视频短基线 |
| `2026-10-14-nc-push` | 2026-10-14 | 20 | 150 KB | NC离板交付提交与推送 |
| `2026-10-14-nc-offboard-closeout` | 2026-10-14 | 30 | 361 KB | NC扩展离板交付与Windows候选验收 |
| `2026-10-14-n03-return-review` | 2026-10-14 | 31 | 34 KB | N03返板包离板复核 |
| `2026-10-14-c04-nc-review` | 2026-10-14 | 26 | 28 KB | C04 NC离板复核证据 |
| `2026-10-13-soc-reset-ce` | 2026-10-13 | 186 | 1.3 MB | 2026-10-13 SoC 复位/CE 物理代价修复：mem_wb_stage 分离复位 |
| `2026-10-13-ddr-single-frame` | 2026-10-13 | 28 | 25 KB | C01 单帧 DDR 驱动与失败实验（2026-10-13） |
| `2026-10-13-cnn-arithmetic` | 2026-10-13 | 56 | 2.5 MB | CNN 整数计算链离板证据（2026-10-13） |
| `2026-10-13-branch-merge` | 2026-10-13 | 9 | 133 KB | 三分支 PR 合并与合并后回归（2026-10-13） |
| `2026-10-12-unattended-offline` | 2026-10-12 | 48 | 3.6 MB | 用户离开期间的离板续工证据 |
| `2026-10-12-source-recovery-prep` | 2026-10-12 | 18 | 1.5 MB | N02：采集卡连接时 Pi 软件重启断源/恢复（2026-10-12） |
| `2026-10-12-real-frame-prototype` | 2026-10-12 | 18 | 5.3 MB | PYNQ 测试原图的电脑软件诊断（2026-10-12） |
| `2026-10-12-pr-review` | 2026-10-12 | 38 | 4.0 MB | 2026-10-12 PR #69/#70/#71 审查证据 |
| `2026-10-12-nc-offline` | 2026-10-12 | 33 | 353 KB | 2026-10-12 NC离板续工证据 |
| `2026-10-12-n03-base-return` | 2026-10-12 | 34 | 8.1 MB | N03 base 取帧与显示共存短诊断（2026-10-12） |
| `2026-10-12-n02-extended` | 2026-10-12 | 54 | 6.5 MB | N02 原 vision 分段观察与重载（2026-10-12） |
| `2026-10-12-document-audit` | 2026-10-12 | 5 | 6 KB | 2026-10-12 文档/实现核对证据 |
| `2026-10-12-collection-readiness` | 2026-10-12 | 29 | 105 KB | 采集规程与模板同步证据 |
| `2026-10-12-cnn-mac-step1` | 2026-10-12 | 14 | 75 KB | CNN MAC 第一步（2026-10-12） |
| `2026-10-12-board-connect` | 2026-10-12 | 37 | 895 KB | 2026-10-12 板卡连接与原 vision 短基线 |
| `2026-10-11-onboard-resume` | 2026-10-11 | 81 | 2.9 MB | 2026-10-11 现场续工记录 |
| `2026-10-11-n03-buffer-guard` | 2026-10-11 | 53 | 6.9 MB | N03 缓冲保护与 C01 接手进展 |
| `2026-10-11-c01-probe-evidence` | 2026-10-11 | 19 | 673 KB | C01 stream_seq 疑点实测闭环（2026-10-11 23:00–23:11） |
| `2026-10-11-c01-hdmi-1791713720540454` | 2026-10-11 | 6 | 480 KB | 2026-10-11-c01-hdmi-1791713720540454 |
| `2026-10-11-c01-hdmi-1791711069004993` | 2026-10-11 | 5 | 373 KB | 2026-10-11-c01-hdmi-1791711069004993 |
| `2026-10-11-c01-hdmi-1791710185764742` | 2026-10-11 | 5 | 373 KB | 2026-10-11-c01-hdmi-1791710185764742 |
| `2026-10-11-c01-capture-rtl` | 2026-10-11 | 245 | 7.1 MB | C01 捕获 RTL / 集成候选证据（2026-10-11） |
| `2026-10-11-c01-capture-probe` | 2026-10-11 | 27 | 506 KB | 2026-10-11-c01-capture-probe |
| `2026-10-10-q01-result-fields` | 2026-10-10 | 16 | 6 KB | Q01 结果字段白名单复验 |
| `2026-10-10-onboard-n01` | 2026-10-10 | 89 | 3.7 MB | 上板 N01：现场版本与连接盘点 |
| `2026-10-10-offline-inspection` | 2026-10-10 | 48 | 9 KB | 2026-10-10 离板检查验证记录 |
| `2026-10-10-model-reference` | 2026-10-10 | 39 | 19 KB | 2026-10-10 模型逐层参考：原始验证记录 |
| `2026-10-10-merge-check` | 2026-10-10 | 3 | 20 KB | 2026-10-10 云端融合拉取与本机复验 |
| `2026-10-10-dataset-integration` | 2026-10-10 | 7 | 7 KB | 数据审计与远端协议整合复验 |
| `2026-10-10-dataset-audit` | 2026-10-10 | 36 | 18 KB | 数据集审计：原始验证记录 |
| `2026-10-10-branch-integration` | 2026-10-10 | 9 | 2 KB | 2026-10-10 分支集成复验 |
| `2026-10-09-module1-2-closeout` | 2026-10-09 | 163 | 3.0 MB | 2026-10-09 模块一／二文档收口复跑证据 |
| `2026-10-09-exe-hud-v4` | 2026-10-09 | 23 | 884 KB | 2026-10-09 HUD v4（Pillow 文本引擎 + 布局定稿 + 接入产品） |
| `2026-10-09-exe-hud-implementation` | 2026-10-09 | 26 | 925 KB | 2026-10-09 EXE HUD v3 实装（preview.py 绘制层重写） |
| `2026-10-09-exe-export-cjk` | 2026-10-09 | 12 | 51 KB | 2026-10-09 EXE 自主推进批次：CSV 记录导出 + 中文渲染能力（M3 预置） |
| `2026-10-09-collaboration-summary` | 2026-10-09 | 19 | 99 KB | 2026-10-09 分模块协作记录来源与分支转移证据 |
| `2026-10-08-exe-ui-design` | 2026-10-08 | 5 | 220 KB | EXE HUD 设计提案（2026-10-08，草案待评审，未提交） |
| `2026-10-08-exe-rounds` | 2026-10-08 | 9 | 11 KB | 2026-10-08 EXE 轮次叠加：bbox 半开对齐 + 状态机抽离与撤框/断联测试 |
| `2026-10-08-exe-records` | 2026-10-08 | 9 | 11 KB | 2026-10-08 EXE 批次记录（D8–D10）离板实现与验证 |
| `2026-10-08-exe-anomalies` | 2026-10-08 | 18 | 142 KB | 2026-10-08 EXE 批次记录加固：采纳点语义修复 + 异常事件日志（D11） |
| `2026-10-08-branch-consolidation` | 2026-10-08 | 8 | 1 KB | bench 合入与分支整理复验 |
| `2026-10-07-pi-pynq` | 2026-10-07 | 17 | 2.9 MB | 相机经 PYNQ 黑屏诊断与恢复（2026-10-07） |
| `2026-10-07-partC-postopt` | 2026-10-07 | 48 | 1.4 MB | Part C PC/flush 优化后复验与上板（2026-10-07） |
| `2026-10-07-module1-closure` | 2026-10-07 | 268 | 1.5 MB | 2026-10-07 模块一收口复验 |
| `2026-10-07-hdmi-diagnostic` | 2026-10-07 | 1 | 664 B | 2026-10-07-hdmi-diagnostic |
| `2026-10-06-vision-sync-schema` | 2026-10-06 | 7 | 10 KB | 2026-10-06 视频/结果同步协议落码证据（schema v1.1 + EXE 轮次叠加） |
| `2026-10-06-pi-pynq` | 2026-10-06 | 9 | 7 KB | 树莓派相机经 PYNQ 的实机检查（2026-10-06） |
| `2026-10-06-pi-boot` | 2026-10-06 | 95 | 817 KB | Raspberry Pi 4B 启动诊断（2026-10-06） |
| `2026-10-06-partC-verify` | 2026-10-06 | 67 | 1.9 MB | Part C 验证证据（2026-10-06） |
| `2026-10-06-partC-pc-depth` | 2026-10-06 | 18 | 246 KB | 保持三级的 Part C PC/flush 优化证据 |
| `2026-10-06-partC-iverilog` | 2026-10-06 | 5 | 16 KB | Part C 四档 iverilog 回归（2026-10-06） |
| `2026-10-06-partC-archtest` | 2026-10-06 | 13 | 34 KB | Part C 四档 arch-test 回归（2026-10-06） |
| `2026-10-06-partB-t2-fmax` | 2026-10-06 | 15 | 536 KB | Part B T2 核 OOC Fmax 复测（2026-10-06） |
| `2026-10-06-partB-t2-board` | 2026-10-06 | 23 | 403 KB | Part B T2 SoC 构建与上板验证（2026-10-06） |
| `2026-10-05-partB-v1-onboard` | 2026-10-05 | 50 | 2.5 MB | Part B v1（三级流水 + 转发）Windows 复验与上板证据（2026-10-05） |
| `2026-10-05-partB-v1-cycle-breakdown` | 2026-10-05 | 5 | 8 KB | Part B v1 CoreMark 分类周期证据 |
| `2026-10-05-partB-v1-cpi` | 2026-10-05 | 6 | 147 KB | Part B v1 D3.1a：退休/CPI 口径自检 |
| `2026-10-05-partB-v1-coremark-cpi` | 2026-10-05 | 6 | 16 KB | Part B v1 D3.1b：CoreMark 双档 CPI |
| `2026-10-05-partB-v1-arch-test` | 2026-10-05 | 11 | 16 KB | Part B v1 arch-test 转发双档证据（2026-10-05） |
| `2026-10-05-partB-radix4-cycle-breakdown` | 2026-10-05 | 5 | 9 KB | Part B Radix-4 CoreMark 双档实测（2026-10-05） |
| `2026-10-05-partB-radix4-arch-test` | 2026-10-05 | 12 | 18 KB | Part B Radix-4 功能回归（2026-10-05） |
| `2026-10-04-partB-v1` | 2026-10-04 | 17 | 353 KB | 2026-10-04-partB-v1 |
| `2026-10-04-fix-implicit-ports` | 2026-10-04 | 8 | 84 KB | ID+EX 隐式端口修复验证 |
| `2026-10-03-vision-onboard` | 2026-10-03 | 26 | 1.7 MB | 模块二上板证据（2026-10-03） |
| `2026-10-03-picorv32-compare` | 2026-10-03 | 25 | 876 KB | PicoRV32 vs 自研 v0 核 Fmax 对比实测（验证线，M4 前置提前完成） |
| `2026-10-03-m3-brevitas-drill` | 2026-10-03 | 4 | 9 KB | 2026-10-03-m3-brevitas-drill |
| `2026-10-03-arm-localize-baseline` | 2026-10-03 | 35 | 11 KB | 2026-10-03-arm-localize-baseline |
| `2026-10-02-vision-offboard` | 2026-10-02 | 72 | 2.6 MB | 模块二离板冲刺证据（2026-10-02） |
| `2026-10-01-vision-offboard` | 2026-10-01 | 3 | 7 KB | 模块二跨分支离板复验（2026-10-01） |
| `2026-10-01-vision-m2-sprint` | 2026-10-01 | 16 | 105 KB | 2026-10-01-vision-m2-sprint |
| `2026-09-30-scaler-retiming` | 2026-09-30 | 5 | 30 KB | 2026-09-30-scaler-retiming |
| `2026-09-30-r2r5-verify` | 2026-09-30 | 2 | 40 KB | 2026-09-30 R2–R5 独立复验（dev/rtl 522e819） |
| `2026-09-30-m3-train-drill` | 2026-09-30 | 4 | 10 KB | 2026-09-30-m3-train-drill |
| `2026-09-30-branch-sync` | 2026-09-30 | 3 | 41 KB | 2026-09-30 分支同步回归 |
| `2026-09-29-vision-m2-kickoff` | 2026-09-29 | 34 | 215 KB | 2026-09-29 模块二开工：rgb2gray / line_buffer / gaussian_3x3 单元回归 |
| `2026-09-29-r1-verify` | 2026-09-29 | 2 | 24 KB | 2026-09-29 R1 独立复验（dev/rtl fe80857） |
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
