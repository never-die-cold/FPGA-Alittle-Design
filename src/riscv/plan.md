# RISC-V 核专项计划：Part A/B/C 与验收

> 更新日期：2026-09-30。本文件只管理 RISC-V 核及其最小 SoC 的技术任务。
> 全项目产品、分工和收口日期见根目录 [项目主计划](../../plan.md)；本模块对应 M1，核任务见 [核交付看板](plan_calendar.md)。
> v0 接口以 [design_v0.md](design_v0.md) 为准，Part B/C 以 [design_v1.md](design_v1.md) 为准。

## §1 模块目标与范围

- Part A：两级 RV32IM 基线核、最小 SoC、仿真与上板基线，已收口。
- Part B：三级流水、转发与冒险控制，完成核集成和功能一致性验证。
- Part C：可切换分支预测、冲刷与四档对比，形成可复现功能/性能证据。
- M1 收口日期只在 [主计划 §1.2](../../plan.md#12-收口时间总览) 定义；提前交付不能降低验收要求。
- CNN、视觉定位、EXE 与工业应用属于其他工作包，本文件仅维护核侧必要的集成依赖。

## §2 核职责与交接

| 成员 | 核侧职责 |
|:---|:---|
| jianglibo | RTL 实现、模块自测、核集成与缺陷修复 |
| never-die-cold | 专项 tb、波形、全量回归、综合与独立复验 |
| watercopper | arch-test、benchmark、四档指标、日志与验收材料 |

RTL 可独立自测后交付配置和已知问题，验证线复验并反馈缺陷；修复后复跑、归档，再完成 M1 验收。全项目分支与 PR 规矩见 [主计划 §2](../../plan.md)。

## §3 已完成部分归档与当前起点

> 2026-09-23：阶段 0、第一阶段任务（9/14–9/24）与 Part A（v0 基线核）的原文与完成证据移入 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)；本节只做索引与当前起点说明，不再重复维护已完成内容。

### 3.1 归档索引（原章节 → 归档位置）

| 原 plan.md | 内容 | 归档位置 |
|:---|:---|:---|
| §1.3 | 现状盘点（9/14 快照） | done/ §E |
| §3.1–3.6 | 第一阶段任务分配与出口检查表 | done/ §C |
| §4.1 | Part A：两级流水基线核 v0 范围 / 交付物 / 验收 | done/ §D |
| §5 阶段 0–1 | 公共基础与 Part A 学习路线 | done/ §B |

### 3.2 当前起点与遗留项

**v0 基线现状**

- 核：v0 六模块两级流水 + 冒烟 / 逐指令 tb（38 用例）；RV32M `muldiv` 已在 `dev/rtl` 实现并通过 RV32IM 整核冒烟（已随 PR #32 合并，2026-09-23）
- 基线数据：Fmax 83.8 MHz / WNS -1.935 ns、LUT 1606 / FF 401 / BRAM 0 / DSP 0（2026-09-28 Vivado 2026.1 重综合，xc7z020clg400-1，10 ns 约束 OOC）
- 回归口径：`sim/scripts/run_iverilog.sh`（含 `soc`/`soc_check`/`bench`/`coremark`/`all`）；arch-test `add-01/addi-01/and-01` PASS

**遗留项（收口前必须处理，详见归档 §G）**

- [x] 最小 SoC 外壳仿真 + 上板冒烟（基线 `db9fe33` 已上板；2026-09-28 新修订只完成仿真/实现，M3 再上板）
- [x] 存储扩容 32KB（8B/8C/9A/9B 已合入）；[x] SoC 计时计数器与 DMEM 镜像预载（RTL、端到端仿真、40 MHz 实现通过）
- [x] 基线 CPI、CoreMark/LUT 与 SoC 资源补录 `data/metrics.csv`
- [x] `dev/rtl` Part A 分支 PR 合并（PR #32，2026-09-23；原计划 9/27 周合并）
- [ ] gate #19 复核签字（9/27）
- [x] benchmark v0.1 / CPI harness / v0 metrics 入档；[ ] CoreMark 四档对比待 Part B/C 完成后补齐

### 3.3 引用兼容说明

历史阶段内容见归档；本文件保留 §3.2 与 §4.1 等核专项入口，避免已有核验收引用断链。全项目产品、人员和收口内容已迁移至根目录主计划。

---

## §4 各 Part 技术内容与验收

<details>
<summary>展开模块一技术范围、交付清单与验收标准</summary>

### 4.1 Part A：两级流水基线核 v0（✅ 已完成，已归档）

范围、交付物和完成证据见 [Part A 归档](done/m1-first-phase-completed.md)；遗留项见 §3.2，复核签字由 [#19 Part A 验收检查点](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/19) 跟踪。

### 4.2 Part B：三级流水与数据转发

**目标**：通过三级流水提高主频，通过数据转发减少相关指令的等待。

#### 范围

- 插入流水寄存器，重构为三级：`if_stage` / `id_ex_stage` / `mem_wb_stage`
- 数据转发（旁路）单元 `forwarding.v`：EX→EX、MEM→EX、WB→EX 三条旁路
- 冒险检测 `hazard.v`：load-use 停顿（stall）、控制冒险处理（先冲刷后预测，Part C 换 BHT）
- 控制信号随流水级逐级传递与裁剪
- 功能一致性：与 v0 跑**同一套**测试集合，保证"优化不改语义"

#### 交付物

- [ ] v1 核（无分支预测版）
- [ ] 转发专项 tb：back-to-back RAW 依赖序列（R-type 连续相关、lw→add 等），波形可数气泡
- [ ] 中期数据：同 benchmark 在 v0 与 v1（无预测）上的 CPI 对比

#### 验收标准

> 验收跟踪：[#20 Part B](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/20)。10/4 与 Part C 一起收口。

- arch-test 与 v0 相同集合全过
- 连续相关 R-type 序列 CPI 接近 1（旁路生效，波形零气泡）
- load-use 场景正确插入 1 拍停顿
- Vivado 综合：v1 相比 v0 主频有提升或持平，WNS ≥ 0

#### 依赖与风险

- 依赖：Part A 的 v0 测试集合与基线数据，状态见 §3.2。
- 风险预案：若拆级后时序仍不达标，回退为"两级 + 完整转发"（L3 保底版），优化深度不打折

### 4.3 Part C：分支预测与对比验证

**目标**：完成分支预测，用同一组测试比较四种配置：v0、v1 无转发、v1 加转发、v1 加转发与预测。

#### 范围

- `branch_predict.v`：1-bit / 2-bit 饱和计数器 BHT，做成**可配置切换**（1-bit/2-bit/关闭三档，便于对比实验）
- 预测错误冲刷（flush）逻辑：PC 恢复、流水寄存器清零
- 命中率统计计数器（片上统计或仿真统计，数据要有来源）
- 自写 benchmark：Dhrystone 思路的整型测试（循环/数组/函数调用/位运算/乘法混编），C 源码 + 反汇编归档
- riscv-arch-test 扩展子集（RV32M 等）跑全
- 最终数据与报告：v0 / v1 无转发 / v1+转发 / v1+转发+预测 四档的 CPI、Fmax、资源（LUT/FF/BRAM）、命中率（2026-09-20 口径重定义，见 [llm_log](../../report/llm_log/2026-09-20-v0-no-stall-cpi-reframe.md)）

#### 交付物

- [ ] 完整 v1 核（三级 + 转发 + 可切换 BHT）
- [ ] benchmark 源码与编译脚本（`src/riscv_fw/`）
- [ ] 对比数据报告（四档数据表格 + 测试条件 + 原始日志），归档 `report/`
- [ ] 验证脚本/清单沉淀，标 `#skill候选`（如"CPI 测量流程"）

#### 验收标准

> 验收跟踪：[#21 Part C / M1 收口](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/21)，截止 10/4。

- CPI 相对 **v1 无转发**基线降低 ≥ 25%（2026-09-20 口径重定义：v0 两级基线 CPI≈1 不可作降幅基线，仅作参考锚点，见 [llm_log](../../report/llm_log/2026-09-20-v0-no-stall-cpi-reframe.md)）
- 实际最高通过频率点 WNS ≥ 0；125 MHz 为非阻塞加分项
- 2-bit BHT 在含循环的 benchmark 上命中率可统计且显著优于无预测
- 全套测试回归通过，数据与 git commit 对得上

#### 依赖与风险

- 依赖：Part B 的 v1 主体
- 风险预案：分支预测若排期吃紧，保底交付"关闭 BHT + 默认冲刷"版本（L3 保底版），四档数据退化为三档
- 风险预案：CoreMark 移植若卡住，四档对比退化为自写 benchmark 的 CPI 对比（CoreMark/MHz 列留空注明原因），M1 收口不受阻

### 4.4 M1 收口后：PicoRV32 对比实测（验证线）

> 由验证线负责，在 M4 材料收口前完成；不另设逐日窗口。详细口径见 [核心对比说明](../../docs/core_comparison.md)。

- [ ] PicoRV32（YosysHQ 官方仓库）regular + large 两配置，同器件 xc7z020clg400-1、同 Vivado 2026.1 OOC post-route（复用 `build/build.tcl` 流程）
- [ ] Fmax 用约束递减收敛法（10ns → 5ns → 收敛，2–3 轮），与本核同法
- [ ] 性能数据引用官方公开口径（0.309 DMIPS/MHz、CPI 4–5），不重跑其基准；脚注注明来源与口径差异
- [ ] 产出：`docs/core_comparison.md` §2 表更新为实测行 + `data/logs/` 原始报告

---

</details>

## §5 学习路线（剩余阶段）

<details>
<summary>展开 Part B/C 学习资料与自测要求</summary>

> 公共基础与 Part A 学习内容已移入 [历史归档](done/m1-first-phase-completed.md) §B；本节只保留 Part B/C 需要的内容。
> 每条资料的具体链接与用途单列在 [docs/resources.md](../../docs/resources.md)，本节只保留条目 + 自测验收。

### Part B 学习内容

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| 流水线与冒险理论 | §7：COAD 4.6–4.9 + 胡伟武书流水线章 | 能区分 RAW/WAR/WAW，说出 load-use 为何必须 stall |
| 转发/停顿工程实现 | §3：蜂鸟 E203 流水线章节精读（long-pipe 结构） | 能画出三级流水时序图并标出三条旁路路径 |
| 波形阅读 | §1：UG900（XSim 波形操作） | 能从波形数出气泡个数，判断转发是否生效 |

### Part C 学习内容

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| 分支预测 | §7：COAD 预测章节 + E203 对应实现 | 能解释 2-bit 饱和计数器为何抗"单次抖动" |
| 验证方法学 | §3：riscv-arch-test README（编译/比对 signature 机制） | 能独立新增一条 arch-test 用例并跑通 |
| benchmark 与 CPI 测量 | §3：Dhrystone / CoreMark / Embench | 能说清"指令数 + 周期数 → CPI"的统计口径 |
| 时序分析与报告阅读 | §1：UG949 速览 + UG901/UG904 读报告 | 能读综合报告，定位最差路径（WNS 怎么看） |

---

</details>

## §6 核交付与证据

### 6.1 按交付物推进

| 交接条件 | 负责人 | 必须交付 |
|:---|:---|:---|
| RTL 可独立自测 | `jianglibo` | RTL、自测入口、配置说明和已知问题；交付后以缺陷修复为主 |
| 收到可复验版本 | `never-die-cold`、`watercopper` | 专项/全量回归、综合、基准测试、指标和原始日志 |
| 功能与证据满足 §4 | 全员 | 完成 #20/#21；必须为 M1 收口预留修复与复验余量 |
| M1 验收通过 | 全员 | 移交核接口、配置与证据；后续工作包和人员安排见根目录主计划 |

“冻结”表示停止新增功能，允许修复验证发现的缺陷。“收口”表示验收通过且证据齐全，具体标准见 §4。到达日期不代表任务自动完成。

- 核回归入口：`bash sim/scripts/run_iverilog.sh all`；tb、脚本和证据均保留在仓库内。
- 功能、CPI、Fmax 和资源报告须关联实际测试版本；模块级 PASS 不替代三级核集成验收。
- 阶段内不设逐日排班，下一核交付物与风险见 [核交付看板](plan_calendar.md)。
- 板端应用集成仅在核接口验证后交接，整机验收与发布由 [主计划](../../plan.md) 管理。

## 附录 A：技术栈全景

<details>
<summary>展开技术栈参考表</summary>

| 层 | 技术 | 用途 | 对应部分 |
|:---|:---|:---|:---|
| 硬件描述语言 | Verilog-2001（综合）+ 简单 SystemVerilog（tb 用） | 全部 RTL 与验证 | A/B/C |
| 指令集 | RV32IM 规范（riscv.org 手册） | 指令编码、语义唯一权威来源 | A |
| 微架构理论 | 流水线/冒险/转发/预测/CPI（COAD RISC-V 版、胡伟武开源书） | 设计依据与答辩理论 | B/C |
| 软件工具链 | riscv-gnu-toolchain（RV32IM, ILP32）+ objdump/objcopy + linker script | C/汇编 → elf → hex 预载 | A/C |
| 仿真 | Vivado XSim（备选 iverilog/Verilator） | tb 仿真、波形分析 | A/B/C |
| 综合实现 | Vivado 综合/实现 + 时序约束 + WNS 分析（UG901/UG904/UG949） | Fmax/资源报告 | A/B/C |
| 验证基准 | riscv-arch-test + 自写 tb + benchmark（Dhrystone 思路） | 功能正确性与 CPI 量化 | A/C |
| 参考设计 | 蜂鸟 E203、PicoRV32 | 流水线/转发/预测实现对照 | B/C |

</details>

## 附录 B：变更记录（含迁移前历史）

| 日期 | 变更 |
|:---|:---|
| 2026-09-10 | 从早期计划草稿整理出执行计划 |
| 2026-09-14 | 建立三分支协作方式和第一阶段任务表 |
| 2026-09-21 | 压缩 M1 排期；决策记录见 [协作日志](../../report/llm_log/2026-09-21-schedule-compression.md) |
| 2026-09-23 | 将基础准备和 Part A 移入 [历史归档](done/m1-first-phase-completed.md) |
| 2026-09-28 | 调整为三模块并行：10/2 交付模块一 RTL，10/4 验收，10/5 启动模块三 |
| 2026-09-28 | 重整文档职责：主计划维护分工和验收，执行日历维护每日任务和风险 |
| 2026-09-29 | 明确允许超前完成（不改变验收标准，结余时间计入最终验收容错）；Part C 频率口径改为“实际最高通过频率/WNS 入档、125 MHz 非阻塞加分” |
| 2026-09-30 | 产品收敛为紧固件识别与工业检查，采用采集卡视频 + 网口结果的 EXE 界面；排期改为仅固定收口时间，保留验收标准与交付依赖 |
| 2026-09-30 | 用户进一步确认自由分散且互不遮挡、传统视觉定位 + CNN 分类，EXE 由 watercopper 负责；补充模块交接与多目标验收条件 |
| 2026-09-30 | 全项目内容迁移至根目录 plan.md；本文件保留 RISC-V 技术范围、历史索引、核验收与学习资料 |
