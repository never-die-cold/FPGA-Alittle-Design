# 提交仓库瘦身审查与修复

日期：2026-10-30；基线：`dev/submission-slim@a631fd2`。用户确认本轮快速模式，并授权提交、PR 合并与分支同步；原有未跟踪文档与协作稿保留。发布状态以本次 PR 记录为准。

## 结果

已修复源码构建和模型复现中的实际断链；本轮未修改 RTL、接口语义或已验收镜像。代码文件净减 465 行（含注释/空行，不把模型文本计为代码）；工作区交付内容净减约 11.9 MiB。只补回构建/训练必需输入，删除原件可由基线及 `cd7290e` 恢复。

## 完整性修复

| 问题 | 修复与结果 |
| --- | --- |
| 固件 Makefile 依赖已删源文件 | 原样恢复 `src/riscv_fw/main_v0.c`、`bench_v0_1.c` 共 55 行；从干净目录构建全部固件，7 份 hex 与现有镜像逐字一致。 |
| r6 训练依赖本机缓存与被删 ROI | 补入 `training-start-r3.pt`（145,205 B，匹配原训练指纹），从 `cd7290e` 恢复第二组 9 ROI 和比较 JSON（18,107 B）；只恢复训练必需子集。 |
| 旧 NC 组包清单缺 9 项输入 | 无现役调用，退役 `package_coprocessor_nc.sh`；统一到实际用于 r6 的 `build_board_package.py`，诊断两用例组包及 loader 离板预检通过。 |
| 主 runner 遇到缺失 tb 静默跳过 | 改为立即退出 1；在仓库内副本移开一个现有 tb，确认输出 `ERROR: missing testbench riscv/tb_core_smoke.v`。 |

r6 按原 80 轮参数重新训练，仍选第 70 轮，全部模型状态张量与冻结模型完全相同；重新量化的 36,032 B payload 与冻结原件逐字节相同。此结果证明训练/量化复现，不代替独立识别精度或整机验收。

## 已退役与精简

- 一次性诊断：`sim/scripts/probe_vivado_project_init.tcl`、`prepare_pi_password_reset.py`、`cop_runtime_snapshot.py`、`cop_register_sweep.py`、`cop_slcr_status.py`、`report_capture_bus_skew.tcl`。
- 重复入口：`build/build_cop.tcl` 统一到 `build/build_coprocessor_gate.tcl`；NC 专用组包统一到通用组包器，历史指标保留原脚本提交锚点。
- 元测试：移除 `sim/vision/test_c01_capture_ordering.py` 及 runner 条目；`test_c01_capture.py` 的真实寄存器顺序与故障恢复测试仍保留，视觉 Python 当前 19 组。
- HOG 支线：删除专用训练器和约 7.64 MiB 模型，去掉两个共享评估/训练入口的 HOG 分支；CNN 分支及其调用参数保留。
- 请求解析移入 `vision_protocol.py`，生产 LIVE 服务解除对 mock 模块的依赖；删除 mock 主程序重复的第二次 `serve_forever()`。
- 协处理器 runner 每次调用只生成一次所需算术/整网/参数包；独立 pipeline 与 manifest 模式仍可运行。删除已过期的大文件例外，卫生检查不再把工作树已删文件算作重复副本。
- 删除 7 张逐字节相同的训练编号图，共 4,625,790 B；保留原件、README 链接和 manifest 的去重映射。ROI、原帧、比较 JSON、标签和训练输入不变。

没有新增测试或门禁脚本。现役数值对拍、流水线冒险、AXI/CDC/DMA、超时和工单去重测试保留。HTTP `reply()`、DMA CRC、模型装载校验和结果序号具有运行语义；逐轮产物协议未作破坏性裁剪。

## 文档同步

- 根 README、核/固件/视觉/CNN/板端 README：修正基线拍序、PS 定位职责、实际集成顶层与存储、实板状态入口、Python 组数及 dis 生成物政策。
- 训练手册改为当前训练/量化/组包入口，Pi 手册去掉 R1–R4 分工、过期排期和 EXE 命令；不再复制主计划的状态指标。
- 协处理器交接单移除已退役命令；仓库卫生手册去掉已删生成器，修正实际构建输出路径；新增模型/结果目录说明。
- 旧技术报告与海报明确标为历史版，保留当时的数据和图片；当前状态统一引用 `plan.md §3.1`。用户正在制作的未跟踪 LaTeX/音频文档没有改动。
- 日志与证据索引随最小输入恢复、去重及接收清单说明更新；旧接收 CSV 原样保留，不作为当前文件树清单。

## 验证命令与原始结果

| 入口 | 原始结果 |
| --- | --- |
| 基线 `bash sim/scripts/run_iverilog.sh all` | `ALL_EXIT=0`；四档 CoreMark cycles 为 19057438 / 17114141 / 16335562 / 16232079，retired 均 10106386。 |
| 改后 `bash sim/scripts/run_coprocessor_iverilog.sh all` | `POST_COP_EXIT=0`；两组整网各 73,795 元素逐项匹配。 |
| 改后 `run_vision_python.sh` / `run_inspection_python.sh` / `run_coprocessor_python.sh` | 19 / 17 / 10 组全部退出 0。 |
| `bash sim/scripts/run_iverilog.sh coprocessor pipeline`；`run_coprocessor_iverilog.sh manifest_v1`；`run_iverilog.sh soc` | 独立模式均退出 0；SoC 首跑 13/1101，软复位后 65/0001。 |
| `mingw32-make -B -C <仓库内干净固件目录> PYTHON=python all` | `FIRMWARE_REBUILD_EXIT=0`；7 份 `SAME_WORDS=True`。 |
| [r6 包内训练与 PTQ 命令](../data/evidence/2026-10-28-cnn-r6/README.md) | `R6_TRAIN_EXIT=0; R6_ALL_STATE_TENSORS_EQUAL=True; SELECTED_EPOCH=70; R6_PTQ_EXIT=0; R6_PAYLOAD_BYTES_EQUAL=True`。 |
| `build_board_package.py` + `cop_payload_loader.preflight` | `PACKAGE_BUILD_EXIT=0; PACKAGE_PREFLIGHT_PASS=pattern,zero`，离板夹具，无板端操作。 |
| `restore_snapshot.py --run <现有快照目录> --check --json` | 5 组退出 0；389 个移出文件的恢复源均无问题。 |
| `iverilog -g2001 -tnull -s <top> <对应 RTL>` | core_top / vision_top / cnn_sequencer / pynq_cop_top 四项退出 0；RTL 此后未改动。 |
| `python sim/scripts/check_repo_hygiene.py --json`；`index_runs.py --check`；`git diff --check` | 卫生检查 0 errors；索引 OK；diff 检查退出 0。 |

原始输出留在 `sim/build/submission-audit/`，验证导出的副本与生成包在结束后清理；复验使用仓库现有入口和已恢复输入。基线全量与修改后专项分别记录，不把旧快照回归写成改后再次跑完全量。

## 保留边界

剩余重复主要为不同历史记录的截图、独立文档资产和冻结构建输入；未破坏这些记录的绑定关系。散落退出码仍有汇总器消费，未一并删除。LLM 记录约 1 MiB，保留既有内容，没有新增协作会话日志。
未实现/未验收：网页端真实数据接线、独立实物精度、工业整机验收、逐帧精确关联、结果 DMA 与任意描述符表，仍按主计划和契约标注。本轮没有新增 Vivado/XSim/arch-test 或实板验收结论。
