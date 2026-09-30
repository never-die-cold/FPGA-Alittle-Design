# Part B 验收清单（verify/bench 线执行计划）

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

- [ ] `design_v1.md` §12/§13 端口位宽逐条落实（`id_ex_stage.v` / `mem_wb_stage.v` / `forwarding.v` / `hazard.v`）
- [ ] `run_iverilog.sh` 提供冻结名 `v1_fwd` / `v1_nofwd`，且 `all` 包含两档（§8.5 / §14.1）
- [ ] 两档由同一文件列表 + elaboration 参数 `ENABLE_FORWARDING=1/0` 产生，无复制 RTL（D3）
- [ ] 编译无隐式 wire、位宽截断、组合环路警告（§13.6）
- [ ] `core_top` 对外端口不变，`soc_top` 零改动可编译（§13.3/§13.6）

## 3. 验收门禁总表（10/4 对照，全部来自契约 §14.1/§14.3）

| 门禁 | 入口/判据 | 执行线 |
|:---|:---|:---|
| v1+转发 | `bash sim/scripts/run_iverilog.sh v1_fwd` 全 PASS | verify |
| v1 无转发 | `bash sim/scripts/run_iverilog.sh v1_nofwd` 全 PASS | verify |
| 全量回归 | `bash sim/scripts/run_iverilog.sh all` 含两档 + 现有 11 tb | verify |
| arch-test | 与 v0 相同用例清单，两档签名一致（`run_arch_test.sh <name> <ext>`） | verify |
| RV32IM | 八种 M、除零、溢出；整核 `tohost=142879` | verify |
| 冒险专项 | R-type 零气泡；load-use 恰 1 气泡；taken 控制转移 1 气泡 | verify |
| CPI 主比 | `gain = (CPI_nofwd − CPI_fwd) / CPI_nofwd ≥ 25%`（D14） | bench |
| Vivado | 同器件同版本，WNS≥0；125 MHz 为非阻塞加分项（D15） | verify |
| 基线锚点 | v0 在 tag `partA-v0`（=`962a4f5`）复现；v1 两档同一 commit | verify |

## 4. tb 备货清单（jianglibo 交付应含，never-die-cold 验收时逐项核对断言点）

| tb | 覆盖契约 | 必查断言 | 状态 |
|:---|:---|:---|:---|
| `tb_forwarding.v`（单元） | §8.6 | 无命中 / x0 / `src_used=0` / 三单命中 / 多重命中优先级；`enable=0` 时 sel=00；`rs1_sel/rs2_sel` 编码 00=RF 01=WB 10=MEM 11=EX | **已闭环（9/30）：对 jianglibo 真 DUT 25 例一次通过（R2–R5 复验，data/logs/2026-09-30-r2r5-verify/）** |
| `tb_hazard.v`（单元） | §13.2 | 两档停顿方程；`redirect && front_stall == 0` 互斥断言 | **已闭环（9/30）：对真 DUT 16020 组合穷举一次通过（含互斥不变量，data/logs/2026-09-30-r2r5-verify/）** |
| `tb_mem_wb_stage.v`（单元） | §12.6 | 正常捕获、气泡覆盖旧槽、复位清 valid、无 hold 端口 | **RTL 线已自写并接入回归（R2–R5，9/30 复验 PASS）** |
| 整核转发专项（新增或扩 tb_core_fwd） | §8.6 | ALU→ALU/branch/JALR/store/muldiv；连续 R-type RAW 零气泡；load-use 恰 1 拍；关转发结果一致且可见 RAW 气泡 | 等 RTL |
| 整核 hazard 专项 | §9.6 | taken 冲刷 1 槽、not-taken 不冲刷；branch 遇 RAW 先停顿再裁决；stall 期间生产者只提交一次；气泡不写 regfile/DMEM/不启动 muldiv | 等 RTL |
| 整核 RV32M | §10.6 | start 仅一次、等待期无提交、done 进正确 rd、紧随消费者两档结果一致 | 等 RTL |
| 复用现有 | — | `tb_muldiv`（单元不回归）、`tb_core_test`（38 用例）、`tb_core_coremark`（口径见第 5 节） | 已有 |

注：两个预写 tb 均未接入 `run_iverilog.sh`（DUT 不存在，接入会破坏 `all`）；`forwarding.v`/`hazard.v` 落地的同一提交必须完成接入（单独模式 + all）并使其 PASS，这是 RTL 线 R2/R3 步的验收动作。预写 tb 在 9/29 仅做过"对契约参考模型 stub 的自一致性检查"（临时 stub 不入库），**不构成任何 RTL 验证结论**。

## 5. CPI 口径与 bench 适配（契约 §14.2，D14）

- 主指标：同一 v1 三级核开/关转发对比；v0 仅作参考锚点（v0 CPI≈2.105，不是降幅基线）。
- 计数窗口（两档必须完全一致）：`cycles` = rst_n 释放后到首次终止 tohost 写；`retired` = 同窗口 `wb_valid=1` 拍数；M 指令只计一次；等待拍计入 cycles，不得剔除。
- `data/scripts/cpi_harness.py` 无需修改：解析的 PASS 行格式不变。**需要适配的是 `tb_core_coremark.v` 的计数信号**：当前绑定 v0 内部信号 `dut.instr_valid && !dut.stall`（见 tb 第 76–78 行），v1 下改为 hierarchical 引用 `dut.wb_valid`（WB 提交记录，契约 §6.4）。适配方案（同 tb 兼容 v0/v1，或 v1 独立 tb）由 RTL 线在 10/2 交付时说明，verify 线只验收"同一 tb 文件、同一计数代码跑两档"。
- `bubble_count` 在 v1 下语义变为"无效槽拍数"，仅作波形辅助，不进 PASS 判据。
- 产出归档：原始日志 `data/logs/<date-slug>/`；波形/覆盖 `data/evidence/`；汇总 `data/metrics.csv`（表格链接原始日志，禁止只留手抄数值）。

## 6. XSim 对拍口径（沿用 Part A 惯例）

1. iverilog `all`（含 v1 两档）全 PASS 后，Vivado XSim 以同一 hex、同 plusargs 判据分别跑 `v1_fwd` / `v1_nofwd`。
2. 通过标准：tohost/exit 终值与 iverilog 一致，cycles 差异为 0（同一确定 RTL；若有差异必须定位到工具差异并记录）。
3. 日志归档 `data/logs/<date-slug>/sim_xsim.log`，注明 Vivado 版本（对齐 Part A：2026.1）。

## 7. 上板负责人简报（10/4 前移交）

- 前置：bitstream 只能在 Vivado 门禁（WNS≥0、无 Error/Critical DRC）通过后生成（§14.3）。
- 需要移交物：v1 门禁后 bitstream、对应 commit 号、核时钟频率（125 MHz 未达标则用实测最高通过频率）、Vivado 版本、下载步骤（沿用 `board/setup.md`）。
- 判据口径（§14.4）：只有实际下载 PYNQ-Z2 并观察到约定 LED/tohost 现象才能记"已上板"；`PROGRAM PASSED` 不算。v1 上板证据追加到 `board/logs/<date-slug>/`，与 v0 的 40 MHz 证据分开，**不得借用 v0 证据表述 v1 已上板**。
- 在此之前所有文档/报告中 v1 一律标"待上板"。

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
