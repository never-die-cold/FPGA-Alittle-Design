# Part C 验收清单（verify/bench 线执行计划）

> 2026-10-07 执行结果见 [收口报告](../report/module1-closure.md) 和 [复现清单](module1-reproduction.md)。以下复选框为交付前计划快照；当前状态以上述原始证据为准。
> 当前四档名称为 v1_nofwd／v1_fwd／v1_fwd_bht1／v1_fwd_bht2；v0 是外部 tag 锚点。
> 本轮无本地 Vivado/XSim；不重复宣称执行历史硬件验证。

> 是什么：Part C（v1 + 可切换 BHT）交付后的验证、四档数据采集与 M1 收口验收执行清单。
> 给谁看：never-die-cold（verify+bench 线，执行人）、jianglibo（RTL 线，交付对照）、watercopper（bench/四档指标）、上板负责人（第 7 节简报）。
> 什么时候读：Part C RTL 交付前对照第 2–4 节备货，交付日按第 8 节逐项执行，10/4 对照第 3 节门禁验收（与 Part B 一并收口，[issue #21](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/21)）。
> 唯一权威：`src/riscv/plan.md` §4.3 + `src/riscv/design_v1.md` §16/D17；验收 commit 由 RTL 提交后回填。
> 契约现状（2026-10-06）：Part C §16/D17 已冻结，BHT RTL、专项 tb 与同 CoreMark 四档入口已完成 Icarus 回归；arch-test/XSim/Vivado/资源/上板仍待验证。
> 本文档只做执行对照，不复制契约条款；不改 RTL、不改脚本。

## 1. 角色边界

| 线 | 负责人 | 本文档内的职责 |
|:---|:---|:---|
| RTL（dev/rtl） | jianglibo | 先收口 Part B，再交付 Part C RTL 与 tb，对照第 2/4 节清单自检交付完整性 |
| verify（dev/verify） | never-die-cold | 独立回归、XSim 对拍、证据归档、验收核对 |
| bench（benchmark/四档指标） | watercopper 主责，never-die-cold 获授权协作 | 自写 benchmark 备货、四档 CPI/命中率采集、metrics 入档、对比报告初稿 |
| 上板 | 专人（非上述三线） | 按第 7 节简报下载与观察，追加 `board/logs/` |

## 2. 交付前置（RTL 线自查，Part C RTL 交付前）

- [x] **Part B 前置闭合**：`v1_fwd` / `v1_nofwd` 已接入脚本且 `all` 回归通过
- [x] **Part C 契约冻结**：端口、三档、恢复拍序和统计通道已写入 `design_v1.md` §16/D17
- [x] 三档由同一 RTL 顶层 parameter 切换，四档入口已冻结并接入脚本
- [x] 命中率由 tb 层次化单拍事件统计，与 CPI 共用窗口
- [x] `core_top` 对外端口不变，`soc_top` 零改动可编译；Verilog-2001 核顶编译通过
- [ ] benchmark 交付物就位：Dhrystone 思路自写整型 benchmark（循环/数组/函数调用/位运算/乘法混编）C 源码 + 编译脚本（`src/riscv_fw/`）+ 反汇编归档
- [ ] arch-test 扩展子集清单列全（RV32IM 等，不少于 Part B 集合），明确四档运行矩阵（`docs/coremark.md` §6.4 口径）

## 3. 验收门禁总表（10/4 对照，全部来自 plan §4.3 + design_v1 §14）

| 门禁 | 入口/判据 | 执行线 |
|:---|:---|:---|
| Part C 功能回归 | `bash sim/scripts/run_iverilog.sh all` 含 BHT 新档 + v1 两档 + 现有 tb，全 PASS | verify |
| BHT 档单独回归 | 新档入口全 PASS（入口名以契约冻结为准，冻结前不抢跑命名） | verify |
| arch-test | 扩展子集全跑：BHT 档与 v1 两档签名一致（`run_arch_test.sh <name> <ext>`） | verify |
| CPI 主比 | `gain_total = (CPI_nofwd − CPI_fwd+BHT) / CPI_nofwd` 必须实测；25% 为组合优化尽力目标（§4.3） | bench |
| CPI 阶梯留档 | `gain_fwd`（Part B D16 回归门槛 ≥8.0%）与 BHT 净贡献（fwd+BHT 相对 fwd）分列入 metrics.csv | bench |
| BHT 命中率 | 2-bit 在含循环 benchmark 上命中率可统计（计数 vs 波形双源核对）且显著优于关闭档（静态不跳）；1-bit/2-bit 对比留档 | bench |
| Vivado | 同器件同版本；实测最高通过频率点 WNS≥0；125 MHz 为非阻塞加分（D15）；四档资源（LUT/FF/BRAM）入表 | verify |
| 基线锚点 | v0 = tag `partA-v0`（=`962a4f5`）；v1 四档同一 RTL/commit，仅参数不同 | verify |
| 降级预案核对 | 若 L3 触发（关闭 BHT + 默认冲刷）四档退化三档；CoreMark 卡住退自写 benchmark——报告必须注明降级范围，不得标完整目标版通过（§4.3 风险预案） | verify |

## 4. tb 备货清单（jianglibo 交付应含，never-die-cold 验收时逐项核对断言点）

| tb | 覆盖契约 | 必查断言 | 状态 |
|:---|:---|:---|:---|
| `tb_branch_predict.v`（单元） | §4.3 范围 | 三档初值、更新时机、方向翻转和饱和 | Icarus PASS（21 checks） |
| `tb_core_bht_flow.v` | §4.3 冲刷逻辑 + 命中率 | 恢复 PC、正确预测零冲刷、错误路径 regfile/DMEM/muldiv 零副作用 | 三档 Icarus PASS |
| `tb_core_coremark.v` | §4.3 CPI + 命中率 | 同窗口计数；hit+miss=lookup；四档 CRC/retired 一致 | 四档 Icarus PASS；外部复验待执行 |
| 复用现有 | — | `tb_core_fwd`（转发/气泡，其边界节已预留"Part C 上 BHT 后按命中率变化"对照点）、`tb_core_test`（38 用例）、`tb_core_coremark`（四档同 hex）、`tb_core_muldiv`、`tb_arch_test`；单元 tb 不回归 | 已有 |
| benchmark / arch-test 备货 | §4.3 | 自写 benchmark 四档同一 hex；arch-test 扩展子集清单；`docs/coremark.md` §6.4 四档矩阵（同 golden，任一档 CRC 不符即该档 FAIL） | bench 线备货 |

注（**Part B 教训，硬性**）：预写 tb 在 DUT 不存在时**不得接入** `run_iverilog.sh`——接入即破坏 `all`（Part B 9/29 实证）；交付前只允许对契约参考模型 stub 做自一致性检查（临时 stub 不入库），**不构成任何 RTL 验证结论**。`branch_predict.v` 落地的同一提交必须完成 tb 接入（单独模式 + `all`）并 PASS，这是 RTL 线交付的验收动作。`tb_branch_predict.v` 预写只能推进到"断言点计划稿"，不得提前声明覆盖。

## 5. CPI 口径与四档阶梯（§14.2 沿用 + plan §4.3）

- 四档定义与角色：**v0 仅锚点**（CPI 2.105 @ CoreMark 2K/32、bench v0.1 2.860；2026-09-20 口径重定义后不作降幅基线）；**v1_nofwd = 唯一降幅基线**；v1_fwd = Part B 中间档；**v1_fwd+BHT = Part C 主交付档**。
- 三级公式（同一套）：
  - `gain_fwd = (CPI_nofwd − CPI_fwd) / CPI_nofwd`——Part B D16 回归门槛 ≥8.0%；
  - `gain_total = (CPI_nofwd − CPI_fwd+BHT) / CPI_nofwd`——Part C §4.3 组合尽力目标 25%；
  - `BHT 净贡献 = CPI_fwd − CPI_fwd+BHT`——负值即回归，必须定位后重测。
- 计数窗口（**四档完全一致**）：rst_n 释放至首次 `tohost_exit` 写；retired 按 `dut.mem_valid` 计，M 只计一次；等待与误预测气泡全部计入 cycles。同 hex、初始化、终止条件和计数代码。
- 命中率按 §16.2 已冻结：tb 在真实 `branch_resolve` 事件统计 lookup／hit／miss，共用 CPI 窗口；每拍互斥且 hit+miss=lookup。关闭档事件全 0，命中率不适用；静态方向命中率如推导须另标来源。
- 当前 tb 已绑定 `dut.mem_valid`（契约逻辑 wb_valid），harness 不另造计数口。执行与原始数据见[收口报告 §2–4](../report/module1-closure.md)，同一 tb 文件跑四档。
- 产出归档：原始日志 `data/logs/<date-slug>/`；波形/覆盖 `data/evidence/`；四档各行入 `data/metrics.csv`（链接原始日志，禁止手抄数值）；四档对比报告入 `report/`（§4.3 交付物，含测试条件与日志索引）。

## 6. XSim 对拍口径（沿用 Part A/B 惯例）

1. iverilog `all`（含在库各档）全 PASS 后，Vivado XSim 以同一 hex、同 plusargs 判据分别跑四档。
2. 通过标准：tohost/exit 终值与 iverilog 一致；同档 cycles 差异为 0（有差异必须定位到工具差异并记录）；BHT 档另核对命中率计数与 iverilog 一致。
3. 日志归档 `data/logs/<date-slug>/sim_xsim.log`，注明 Vivado 版本（对齐既有口径：2026.1）。

## 7. 上板负责人简报（验收日前移交）

- 前置：bitstream 只能在 Vivado 门禁（WNS≥0、无 Error/Critical DRC）通过后生成（§14.3）。
- 需要移交物：上板档（建议 v1_fwd+BHT 主档）bitstream、对应 commit 号、核时钟频率（125 MHz 未达标则用实测最高通过频率；未经 WNS≥0 不得把板载 125 MHz 直接入核——D15）、Vivado 版本、下载步骤（沿用 `board/setup.md`）。
- 判据口径（§14.4）：只有实际下载 PYNQ-Z2 并观察到约定 LED/tohost 现象才能记"已上板"；`PROGRAM PASSED` 不算。Part C 上板证据追加 `board/logs/<date-slug>/`，与 v0 40 MHz、Part B 证据分开，**不得借用低档位证据表述高档位已上板**。
- 在此之前所有文档/报告中 Part C 配置一律标"待上板"。

## 8. 执行清单（Part C RTL 交付日 verify + bench 当日照单执行；10/4 对照第 3 节验收）

1. `git fetch` 确认验收 commit；记录 commit 号与工具版本（iverilog 13.0 / Vivado 2026.1）。
2. 核对 Part B 前置已闭合（第 2 节第 1 条）：v1 两档在 `all` 中全 PASS 且复验在案，否则 Part C 不开工。
3. `bash sim/scripts/run_iverilog.sh all`——确认含 BHT 新档，全 PASS，原始日志入档；新档单独复跑留独立日志（验收引用用单独日志，不用 `all` 混合日志）。
4. arch-test 扩展子集：BHT 档与 v1 两档各跑一遍，签名一致性核对；v0 锚点按需在 tag `partA-v0` 上复现。
5. CPI：bench 模式四档同 hex 同参数采集，`cpi_harness.py` 出数；计算 `gain_fwd` / `gain_total` / BHT 净贡献；命中率与冲刷次数统计；`metrics.csv` 入行。
6. Vivado：四档（或主档 + 关闭档对照 + 说明）综合实现，七件套报告入 `build/reports/`，WNS 核对；LUT/FF/BRAM 资源入 metrics。
7. XSim 对拍（第 6 节）。
8. 四档对比报告入 `report/`（底稿：`docs/coremark.md` A.7 G1–G3；四档表 + 测试条件 + 原始日志索引）；`data/logs/<date-slug>/README.md` 汇总命令/版本/commit/PASS-FAIL 明细/遗留问题；CPI 测量流程按 §4.3 标 `#skill候选` 沉淀。
9. 有 FAIL：只归档证据与最小复现，交 RTL 线修复；verify 线不改 RTL。
10. 若触发降级（L3 三档 / 自写 benchmark）：报告显著注明降级范围与原因，验收判定按第 3 节降级预案行执行。

## 9. 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-10-03 | 首版：Part C RTL 交付前备货清单；如实标注契约现状（design_v1.md 尚无 Part C 专章，第 4 节断言点为计划稿待回填） | never-die-cold（verify 线） |
| 2026-10-09 | 补实际四档、mem_valid／tohost_exit 和 tb 事件统计口径；历史复选框与失败数据不回填 | Codex |
