# M1 第一阶段完成归档：阶段 0 + 第一阶段任务 + Part A 基线核 v0

> 归档日期：2026-09-23 ｜ 归档分支：`dev/verify` ｜ 范围：原 plan.md §1.3 / §3 / §4.1 / §5（阶段 0–1）
> 用法：本文件是**已完成内容的原文快照 + 完成证据**，只追加不改写；未完成部分看 [../plan.md](../plan.md)（只保留剩余计划）。
> 关联检查点：[#19 [M1] Part A 验收检查点（9/27）](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/19)——归档时仍 OPEN，未验证不声称，收口遗留见 §G。
> 说明：原文照抄自 2026-09-23 的 plan.md（不含整理性改写）；仅相对链接补一级目录，以适配本目录位置。

---

## §A 完成情况总表（截至 2026-09-23）

| 范围 | 项目 | 状态 | 证据 |
|:---|:---|:---|:---|
| 环境 | RISC-V 工具链闭环（C → elf → 反汇编 → hex） | ✅ 2026-09-11 | `src/riscv_fw/`、commit `2f40446`、[llm_log](../../../report/llm_log/2026-09-11-riscv-toolchain.md) |
| 环境 | Vivado 2026.1 安装与验收 | ✅ 2026-09-14 | issue #2（closed）、`build/build.tcl`、`build/reports/`、commit `a16e56b` |
| 环境 | PYNQ-Z2 到货 + 联网 / Jupyter / 点灯验证 | ✅ 2026-09-20 | issue #1（closed）、[board/logs/2026-09-20-pynq-z2-smoke](../../../board/logs/2026-09-20-pynq-z2-smoke/README.md) |
| 阶段 0 | RV32I 编解码自测 `ALL OK` | ✅ 2026-09-11 | `sim/tools/verify_rv32i.py`、commit `2f40446`、[llm_log](../../../report/llm_log/2026-09-11-riscv-instruction-tests.md) |
| 阶段 0 | 公共日历学习项（手册 / 数据通路 / 环境） | ✅ 2026-09-14–20 | §B（原 §3.6 日历） |
| 第一阶段 | v0 六模块 RTL + 冒烟 / 逐指令 tb（38 用例） | ✅ 2026-09-11 | `src/riscv/*.v`、`sim/riscv/tb_core_*.v`、commits `80c47f7`/`7de2915`/`81569ae`/`58ed400` |
| 第一阶段 | v0 回归基线归档（iverilog + XSim 对拍） | ✅ 2026-09-14 | `data/logs/v0_baseline_2026-09-14/`、commit `9eefc21` |
| 第一阶段 | 转发专项 tb + v0 对照数据 + 理解门槛样板 | ✅ 2026-09-20 | `sim/riscv/tb_core_fwd.v`、`data/logs/2026-09-20-fwd-baseline/`、commit `38f1084` |
| 第一阶段 | riscv-arch-test 接入（首组 3 用例 PASS） | ✅ 2026-09-20 | `sim/arch_test/`、`data/logs/2026-09-20-arch-test/`、commit `643f258` |
| 第一阶段 | 工具链复现手册（基准线） | ✅ | `src/riscv_fw/README.md` |
| 第一阶段 | benchmark v0.1 / CPI harness / CoreMark 移植层（基准线） | ⬜ 未入库，顺延至 Part B/C 窗口 | `data/scripts/`（仅 `.gitkeep`） |
| 第一阶段 | 三线工作流 + gate issue 体系 | ✅ 2026-09-14/20 | §2 原文随 [../plan.md](../plan.md) §2 保留；issues #19–#21、commits `3d944a8`/`6193f4f` |
| Part A | `muldiv.v`（RV32M 八操作 + 边界） | 🟡 已实现，待 `dev/rtl` PR 合并 | 分支 `origin/dev/rtl`：`d4c1649`/`745d3b3`/`726d4e5`/`f22f5a3`；`sim/riscv/tb_core_muldiv.v`（该分支） |
| Part A | 最小 SoC 外壳（BRAM 预载 + LED/UART） | 🟡 接口骨架在 main，仿真 / 上板收口中 | `src/riscv/soc_top.v`、`design_v0.md` §5.8 |
| Part A | 存储扩容 32KB + SoC 计时计数器 | ⬜ 契约已冻结（8A），实现未开始 | `report/llm_log/2026-09-22-memory-contract.md`（`dev/rtl`） |
| Part A | 基线数据 Fmax / WNS | ✅ 2026-09-14（Fmax 86.8 MHz / WNS -1.530 ns） | `data/metrics.csv`、`build/reports/timing_impl.rpt` |
| Part A | 基线数据 CPI / 资源 | ⬜ CPI 待补录；资源 ✅（LUT 846 / FF 65 / BRAM 0 / DSP 0） | `data/metrics.csv`、`build/reports/utilization_impl.rpt` |
| Part A | 上板冒烟（LED，JTAG） | ✅ 2026-09-20（回补） | `board/logs/2026-09-20-pynq-z2-smoke/`、`board/smoke_test/`、commit `c8bd5fa` |
| 验收 | gate #19 复核签字 | ⏳ 9/27 周日合并时执行 | issue #19 |

> 状态图例：✅ 完成；🟡 已实现 / 冻结但未随 main 合并或未收口；⬜ 未开始 / 待补；⏳ 待复核。

---

## §B 阶段 0 原文（原 §5 阶段 0 学习表 + §3.6 公共日历）

### 阶段 0：公共基础（开工前 1 周，全员）

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| Verilog 基本功：语言 + 时序电路 | §4：Nandland / ChipVerify 教程 | 能独立写状态机 |
| 体系结构理论：单周期数据通路 | §7：COAD 第 4 章 4.1–4.5 | 能徒手画出单周期 RV32I 数据通路并标注控制信号 |
| RISC-V ISA：RV32I 指令编码 | §3：RISC-V 官方手册第 2 章 + 编码速查卡 | 给定汇编指令能手算机器码；给定机器码能反汇编 |

### 阶段 1：对应 Part A（第 1 周）

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| 中文 CPU 设计实践对照 | §3：蜂鸟 E203 书前 3 章 + PicoRV32 源码速读 | 能说出 E203 与我们的两级结构差异 |
| RISC-V 工具链实操 | §3：riscv-gnu-toolchain 安装与使用 | 独立完成：C 编译 → objdump 反汇编 → objcopy 转 hex |
| （推荐）单周期迷你核练手 | §4：Nandland 教程辅助 | 一天内跑通加法/跳转两条指令 |

### 3.6 阶段 0 公共日历（9/14–9/20）

| 日期 | 公共事项 | 验收 |
|:---|:---|:---|
| 9/14 周一 | 开工会：三线认领、各自 `git fetch` + `checkout` 分支实操；Vivado 启动下载 | 每人本地切到自己分支成功 |
| 9/15 周二 | RISC-V 手册 §2 指令编码 | 给定汇编能手算机器码 |
| 9/16 周三 | 机器码反汇编练习 | 给定机器码能反汇编 |
| 9/17 周四 | Vivado 安装并跑通官方例程（谁先装好谁带全队） | 🔴 license 与器件库无报错 |
| 9/18 周五 | 工具链复核（全员各自复现一遍 C → hex） | 🔴 每人独立产出 hex |
| 9/19 周六 | ⏸ 板卡烧录顺延（issue #1）；改为 PYNQ 官方文档预习 + COAD 4.1–4.5 | 能徒手画单周期数据通路 |
| 9/20 周日 | 上午 E203 书 + 工具链全流程；晚 1h 复盘 + **首次周合并** | 首次 PR 合并完成 |

> 📌 2026-09-20 更新：PYNQ-Z2 到货并完成上板验证（issue #1 闭环），9/19 顺延的板卡项恢复执行；全队共用 1 块板，上板时段自行错峰报备。

---

## §C 第一阶段任务分配原文（原 §3.1–§3.5）

> **第一阶段 = 阶段 0（知识准备）＋ Part A（基线收口）**；出口 = §3.5 检查表全勾。
> 工时结构：工作日晚约 2h；整天块 = 9/19–20（周末）、9/25–27（中秋 3 天，已被 Part B 占用）。
> 前置约束：9/14 前全队被另一比赛占用，阶段 0 知识准备并入本窗口第一周。
> 用法：全员先读 §3.1，再读自己那条线（§3.2 / §3.3 / §3.4）；组长按 §3.5 验收、按 §3.6 对日历。
> 逐人执行清单（含 9/14 实际进度核对）已移至队内私有目录（不随开源仓库分发）。

### 3.1 全员公共（每天固定动作）

- [ ] 每晚前 30 分钟理论补课（以 §5 学习路线阶段 0 的自测表为准）
- [ ] 收尾 10 分钟：commit（AI 产出注明 prompt 要点）+ 卡点/决策记 llm_log
- [ ] 一切 AI 生成代码走理解门槛（[code_review_checklist.md](../../../docs/code_review_checklist.md)）
- [ ] 卡住超 30 分钟发群里，不硬扛

### 3.2 RTL 线（主责：逻辑开发主力）—— 分支 `dev/rtl`

**目标**：吃透 v0 并接管 → Part A 收口（M 扩展 / SoC 外壳 / 基线数据）→ 为 Part B 三级重构备好设计

**周 1（9/14–9/20）：吃透 + 准备**

- [ ] 精读 [design_v0.md](../design_v0.md) + v0 六模块 RTL，**过理解门槛**（逐段讲解 + 3 题；讲解稿存 llm_log）——你是后续所有 RTL 的接手人，这不是可选项
- [ ] COAD 4.1–4.5：能徒手画单周期 RV32I 数据通路并标注控制信号
- [ ] 蜂鸟 E203 书前 3 章速读：能说出 E203 与我们的两级结构差异
- [ ] `muldiv` 设计准备（先设计后写码）：读 design_v0.md §9 决策，写出"移位加减"架构要点 + 接口草案

**周 2（9/21–9/24）：Part A 收口（压缩后 4 个工作日晚，9/25 起 RTL 线转 Part B）**

- [ ] `muldiv.v`：RV32M 乘除实现 + 单指令测试（接口风格对齐现有模块）
- [ ] 最小 SoC 外壳：指令 BRAM 预载 hex + LED / UART 二选一，仿真跑通 + 上板冒烟（板卡已到，2026-09-20 解除顺延；共用板需错峰）
- [ ] Vivado 装好后第一件事：综合 v0 → Fmax/WNS + LUT/FF/BRAM 基线数据 → 日志入 `data/logs/`、数值入 `data/metrics.csv`
- [ ] **存储扩容（2026-09-21 新增，CoreMark 硬依赖）**：dmem 4KB→32KB、imem 16KB→32KB；dmem 若由异步读改同步读 BRAM，v0 CPI 锚点语义变化须重跑冒烟 + arch-test 回归，决策记录 llm_log
- [ ] **SoC 计时计数器（2026-09-21 新增）**：`soc_top` 加 32-bit 存储器映射自由运行计数器（~30 行），供 CoreMark 板上计时；地址分配写入 design_v0.md §3.3
- [ ] 同步更新 `design_v0.md`（muldiv 接口与实现决策 + 扩容/计数器）
- [ ] 风险预案：M 扩展卡住 → 先出 RV32I 基线数据，乘除后补；不影响 Part A 其余验收

**交付物**：[ ] muldiv + 单测 ｜ [ ] SoC 外壳仿真 PASS ｜ [ ] v0 基线数据入档 ｜ [ ] design_v0.md 同步 ｜ [ ] 存储扩容 + 计时计数器（CoreMark 前置）

> 📌 后续修订（`dev/rtl`，commit `f22f5a3`）：存储扩容契约冻结为 dmem 16KB→32KB、imem 16KB→32KB，DMEM 冻结为异步读以保住 v0 CPI 锚点语义（统一契约见 design_v0.md §3，决策见 `report/llm_log/2026-09-22-memory-contract.md`，该 commit 尚未并入 main，暂不挂链接）。

### 3.3 验证线（主责：组长）—— 分支 `dev/verify`

**目标**：v0 回归基线固化 → Part B 测试先行（转发 tb 对契约先写）→ 理解门槛与 PR 流程跑成样板

**周 1（9/14–9/20）：基线固化 + 方法学**

- [ ] 跑通 `sim/scripts/run_iverilog.sh`，输出与结果归档 `data/logs/v0_baseline_2026-09-14/`（后续"优化不改语义"的对照证据）
- [ ] tb 方法学 + 波形阅读（[resources.md](../../../docs/resources.md) / UG900）：能从波形数出气泡个数
- [ ] 精读 design_v0.md；为 v0 六个模块各写一句"验证观察点"（放 `sim/README.md` 或 llm_log）
- [ ] 理解门槛样板：首个真实 PR 走一遍"讲解 + 3 题 + llm_log 存档"全流程

**周 2（9/21–9/24）：测试先行（压缩窗口，与 Part A 同步收口）**

- [ ] **转发专项 tb 框架**：back-to-back RAW 序列（R-type 连续相关、lw→add 等）+ load-use 停顿判据——按 design_v0 契约写，先在 v0 上跑出对照数据（v0 应出现气泡/停顿，供 v1 对比）
- [ ] riscv-arch-test 接入：编译 / 比对 signature 机制跑通，至少 1 组 RV32I 子集纳入回归
- [ ] `run_iverilog.sh` 升级：支持"v0 回归集合 + 转发专项"两档
- [ ] 更新 `sim/README.md`（跑法 / 判据 / 证据路径）

**交付物**：[ ] v0 回归基线归档 ｜ [ ] 转发 tb 框架 + v0 对照数据 ｜ [ ] arch-test 首组跑通 ｜ [ ] 理解门槛样板

### 3.4 基准线（主责：文档与答辩）—— 分支 `dev/bench`

**目标**：工具链复现手册 → benchmark 骨架 → CPI 度量与 metrics 填报工具 → 答辩素材

**周 1（9/14–9/20）：复现 + 摸底**

- [ ] 按 `src/riscv_fw/README.md` 独立复现工具链闭环（C → elf → 反汇编 → hex），把卡点补进 README（变成新人手册）
- [ ] 调研 Dhrystone / CoreMark / Embench 统计口径，产出 1 页《CPI 怎么测》笔记（`data/scripts/` 或 llm_log）
- [ ] RISC-V 手册第 2 章：给定汇编能手算机器码、给定机器码能反汇编
- [ ] 通读 README + proposal_upgrade：建立作品全貌（文档与答辩素材的来源）

**周 2（9/21–9/27）：benchmark + 度量工具（9/24 前完成主体，9/25–10/1 CoreMark 移植与 Part B/C 并行）**

- [ ] benchmark C 程序 v0.1：循环 / 数组 / 函数调用 / 位运算 / 乘法混编（Dhrystone 思路），C 源码 + 反汇编归档
- [ ] **CoreMark 移植启动（2026-09-21 新增，唯一正式基准，决策见 [docs/core_comparison.md](../../../docs/core_comparison.md)）**：EEMBC coremark 拉取 + `core_portme.c/h` 裸机移植层（依赖 Part A 扩容与计数器，9/24 前就绪）；移植窗口 9/25–10/1（压缩后排期，与 Part B/C 并行）；linker script 按扩容后布局调整
- [ ] CPI 统计 harness 脚本骨架：仿真侧统计 retired 指令数 / 周期数（`data/scripts/`）
- [ ] `data/metrics.csv` 填报规范：日志 → 表格的流程（测量条件必填）
- [ ] 两次合并（9/20、9/27）的证据与 llm_log 汇总整理

**交付物**：[ ] 工具链复现手册定稿 ｜ [ ] benchmark v0.1 ｜ [ ] CPI harness 骨架 ｜ [ ] metrics 填报规范 ｜ [ ] CoreMark 移植层（依赖 Part A 扩容就绪）

### 3.5 第一阶段出口检查表（9/24 全勾目标，9/27 周日合并复核，组长主持）

> 检查点 issue：[#19 [M1] Part A 验收检查点（9/27）](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/19)——本表全勾后关闭。压缩后 9/24 为全勾目标日，9/27 周日合并时复核签字（自带 3 天缓冲）。

- [ ] 全员：阶段 0 自测三项全过（编解码 / 画数据通路 / 编码练习）
- [ ] RTL 线：§3.2 交付物全勾 + §4.1 Part A 验收
- [ ] 验证线：§3.3 交付物全勾（转发 tb 在 v0 上跑出对照数据）
- [ ] 基准线：§3.4 交付物全勾
- [ ] 合并：9/20、9/27 两次周日合并完成（PR 记录 + 复核签字）
- [ ] 记录：每人 ≥2 条 llm_log（含理解门槛讲解稿落盘）

---

## §D Part A 原文（原 §4.1）

### 4.1 Part A：两级流水基线核 v0（状态：收口阶段）

**目标**：先把"从 C 编译到板上跑起来"的闭环打通，拿到后续一切对比的**锚点数据**。

#### 范围

- 两级流水：第一级取指（IF），第二级译码+执行+访存+写回
- 数据通路：`pc` / `if_stage` / `decode` / `alu` / `muldiv`（M 扩展，可先斩后补）/ `regfile` / 访存接口
- 控制信号完整，`core_top` 顶层打通
- 配套最小 SoC 外壳：指令 BRAM（预载 hex）+ 一个最小外设（LED / UART 二选一）
- 工具链闭环：riscv-gnu-toolchain 编译 → objcopy 转 hex → 预载入 BRAM → 仿真/上板

#### 交付物（状态截至 9/14）

- [x] `v0` 核 RTL（每模块头部注释：功能/接口/作者/日期）—— 9/11 完成
- [x] 冒烟 testbench（逐指令 38 用例）—— 9/11 完成
- [x] 工具链脚本（编译、转 hex、加载流程写死在脚本里）—— 9/11 完成
- [ ] `muldiv.v`（M 扩展）
- [ ] 最小 SoC 外壳（仿真）
- [ ] **基线数据**：Vivado 综合 Fmax/WNS + 初版 CPI（依赖 Vivado 安装）

#### 验收标准

- 仿真：RV32I 算术/逻辑/访存/分支/跳转指令单测全部通过（✅ 已过，38 用例）
- 上板：跑通 LED 闪烁或乘法小程序（✅ 2026-09-20 板卡到货解除顺延，9/27 前回补完成；实测记录入 `board/`）
- 数据：基线 CPI 与 Fmax 记录进 `data/`（`metrics.csv` + `logs/`），这是之后"降低 ≥25%"的对照锚点

#### 依赖与风险

- 依赖：~~Vivado 安装（issue #2）~~ ✅ 已完成（2026-09-14 验收，综合基线已入库）；~~板卡到货（issue #1）~~ ✅ 2026-09-20 到货并完成上板验证
- 风险预案：M 扩展乘除若卡住，先以 RV32I 出基线数据，乘除放 Part A 收尾补

---

## §E 现状盘点原文（原 §1.3，9/14 快照）

> 仅作历史快照归档，不再更新；后续进展以 §A 与 [../plan.md](../plan.md) 为准。

**✅ 已提前完成（9/11）**

- v0 两级流水六个模块 RTL 已落地，逐指令自检 **RV32I 38 用例全过**（iverilog 一键回归：`sim/scripts/run_iverilog.sh`）
- 工具链闭环（C → elf → 反汇编 → hex）与构建脚本（`src/riscv_fw/`）

**⏳ 阻塞 / 待办**

- ~~PYNQ-Z2 未到货（issue #1）~~ ✅ 2026-09-20 板卡到货并完成上板验证（联网 / Jupyter / base overlay / 点灯）：上板类任务解除顺延；阶段 0"板子过关"项已勾。**全队共用 1 块板，上板时段群内报备**
- ~~Vivado 待装（issue #2）~~ ✅ 2026-09-14 已装（2026.1 BASIC）并完成验收：v0 核综合基线出炉（WNS -1.530 ns / **Fmax 86.8 MHz**，未达 100 MHz → Part B 优化对象；证据 `build/reports/`）

**📌 对第一阶段的影响**

Part A 只剩收口项（M 扩展 / SoC 外壳 / 基线数据）。三线不空转：RTL 线提前吃透与设计准备；验证线、基准线把 Part B/C 需要的测试与度量工具先造好。

---

## §F 完成证据索引（commit / 数据 / issue）

**关键 commit（`git log --all`，2026-09-11 – 09-22）**

| 主题 | commit |
|:---|:---|
| v0 接口冻结 / 模块 RTL / 冒烟连通 | `cf78db6` `80c47f7` `7de2915` `81569ae` |
| 逐指令自检 tb + 编解码自测 | `58ed400` `2f40446` `6d05cc9` |
| 结构治理（metrics→data、sw→src、src/soc 并入） | `aec4d7b` `b11ec80` `49a490e` |
| 三线工作流 + plan 重构 + gate issue | `3d944a8` `60f7e0c` `6193f4f` |
| 环境验收与 v0 基线（Vivado / 回归归档） | `a16e56b` `9eefc21` |
| 板卡到货闭环 + 上板冒烟 | `f7a075e` `1fb6787` `c8bd5fa` `2869118` |
| 转发专项 tb + arch-test 接入 | `38f1084` `643f258` `565d142` `49a4e9c` |
| Part A 契约 / sb-sh / IF 停顿（已入 main） | `e0fdef0` |
| Part A muldiv 实现（`origin/dev/rtl`，**尚未并入 main**） | `bf4a180` `d4c1649` `745d3b3` `726d4e5` `f22f5a3` |

**数据与日志**

- `data/logs/v0_baseline_2026-09-14/`（iverilog + XSim 对拍）
- `data/logs/2026-09-20-fwd-baseline/`（转发专项 v0 对照）
- `data/logs/2026-09-20-arch-test/`（add-01 / addi-01 / and-01 PASS）
- `data/logs/2026-09-20-pynq-z2-smoke-vivado/`（独立复核 DRC/timing/utilization）
- `data/metrics.csv`（Fmax / WNS / 资源基线）
- `build/reports/{timing,utilization,design_analysis}_impl.rpt`、`build/build.tcl`
- `board/logs/2026-09-20-pynq-z2-smoke/`、`board/smoke_test/`

**llm_log 主要条目**

- 2026-09-11：`plan1-merge-repo-hygiene` / `riscv-instruction-tests` / `riscv-toolchain` / `riscv-v0-design` / `riscv-v0-rtl` / `skip-wildfire-board`
- 2026-09-14：`vivado-2026-1-acceptance` / `vivado-2026-1-decision` / `three-line-workflow` / `restructure-official-layout` / `track-guides-alignment`
- 2026-09-15：`muldiv-interface-gap`
- 2026-09-20：`fwd-tb-understanding-gate` / `arch-test-integration` / `v0-no-stall-cpi-reframe` / `m1-gate-issues` / `pynq-z2-smoke-verification` / `partA-gufa-programming` / `board-arrival-doc-sync` 等
- 2026-09-21：`schedule-compression` / `narrative-architecture-fix`
- `origin/dev/rtl`（未合并）：`2026-09-22-partA-7b-core-integration` / `2026-09-22-memory-contract`

**issue**

- #1 板卡到货（closed）、#2 Vivado 安装（closed）；#19 Part A 验收（open，9/27）

---

## §G 遗留与收口清单（Part A / 第一阶段未完成项）

> 归档不代表验收完成——以下为截至 2026-09-23 仍未收口的项目，跟踪入口：[../plan.md](../plan.md) §3.2，验收签字见 issue #19。

| # | 遗留项 | 现状 | 建议窗口 |
|:---|:---|:---|:---|
| 1 | 最小 SoC 外壳仿真 + 上板冒烟 | `soc_top.v` 骨架在 main；仿真 tb / 上板工程未收口 | 9/24–9/27（gate #19 前） |
| 2 | 存储扩容 32KB + SoC 计时计数器 | 契约已冻结（`dev/rtl` 8A），实现未开始 | Part A 收口 / Part B 前 |
| 3 | 基线 CPI 补录 | `data/metrics.csv` 第 2 行留空 | Part A 收口 |
| 4 | `dev/rtl` Part A 分支合并 | 5 个 commit 未进 main（`f22f5a3` 等） | 9/27 周合并 |
| 5 | gate #19 复核签字 | issue OPEN | 9/27 |
| 6 | benchmark v0.1 / CPI harness / CoreMark 移植层 | 未入库（原第一阶段基准线交付物） | Part B/C 窗口（与 Part B/C 并行） |
