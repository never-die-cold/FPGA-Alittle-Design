# 模块一开发计划（剩余部分）：Part B/C → M1 收口 → M2–M4

> 已完成部分（阶段 0、第一阶段任务、Part A 两级流水基线核 v0）的原文与完成证据见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)；本文只列**未完成**部分。
> 指令集 RV32IM ｜ 当前基线 v0（两级流水，Fmax 86.8 MHz）→ 三级流水（IF / ID+EX / MEM+WB）＋数据转发 ＋轻量分支预测（v1）
> M1 窗口：9/25 – 10/1（2026-09-21 压缩提前，原 10/4）｜ 出口：CPI 相对 v1 无转发基线降 ≥25%（2026-09-20 口径重定义，见 §4.3）、Fmax ≥100 MHz、全套回归通过、数据入档
> 工作流（2026-09-14 起）：三线并行 + 每周日 PR 合并，分支操作要点见 §2

**本文怎么用**

| 节 | 内容 | 谁重点看 |
|:---|:---|:---|
| §1 | 剩余目标与时间轴（9/25 起） | 全员（开工前必读） |
| §2 | 三线分工与协作规矩 | 全员 |
| §3 | 已完成部分归档索引与当前起点（含遗留项） | 全员（开工前核对） |
| §4 | 剩余各 Part 技术内容与验收（Part B / C / PicoRV32） | 全员（对照验收） |
| §5 | 学习路线（剩余阶段 2–3） | 全员 |
| §6 | 后续排期（Part B/C + M2–M4）、纪律、关键日期 | 全员 |

---

## §1 目标与剩余时间轴

### 1.1 技术路线（三部分总览）

| 部分 | 名称 | 核心内容 | 关键交付物 | 验收标准 | 主责 |
|:---|:---|:---|:---|:---|:---|
| A ✅ | 两级流水基线核 v0（已完成，已归档） | 数据通路 + 控制 + RV32IM 全指令，打通工具链闭环 | 可综合 v0 核 + 冒烟 tb + 工具链脚本 | 单指令冒烟全过，上板跑通小程序，**基线 CPI / Fmax 数据在案** | RTL 线 `dev/rtl`（验证/基准线对契约先行） |
| B | 三级流水重构 + 数据转发 | 拆三级 + 旁路电路 + Stall 控制 | v1 核（无预测版）+ 转发专项 tb | 相关指令序列 CPI≈1，load-use 正确停顿，arch-test 与 v0 同集合全过 | RTL 线 `dev/rtl`（验证线并行出 tb） |
| C | 分支预测 + 验证闭环 | 1-bit/2-bit BHT + 冲刷 + benchmark + 全对比数据 | 完整 v1 核 + benchmark 源码 + 四级对比报告 | CPI 降低 ≥25%（相对 v1 无转发；2026-09-20 重定义），Fmax ≥100 MHz，命中率可统计 | RTL 线 `dev/rtl`；验证线出命中率与回归证据；基准线出四档数据 |

> 分工不分家：每周例会互讲进度，A/B/C 每个部分的设计决策、波形与数据三人都会看。
> A 的范围、交付物、完成证据与收口遗留见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)（§D / §A / §G）。

### 1.2 时间轴（剩余部分，2026-09-21 极限压缩版）

> 2026-09-21 起排期整体前移：Part A 压缩到 4 个工作日晚，Part B/C 提前至中秋+国庆前段，M1 从 10/4 提前到 10/1 收口，为 M2/M3 多争取 ~9 天缓冲。决策记录见 [../../report/llm_log/2026-09-21-schedule-compression.md](../../report/llm_log/2026-09-21-schedule-compression.md)。
> 阶段 0 与 Part A 已收口（原文与证据见 [done/](done/)），本表只列剩余阶段。

| 阶段 | 时间 | 出口标准 | 每日安排 |
|:---|:---|:---|:---|
| Part B：三级 + 转发 | 9/25 – 9/28 | §4.2 Part B 验收（gate #20 提前至 9/28） | §6.1 |
| Part C：BHT + 验证闭环 | 9/29 – 10/1 | §4.3 M1 验收（gate #21 提前至 10/1） | §6.1 |
| M2：协处理器 + 预处理 | 10/2 – 10/12 | README 里程碑 M2 | §6.4 |
| M3：系统集成 | 10/13 – 10/20 | README 里程碑 M3 | §6.4 |
| M4：文档冲刺（边做边写摊薄） | 10/21 – 10/26 | README 里程碑 M4 | §6.4 |
| 缓冲 + stretch + 答辩素材 | 10/27 – 11/3 | L3.5 随时可砍 | docs/proposal_upgrade.md |
| 作品提交 | 11/4 18:00 截止 | 全套材料提交 | README 开发计划 |

---

## §2 三线分工与协作规矩

> 2026-09-14 起采用"三线并行 + 每周 PR 合并"工作流；操作要点：dev/rtl、dev/verify、dev/bench 三条分支各自推进，周日由组长审 PR 后合并，任何人（含组长）不直接 push `main`。

### 2.1 三条线

| 线 | 分支 | 主责 | 内容（对齐 §4 验收标准） | 目录边界 |
|:---|:---|:---|:---|:---|
| RTL 线 | `dev/rtl` | 逻辑开发主力 | Part A 遗留收口 + Part B 全部 + Part C 的 BHT RTL；内部 B→C 保持串行、一人连贯完成 | `src/riscv/` |
| 验证线 | `dev/verify` | 组长 | 测试先行：转发专项 tb、arch-test 扩集、BHT 命中率统计、全套回归证据 | `sim/`；归档可写 `data/logs/`、`data/evidence/` |
| 基准线 | `dev/bench` | 文档与答辩 | benchmark C 程序、CPI 统计 harness、三档对比数据、`data/metrics.csv` 填报 | `src/riscv_fw/`、`data/` |

### 2.2 六条分支规矩

1. 每人只动自己目录；跨目录改动（README / docs / llm_log 等共享文件）先在群里说一声
2. 每周日 = 合并日（例会日）：上午各线发 PR，下午例会审合并；首次 9/20，此后 9/27、10/4
3. **任何人（含组长）不直接 push `main`**，一切改动经 PR 合并
4. 组长审 PR 时按 [code_review_checklist.md](../../docs/code_review_checklist.md) 走理解门槛（逐段讲解 + 3 道测试题）；AI 代码未通过不 merge
5. 合并后全员 `git pull origin main` 同步，下一周从最新 main 续做
6. 任何一步卡住超 30 分钟：群里报，不硬扛

### 2.3 依赖红线

RTL 线内部 Part B（9/25–9/28）→ Part C（9/29–10/1）串行不变；验证线 / 基准线对照 [design_v0.md](design_v0.md) 接口契约先行开工，不等 RTL 完成。

---

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

- 核：v0 六模块两级流水 + 冒烟 / 逐指令 tb（38 用例）；RV32M `muldiv` 已在 `dev/rtl` 实现并通过 RV32IM 整核冒烟（待 PR 合并）
- 基线数据：Fmax 86.8 MHz / WNS -1.530 ns、LUT 846 / FF 65 / BRAM 0 / DSP 0（Vivado 2026.1，xc7z020clg400-1，10 ns 约束 OOC）
- 回归口径：`sim/scripts/run_iverilog.sh`（v0|fwd 两档）；riscv-arch-test 首组（add-01 / addi-01 / and-01）PASS

**遗留项（收口前必须处理，详见归档 §G）**

- [ ] 最小 SoC 外壳（BRAM 预载 + LED/UART）仿真 + 上板冒烟
- [ ] 存储扩容 32KB + SoC 计时计数器（契约已冻结，见归档 §G 第 2 项）
- [ ] 基线 CPI 补录 `data/metrics.csv`
- [ ] `dev/rtl` Part A 分支 PR 合并（`f22f5a3` 等 5 个 commit，9/27 周合并）
- [ ] gate #19 复核签字（9/27）
- [ ] benchmark v0.1 / CPI harness / CoreMark 移植层（原第一阶段基准线交付物，顺延）

### 3.3 引用兼容说明

原 §3.5 / §4.1 的引用（onboarding、gate issue #19）已改为指向归档；§4.1 保留占位节避免断链。旧新章节对照见附录 B。

---

## §4 各 Part 技术内容与验收

### 4.1 Part A：两级流水基线核 v0（✅ 已完成，已归档）

范围、交付物、验收标准与完成证据全文见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)；其收口遗留项见 §3.2，复核签字见 [#19 [M1] Part A 验收检查点（9/27）](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/19)。

### 4.2 Part B：三级流水重构 + 数据转发（9/25 – 9/28）

**目标**：完成本项目最核心的创新点——拆级提频 + 旁路消气泡。

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

> 检查点 issue：[#20 [M1] Part B 验收：三级流水 + 数据转发（9/28）](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/20)

- arch-test 与 v0 相同集合全过
- 连续相关 R-type 序列 CPI 接近 1（旁路生效，波形零气泡）
- load-use 场景正确插入 1 拍停顿
- Vivado 综合：v1 相比 v0 主频有提升或持平，WNS ≥ 0

#### 依赖与风险

- 依赖：Part A 的 v0 测试集合与数据（9/24 前就绪）；中秋 9/25–27 三个整天块是本 Part 的主要工时来源
- 风险预案：若拆级后时序仍不达标，回退为"两级 + 完整转发"（L3 保底版），优化深度不打折

### 4.3 Part C：分支预测 + 验证闭环（9/29 – 10/1）

**目标**：BHT 落地 + benchmark 完整化 + 出一份有说服力的三级对比数据。

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

> 检查点 issue：[#21 [M1] Part C 验收 + M1 收口（10/1）](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/21)

- CPI 相对 **v1 无转发**基线降低 ≥ 25%（2026-09-20 口径重定义：v0 两级基线 CPI≈1 不可作降幅基线，仅作参考锚点，见 [llm_log](../../report/llm_log/2026-09-20-v0-no-stall-cpi-reframe.md)）
- Fmax ≥ 100 MHz，WNS ≥ 0
- 2-bit BHT 在含循环的 benchmark 上命中率可统计且显著优于无预测
- 全套测试回归通过，数据与 git commit 对得上

#### 依赖与风险

- 依赖：Part B 的 v1 主体
- 风险预案：分支预测若排期吃紧，保底交付"关闭 BHT + 默认冲刷"版本（L3 保底版），四档数据退化为三档
- 风险预案：CoreMark 移植若卡住，四档对比退化为自写 benchmark 的 CPI 对比（CoreMark/MHz 列留空注明原因），M1 收口不受阻

### 4.4 M1 收口后：PicoRV32 对比实测（10/21 – 10/24，验证线）

> 2026-09-21 决策：排 M1 收口之后（不进 M1 关键路径），主责验证线。原 10/5–10/8 窗口因排期压缩让位给 M2 冲刺（10/2–10/12）与 M3 集成（10/13–10/20），后移至 M4 窗口前段。详见 [docs/core_comparison.md](../../docs/core_comparison.md)。

- [ ] PicoRV32（YosysHQ 官方仓库）regular + large 两配置，同器件 xc7z020clg400-1、同 Vivado 2026.1 OOC post-route（复用 `build/build.tcl` 流程）
- [ ] Fmax 用约束递减收敛法（10ns → 5ns → 收敛，2–3 轮），与本核同法
- [ ] 性能数据引用官方公开口径（0.309 DMIPS/MHz、CPI 4–5），不重跑其基准；脚注注明来源与口径差异
- [ ] 产出：`docs/core_comparison.md` §2 表更新为实测行 + `data/logs/` 原始报告

---

## §5 学习路线（剩余阶段）

> 阶段 0–1（公共基础与 Part A 相关）已随归档移出，原文见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md) §B；本节只保留对应 Part B/C 的阶段 2–3。
> 每条资料的具体链接与用途单列在 [docs/resources.md](../../docs/resources.md)，本节只保留条目 + 自测验收。

### 阶段 2：对应 Part B（第 2 周）

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| 流水线与冒险理论 | §7：COAD 4.6–4.9 + 胡伟武书流水线章 | 能区分 RAW/WAR/WAW，说出 load-use 为何必须 stall |
| 转发/停顿工程实现 | §3：蜂鸟 E203 流水线章节精读（long-pipe 结构） | 能画出三级流水时序图并标出三条旁路路径 |
| 波形阅读 | §1：UG900（XSim 波形操作） | 能从波形数出气泡个数，判断转发是否生效 |

### 阶段 3：对应 Part C（第 3–4 周）

| 学习内容 | 资源（docs/resources.md） | 自测验收 |
|:---|:---|:---|
| 分支预测 | §7：COAD 预测章节 + E203 对应实现 | 能解释 2-bit 饱和计数器为何抗"单次抖动" |
| 验证方法学 | §3：riscv-arch-test README（编译/比对 signature 机制） | 能独立新增一条 arch-test 用例并跑通 |
| benchmark 与 CPI 测量 | §3：Dhrystone / CoreMark / Embench | 能说清"指令数 + 周期数 → CPI"的统计口径 |
| 时序分析与报告阅读 | §1：UG949 速览 + UG901/UG904 读报告 | 能读综合报告，定位最差路径（WNS 怎么看） |

---

## §6 后续排期、纪律与关键日期

### 6.1 Part B / Part C 日粒度排期（9/25 – 10/1，2026-09-21 压缩版）

#### Part B：三级流水重构 + 数据转发（9/25 – 9/28）

> 中秋 3 天（9/25–27）是本 Part 主要工时来源，RTL 线全天投入；9/27 兼顾 Part A 复核与周合并。

| 日期 | 类型 | 任务 |
|:---|:---|:---|
| 9/25（中秋 D1） | **全天** | 插流水寄存器，重构三级（IF / ID+EX / MEM+WB）；COAD 4.6–4.9 同步补课；控制信号逐级传递与裁剪 |
| 9/26（中秋 D2） | **全天** | `forwarding.v` 三条旁路（EX→EX / MEM→EX / WB→EX）+ `hazard.v` load-use 停顿；三级数据通路连通 |
| 9/27（中秋 D3·周日） | **全天** | 与 v0 同集合回归全过；转发专项 tb（back-to-back RAW 序列，波形数气泡）；上午 Part A 复核（#19）+ **周合并** |
| 9/28（周一） | 晚 | Vivado 综合对比 v0/v1 主频；✅ Part B 验收（#20） |

#### Part C：分支预测 + 验证闭环（9/29 – 10/1）

| 日期 | 类型 | 任务 |
|:---|:---|:---|
| 9/29（周二） | 晚 | `branch_predict.v`：1-bit / 2-bit 饱和计数器 BHT，三档可配置（1-bit/2-bit/关闭）；预测错误冲刷逻辑（PC 恢复、流水寄存器清零） |
| 9/30（周三） | 晚 | 自写 benchmark + arch-test 扩展子集（RV32M 等）跑全；命中率统计计数器 |
| 10/1（国庆 D1） | **全天** | 四档（v0 / v1 无转发 / v1+转发 / v1+转发+预测）CPI、Fmax、资源对比报告归档 `report/`；llm_log 收尾；✅ **M1 里程碑验收**（#21） |

### 6.2 全程纪律

1. **每晚收尾 10 分钟**：AI 产出 RTL 立即 `git commit`（message 注明 prompt 要点）；解决了设计决策点按 `report/llm_log/template.md` 写协作记录。
2. **降级红线（压缩后提前）**：若 **9/29** 时 Part B 未验收，立即启动 L3 预案，保住"三级 + 转发"核心创新点完整可测——压缩排期下缓冲变薄，红线触发要更果断。
3. **理论补课嵌入式进行**：每晚前 30 分钟补当日 RTL 涉及的理论（本文学习路线阶段 2–3 自测表为 checklist），不单独占整天。
4. **分工不分家**：中秋、国庆假期每天收工前 15 分钟三人互讲进度，波形与数据三人都会看。
5. **演示层任务不进 M1 关键路径**：命题升级（参数化演示面板、软/硬推理切换、OSD 动效、检测-跟踪 stretch）的归属与排期见 `docs/proposal_upgrade.md`，全部排在 M2/M3 内嵌或其后的 stretch 窗口；M1 主线技术内容零改动（日期 2026-09-21 压缩前移）。
6. **每周日下午固定 1.5h 备考决赛 Verilog 上机考核**（不通过即失评奖资格）：限时真题 / HDLBits 专题交替；压缩排期不砍备考——备考日期全部维持原位（9/27 数字钟 / 10/1 交通灯 / 10/3 运算类 / 10/4 全真模拟）。
7. **分支纪律（2026-09-14 起）**：三线并行、每周日 PR 合并——分支名、目录边界与六条规矩见 §2；任何人（含组长）不直接 push `main`。

### 6.3 关键日期速查（2026-09-21 压缩版，已完成日期见归档）

| 日期 | 事件 |
|:---|:---|
| 9/25–9/26 中秋 | Part B 冲刺：三级流水 + 转发（整天块） |
| 9/27 周日 | Part A 复核（#19）+ 周合并 |
| 9/28 周一 | ✅ Part B 验收（#20） |
| 9/29–9/30 | Part C：BHT + 冲刷 + 命中率统计 |
| 10/1 国庆 D1 | ✅ Part C 验收 + **M1 收口**（#21） |
| 10/2–10/8 国庆 | M2 冲刺：预处理链路 / MAC 阵列 / Jupyter 面板三线并行 |
| 10/12 | M2 验收：HDMI 直通演示 + CNN 首个网络跑通 |
| 10/13–10/20 | M3 系统集成：SoC 全链路闭环 + 全部指标实测 |
| 10/21–10/24 | PicoRV32 对比实测（验证线）+ M4 文档终稿启动 |
| 10/26 | M4 收口：设计报告、协作记录、Skill、演示视频 |
| 10/27–11/3 | 缓冲 + L3.5 stretch（随时可砍）+ 答辩演练提前启动 |
| 11/4 18:00 | 作品提交截止 |

### 6.4 M2 / M3 / M4 概览（压缩后排期，详细任务见 README 与各模块 README）

| 阶段 | 时间 | 主线内容 | 三线分工 |
|:---|:---|:---|:---|
| M2 | 10/2 – 10/12 | 预处理流水线 HDMI 直通演示；CNN 协处理器跑通首个网络 | 视觉 RTL=验证线、协处理器 RTL=RTL 线、Jupyter 上位机=基准线，三人并行 |
| M3 | 10/13 – 10/20 | SoC 全链路闭环上板演示；全部指标实测采集完成 | 全员集成；验证线主持实测 |
| M4 | 10/21 – 10/26 | 设计报告、协作记录、Skill、演示视频收尾 | 文档主责=基准线；边做边写已摊薄，此窗口只留终稿 |

---

## 附录 A：技术栈全景

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

## 附录 B：文档来历

> 本计划的技术内容与验收标准来自 README 里程碑与 team 决议；原"执行排期"节由 Kimi 工作区 plan1 草稿合并而来（2026-09-10）。
> 2026-09-14 随"三线并行 + 每周 PR"工作流重构为本文结构（§3 第一阶段任务分配为新增），技术内容与验收标准未改动。
> 2026-09-21 排期极限压缩：Part A 压至 9/21–9/24、Part B/C 前移至中秋+国庆 D1、M1 提前至 10/1 收口、M2–M4 相应前移与摊薄；技术内容与验收标准未改动，决策记录见 [../../report/llm_log/2026-09-21-schedule-compression.md](../../report/llm_log/2026-09-21-schedule-compression.md)。
> 2026-09-23 已完成部分归档：阶段 0、第一阶段任务与 Part A（原 §1.3 / §3 / §4.1 / §5 阶段 0–1）原文与完成证据移入 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)，本文只保留未完成部分。为不打断既有引用（onboarding、gate issue #19–#21、README），原 §2 / §4.2–4.4 / §5 阶段 2–3 / §6 编号保持不变；原 §3 位次改为"已完成部分归档与当前起点"，§4.1 保留占位节指向归档。
