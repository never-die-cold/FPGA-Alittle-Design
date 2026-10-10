# Part B 验收清单（verify/bench 线执行计划）

> **当前入口（2026-10-09）**：下文排期、角色分支和早期复选框为历史执行记录；
> 模块一核＋最小 SoC 已完成收口，见[收口报告](../report/module1-closure.md)
> 与[合并验收](../data/logs/2026-10-07-module1-closure/README.md)。
> 当前重现入口见[复现清单](module1-reproduction.md)，分工见[分支规则](branch-layout.md)。
> 本轮本机 Icarus 为 11.0，原验收为 13.0；本机无 Vivado/XSim，不能产生新时序结论。

> 是什么：Part B（v1 三级流水+转发）交付后的验证、数据采集与验收执行清单。
> 给谁看：never-die-cold（verify+bench 线，执行人）、jianglibo（RTL 线，交付对照）、上板负责人（第 7 节简报）。
> 什么时候读：10/2 RTL 交付前对照第 3–4 节备货，10/3 按第 8 节逐项执行，10/4 验收对照第 3 节门禁。
> 唯一权威：`src/riscv/design_v1.md` 冻结版（dev/rtl `fe80857`，2026-09-28 冻结，D1–D15 已确认）。
> 本文档只做执行对照，不复制契约条款；冲突时以契约为准。

## 1. 角色边界

| 线 | 负责人 | 本文档内的职责 |
|:---|:---|:---|
| RTL（dev/rtl） | jianglibo | 交付 RTL 与 tb，对照第 4 节清单自检交付完整性 |
| verify（dev/verify） | never-die-cold | 独立回归、XSim 对拍、证据归档、验收核对 |
| bench（获授权） | never-die-cold（watercopper 交接） | CPI 三档数据采集与 metrics 入档 |
| 上板 | 专人（非上述两线） | 按第 7 节简报下载与观察，追加 `board/logs/` |

## 2. 交付前置（RTL 线自查，10/2 前）

- [x] `design_v1.md` §12/§13 端口位宽逐条落实（`id_ex_stage.v` / `mem_wb_stage.v` / `forwarding.v` / `hazard.v`）
- [x] `run_iverilog.sh` 提供冻结名 `v1_fwd` / `v1_nofwd`，且 `all` 包含两档（§8.5 / §14.1）
- [x] 两档由同一文件列表 + elaboration 参数 `ENABLE_FORWARDING=1/0` 产生，无复制 RTL（D3）
- [ ] 编译无隐式 wire、位宽截断、组合环路警告（§13.6）
- [x] `core_top` 对外端口不变，`soc_top` 零改动可编译（§13.3/§13.6）

## 3. 验收门禁总表（10/4 对照，全部来自契约 §14.1/§14.3）

| 门禁 | 入口/判据 | 执行线 |
|:---|:---|:---|
| v1+转发 | `bash sim/scripts/run_iverilog.sh v1_fwd` 全 PASS | verify |
| v1 无转发 | `bash sim/scripts/run_iverilog.sh v1_nofwd` 全 PASS | verify |
| 全量回归 | `bash sim/scripts/run_iverilog.sh all`；当前完整列表以脚本为准，不限早期 11 tb | verify |
| arch-test | 与 v0 相同用例清单，两档签名一致（`run_arch_test.sh <name> <ext>`） | verify |
| RV32IM | 八种 M、除零、溢出；整核 `tohost=142879` | verify |
| 冒险专项 | R-type 零气泡；load-use 恰 1 气泡；taken 控制转移 1 气泡 | verify |
| CPI 主比 | `gain = (CPI_nofwd − CPI_fwd) / CPI_nofwd ≥ 8.0%`；旧工作点 8.14%，Radix-4 工作点 10.20%；原 25% 门禁 FAIL 并保留（D16） | bench |
| Vivado | 同器件同版本，WNS≥0；125 MHz 为非阻塞加分项（D15） | verify |
| 基线锚点 | v0 在 tag `partA-v0`（=`962a4f5`）复现；v1 两档同一 commit | verify |

## 4. tb 备货清单（jianglibo 交付应含，never-die-cold 验收时逐项核对断言点）

| tb | 覆盖契约 | 必查断言 | 状态 |
|:---|:---|:---|:---|
| `tb_forwarding.v`（单元） | §8.6 | 无命中 / x0 / `src_used=0` / 三单命中 / 多重命中优先级；`enable=0` 时 sel=00；`rs1_sel/rs2_sel` 编码 00=RF 01=WB 10=MEM 11=EX | **已闭环（9/30）：对 jianglibo 真 DUT 25 例一次通过（R2–R5 复验，data/logs/2026-09-30-r2r5-verify/）** |
| `tb_hazard.v`（单元） | §13.2 | 两档停顿方程；`redirect && front_stall == 0` 互斥断言 | **已闭环（9/30）：对真 DUT 16020 组合穷举一次通过（含互斥不变量，data/logs/2026-09-30-r2r5-verify/）** |
| `tb_mem_wb_stage.v`（单元） | §12.6 | 正常捕获、气泡覆盖旧槽、复位清 valid、无 hold 端口 | **RTL 线已自写并接入回归（R2–R5，9/30 复验 PASS）** |
| 整核转发专项（扩展整核 tb） | §8.6 | ALU→ALU/branch/JALR/store/muldiv；连续 R-type RAW 零气泡；load-use 恰 1 拍；关转发结果一致且可见 RAW 气泡 | **已接入 `v1_fwd`/`v1_nofwd` 与 `all`，PASS** |
| 整核 hazard 专项 | §9.6 | taken 冲刷 1 槽、not-taken 不冲刷；branch 遇 RAW 先停顿再裁决；stall 期间生产者只提交一次；气泡不写 regfile/DMEM/不启动 muldiv | **已由 `v1_flow`/`hazard` 回归覆盖，PASS** |
| 整核 RV32M | §10.6 | start 仅一次、等待期无提交、done 进正确 rd、紧随消费者两档结果一致 | **已由 `v1_muldiv_flow`/`rv32im` 覆盖，PASS** |
| 复用现有 | — | `tb_muldiv`（单元不回归）、`tb_core_test`（38 用例）、`tb_core_coremark`（口径见第 5 节） | 已有 |

注：9/29 的参考模型 stub 只用于早期红灯，不构成 RTL 结论；当前状态以真 DUT 的仓库内
`forwarding`、`hazard`、`v1_flow`、`v1_muldiv_flow`、`v1_fwd`、`v1_nofwd` 和 `all` 结果为准。

## 5. CPI 口径与 bench 适配（契约 §14.2，D14）

- 主指标：同一 v1 三级核开/关转发对比；v0 仅作参考锚点（v0 CPI≈2.105，不是降幅基线）。
- 计数窗口（各档完全一致）：rst_n 释放至首次 `tohost_exit` 写；`retired` 按 `dut.mem_valid` 计数，M 只退休一次；等待拍全部计入 cycles。
- 适配已在 `sim/riscv/tb_core_coremark.v` 落实；契约 §6.4 的逻辑 `wb_valid` 在当前核映射为 `mem_valid`，不是另一个提交寄存器。不得再按 v0 的 `instr_valid && !stall` 统计 v1。
- 气泡按同窗口无效提交槽计数，并检查 `cycles=retired+bubbles`、分类之和等于 bubbles；四档使用同一 tb/hex/计数代码。证据见[收口报告 §2–3](../report/module1-closure.md)。
- 产出归档：原始日志 `data/logs/<date-slug>/`；波形/覆盖 `data/evidence/`；汇总 `data/metrics.csv`（表格链接原始日志，禁止只留手抄数值）。

## 6. XSim 对拍口径（沿用 Part A 惯例）

1. iverilog `all`（含 v1 两档）全 PASS 后，Vivado XSim 以同一 hex、同 plusargs 判据分别跑 `v1_fwd` / `v1_nofwd`。
2. 通过标准：tohost/exit 终值与 iverilog 一致，cycles 差异为 0（同一确定 RTL；若有差异必须定位到工具差异并记录）。
3. 日志归档 `data/logs/<date-slug>/sim_xsim.log`，注明 Vivado 版本（对齐 Part A：2026.1）。

## 7. 上板负责人简报（10/4 前移交）

- 前置：bitstream 只能在 Vivado 门禁（WNS≥0、无 Error/Critical DRC）通过后生成（§14.3）。
- 需要移交物：v1 门禁后 bitstream、对应 commit 号、核时钟频率（125 MHz 未达标则用实测最高通过频率）、Vivado 版本、下载步骤（沿用 `board/setup.md`）。
- 判据口径（§14.4）：只有实际下载 PYNQ-Z2 并观察到约定 LED/tohost 现象才能记"已上板"；`PROGRAM PASSED` 不算。v1 上板证据追加到 `board/logs/<date-slug>/`，与 v0 的 40 MHz 证据分开，**不得借用 v0 证据表述 v1 已上板**。
- 未取得对应配置的实机证据前标“待上板”；当前 BHT2/40 MHz 已有[下载与人工 LED 观察](../data/logs/2026-10-07-partC-postopt/README.md)，不推广到其他频率/配置。

## 8. 10/3 执行清单（verify + bench 当日照单执行）

1. `git fetch` 确认验收 commit；记录 commit 号与工具版本（iverilog 13.0 / Vivado 版本）。
2. `bash sim/scripts/run_iverilog.sh all`——确认含 v1_fwd/v1_nofwd 两档，全 PASS，原始日志入档。
3. `v1_fwd`、`v1_nofwd` 单独复跑一遍留独立日志（验收引用用单独日志，不用 all 混合日志）。
4. arch-test 与 v0 相同集合，两档各跑一遍，签名一致性核对。
5. CPI：bench 模式分别采 v1_fwd / v1_nofwd（同 hex 同参数），`cpi_harness.py` 出数，`gain` 计算，metrics.csv 入行。
6. Vivado：v1 两档（或仅转发档 + 说明）综合实现，七件套报告入 `build/reports/`，WNS 核对。
7. XSim 对拍（第 6 节）。
8. 汇总 README（`data/logs/<date-slug>/README.md`）：命令、版本、commit、原始输出链接、PASS/FAIL 明细、遗留问题。
9. 有 FAIL：只归档证据与最小复现，交 RTL 线修复；verify 线不改 RTL。

## 9. 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版：按冻结契约 fe80857 制定执行清单；R1 独立复验同日启动（`data/logs/2026-09-29-r1-verify/`） | never-die-cold（verify 线） |
| 2026-10-05 | 增加 40/125 MHz 同 RTL 双档构建入口；具体命令、门禁和上板判据见 `docs/partB-rtl-handoff.md` | Codex（RTL 线） |
| 2026-10-09 | B04：补当前收口入口，校正退休绑定、tohost_exit 窗口和气泡对账；保留历史排期及失败门禁 | Codex |
