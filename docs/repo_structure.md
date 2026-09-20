# 仓库结构说明（每个文件夹要做什么）

> 对齐赛题指南 §3.3.5.4（AMD 自主选题赛道推荐结构，非强制 + 本表即对照说明）。
> 本文是"逐文件夹职责 + 当前状态 + 后续填充计划"的导航手册；一图流版本见根 `README.md` 目录树。
> 结构整理决策记录：`report/llm_log/2026-09-14-restructure-official-layout.md`。

---

## 根目录（官方允许：README + LICENSE；其余为基础设施）

| 文件/目录 | 要做什么 |
|:---|:---|
| `README.md` | 仓库门面 + **复现步骤入口**（指南提交物要求）：项目定位、三大模块、目录对照表、开发计划、降级策略、环境与工具链链接 |
| `LICENSE` | MIT 开源协议——满足指南"强烈要求开源、推荐 MIT/Apache-2.0" |
| `.gitignore` | 忽略编译/仿真产物（`*.elf/*.bin/*.o`、Vivado、iverilog）；**`*.hex/*.coe` 明确不入忽略**（BRAM 预载与测试向量必须入库） |
| `.github/ISSUE_TEMPLATE/` | `bug_report.md`（现象/复现/期望/日志）、`task.md`（任务待办）——所有跟踪走 GitHub Issue |

## src/ —— 设计源码（指南定义：RTL / HLS / PS 侧软件全在此）

| 子目录 | 现状 | 要做什么 |
|:---|:---|:---|
| `src/riscv/` | ✅ 已开工 | **模块一核心**：自研 RISC-V 核 RTL。`plan.md` 排期与学习路线、`design_v0.md` 接口契约（唯一权威）、`pc/regfile/alu/decode/if_stage/core_top.v` 六个模块（v0 两级流水已仿真 PASS）。后续：Part B 三级+转发（9/28–10/1）、Part C 分支预测（10/2–10/4）、M 扩展 `muldiv.v` 与最小 SoC 外壳收尾（原 `src/soc/` 已并入本目录） |
| `src/riscv_fw/` | ✅ 已开工 | 跑在自研核上的**裸机固件**：统一工具链权威文档（MSYS2 riscv32-unknown-elf）、Makefile 三目标（RV32IM 冒烟 / RV32I v0 冒烟 / 38 用例逐指令自检）、start.S/link.ld/bin2hex.py、三套 dis+hex 证据。后续：benchmark（Part C）、协处理器驱动 |
| `src/vision/` | 🚧 占位 | **模块二**：HDMI 预处理流水线 RTL（rgb2gray→gaussian→scaler→sobel、行缓存、AXI-Lite 参数寄存器、OSD）。M2 开工；演示层任务（参数化直通、直通 vs 帧缓存对比）见 `docs/proposal_upgrade.md` |
| `src/coprocessor/` | 🚧 占位 | **模块三**：CNN 推理协处理器（INT8 MAC 阵列、DMA、自定义指令译码）。M2 开工；算子化验证（CONV/POOL/GEMM 加速比表）+ 软硬切换；L2 降级时可整体裁剪 |
| ~~`src/soc/`~~ | 已并入 | **SoC 外壳**已合并进 `src/riscv/`（顶层、总线互连、地址映射表）；`addr_map.md` 定稿后 `src/riscv_fw` 与 `src/pynq_host` 以此为准。M1 起步、M3 完成集成 |
| `src/pynq_host/` | 🚧 占位 | **PS 侧上位机**：Jupyter 控制面板（实时调参、软/硬推理一键切换、指标实时曲线——命题升级 A 档演示形态）。M2/M3 |

## sim/ —— 仿真与验证（铁律：所有 RTL 先过仿真再上板）

| 内容 | 现状 | 要做什么 |
|:---|:---|:---|
| `sim/README.md` | ✅ | 仿真工具约定：过渡期 iverilog 13.0（Vivado 未装），到货后 XSim 跑同一套 tb 复核 |
| `sim/riscv/tb_core_smoke.v` | ✅ | 程序级冒烟：加载 `../src/riscv_fw/hello_v0.hex`，查 `tohost==13 && tohost_exit==0` |
| `sim/riscv/tb_core_test.v` | ✅ | 逐指令自检：加载 `hello_test.hex`，RV32I 38 用例全过才算 PASS |
| `sim/scripts/run_iverilog.sh` | ✅ | 一键仿真入口（自动定位 iverilog、防 DLL 冲突、编译 + 逐 tb 运行）——**回归基线命令** |
| `sim/coprocessor/`、`sim/vision/` | 🚧 待建 | 各模块与整核联调 tb（M2/M3）；SoC 外壳联调 tb 放 `sim/riscv/`；testbench 一律输出 PASS/FAIL，禁止肉眼看波形 |

## build/ —— 构建产物（指南：可复现构建脚本 + 综合与实现报告）

- 现状：`README.md` 占位。
- 要做什么：Vivado 工程 tcl（可从零复现）、综合/实现报告（Fmax/WNS/资源）、`.bit/.xsa` 归档策略；issue #2（Vivado 2026.1）装好后第一件事就是把 v0 核的综合脚本与报告放进来，支撑 Part A 的 Fmax 基线数据。

## board/ —— 上板工程与实测输出（指南同名目录）

- 现状：`README.md` 占位；PYNQ-Z2 已于 2026-09-20 到货并完成上板验证（全队共用 1 块），上板工程、运行脚本与实测日志待填充。
- 要做什么：上板工程、一键运行脚本、实测输出日志（**只追加不删改**，按日期归档）；每条记录含日期/硬件连接/bitstream 版本（commit hash）/结果——实测数据是评分硬依据。

## data/ —— 测试数据与参考结果（原顶层 `metrics/` 已并入）

| 内容 | 要做什么 |
|:---|:---|
| `metrics.csv` | 指标汇总表（唯一权威）：CPI、Fmax/WNS、预处理延迟、直通 vs 帧缓存对比、端到端帧延迟、动效帧率、推理加速比、资源占用；M3 起填充 |
| `logs/` | 原始日志（延迟分位数、闭环成功率），只追加 |
| `scripts/` | 可重跑的测试/采集脚本（提交环境可复现） |
| `evidence/` | 波形、示波器、逻辑分析仪截图 |
| `images/`、`models/`、`golden/` | 测试图样、INT8 权重、软件黄金参考输出（规划） |

铁律：先测基线再谈优化；测量条件必填（器件/精度/输入规格/软件版本/时钟/功耗模式）；报告数据必须能追溯到这里。

## skill/ —— 技能包（评分加分项：大模型协作沉淀）

- 要做什么：把协作过程中沉淀的经验提炼成**换题换板仍可复用**的条目，每条写明适用场景/使用方法/已验证效果/失效条件/来源 llm_log。
- 已收录：`understand-gate/SKILL.md`（入库理解门槛：AI 代码 commit 前逐段讲解 + 3 道理解测试题）。
- 规划：PYNQ Overlay 范式、仿真—上板一致性清单、指标自动采集脚本、时序瓶颈提示词工作流；每周从 `#skill候选` 提炼。

## report/ —— 设计报告 + 大模型协作记录（指南同名目录）

| 内容 | 要做什么 |
|:---|:---|
| `llm_log/` | **评委要看的"纠错轨迹"**：一条 = 一个设计决策点（提示词→首版→失败→纠错→结论→经验）。已有 21 条真实记录；铁律：别造假别后补，commit 是锚点，历史条目中的旧路径不改写 |
| `README.md` + `template.md` | 记录规范与六段模板 |
| 后续 | M4 阶段在此产出正式设计报告（选题背景/架构/优化对比表/协作记录/复现说明） |

## docs/ —— 非强制扩展目录（指南未列，README 对照表已登记豁免理由）

集中放"过程文档"（不属于作品结构七目录、但团队运转必需）：

| 文件 | 要做什么 |
|:---|:---|
| `onboarding.md` | 新队友上手：Git/Markdown/Agent 使用与 Issue 纪律 |
| `prep_checklist.md` | 开工前准备清单（🔴卡脖子项进度、🟡建议、🟢加分） |
| `code_review_checklist.md` | 理解门槛检查单（跨 agent 通用版，与 `skill/understand-gate` 配套） |
| `exam_prep.md` | 决赛 Verilog 上机备考（2019–2025 真题打法 + 进度表） |
| `resources.md` | 分类资料清单（11 节 40+ 链接） |
| `amd_track_awards.md` | 往届 AMD 赛道获奖作品与赛制调研 |
| `track_guides_2026_summary.md` | 2026 全部 7 企业 24 选题指南摘要 |
| `proposal_upgrade.md` | 命题升级方案（A/B/C 阶梯、借鉴映射、演示剧本、红线） |
| `idea1.md` | EdgePilot 扩展方案（L4 云台伺服蓝图） |
| `git_learning/` | 队友 Git 学习笔记（从根目录合规移入的历史记录） |
