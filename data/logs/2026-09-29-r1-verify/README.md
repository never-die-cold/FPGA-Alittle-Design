# 2026-09-29 R1 独立复验（dev/rtl fe80857）

> 目的：verify 线对 RTL 线 `fe80857`（Part B 契约冻结 + R1 decode 源操作数使用标志）做合并前独立复验。
> 结论：全量回归 11/11 PASS，无回归；R1 改动（decode.v +tb_decode.v）功能符合预期。

## 环境与对象

| 项 | 值 |
|:---|:---|
| 被测 commit | `fe80857`（dev/rtl，Part B 契约冻结 + R1；main 当时尚无此提交） |
| 工作方式 | git worktree 检出（`sim/build/wt-rtl`，运行后已删除），主工作区未受影响 |
| iverilog | Icarus Verilog 13.0 (stable) (v13_0)，MSYS2 UCRT64 |
| 命令 | `bash sim/scripts/run_iverilog.sh all` |
| 原始日志 | 本目录 `all-fe80857.log` |

## 结果明细（11/11 PASS）

| tb | 结果 | 关键数值 |
|:---|:---|:---|
| tb_imem | PASS | 同步读/addr[14:2] 索引 |
| tb_dmem | PASS | 异步读/字节写 |
| tb_core_smoke | PASS | tohost=13 |
| tb_core_test | PASS | RV32I 全部 38 用例 |
| tb_core_fwd | PASS | 气泡 A/B/C/D = 0/0/5/0 |
| tb_decode（R1 新增） | PASS | 11 用例（lui/auipc/jal 不使用源；jalr/lw/addi 仅 rs1；beq/sw/add/mul 双源；非法 0） |
| tb_muldiv | PASS | 8 操作 + 边界 + 握手 |
| tb_core_muldiv | PASS | RV32IM tohost=142879 |
| tb_core_coremark | PASS | 21275738 cycles / 10106387 instrs / CPI 2.105（与 9/28 基线一致） |
| tb_bench_v0_1（bench 模式复跑） | PASS | 3446 cycles / 1205 instrs / CPI 2.859 |
| tb_soc_top | PASS | first-run=13/1101，软复位重跑=65/0001 |
| tb_soc_check | PASS | tohost=534f4301 cycles=3000 |

说明：`all` 模式下 tb_core_coremark 编译一次、按 COREMARK 与 BENCH 两组 plusargs 各跑一遍，故 11 个 tb 得 12 条 PASS 记录。

## 评审附注（verify 视角，非阻塞）

1. 契约冻结核验：`design_v1.md` 头部标注"接口契约已冻结（2026-09-28）"，§99 九项全勾，D1–D15 已确认。
2. `run_iverilog.sh` 已接入 `decode` 单独模式并纳入 `all`，符合 workflow 收尾规定。
3. R1 的 uses_rs1/uses_rs2 语义与契约 §9.1 一致（来自指令语义而非位域猜测）：LUI/AUIPC/JAL 为 0，JALR/loads/ALU 单目仅 rs1，branch/store/双目运算为 1。
4. 遗留警告（历史既有，非 R1 引入）：多个 RTL 文件无 `timescale` 声明（从 tb 继承）；imem 预载 hex 字数少于 8192 属预期。可在 Part B 后续步骤顺手补 timescale，避免 XSim 口径差异。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版：fe80857 独立复验 11/11 PASS | never-die-cold（verify 线） |
