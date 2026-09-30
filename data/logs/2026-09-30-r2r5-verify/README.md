# 2026-09-30 R2–R5 独立复验（dev/rtl 522e819）

> 目的：verify 线对 RTL 线 R2–R5（Part B v1 四个积木模块：forwarding/hazard/mem_wb_stage/id_ex_stage）做合并前独立复验。
> 结论：全量回归 15/15 tb PASS（12 tb + coremark 双跑），零回归；**verify 预写的 tb_forwarding（25 例）/ tb_hazard（16020 组合穷举）对真 DUT 一次通过**——契约 → tb 先行 → RTL 落地的闭环首次走通。

## 环境与对象

| 项 | 值 |
|:---|:---|
| 被测 commit | `522e819`（dev/rtl，Part B R2–R5 模块级落地） |
| 工作方式 | git worktree 检出（sim/build/wt-rtl2，复验后已删除） |
| iverilog | Icarus Verilog 13.0，MSYS2 UCRT64 |
| 命令 | `bash sim/scripts/run_iverilog.sh all` |
| 原始日志 | 本目录 `all-522e819.log` |

## 结果要点

| 项 | 结果 | 说明 |
|:---|:---|:---|
| tb_forwarding（verify 预写） | PASS | 25 例对真 DUT：x0/used=0/三单命中/优先级/门控位/enable=0 全对 |
| tb_hazard（verify 预写） | PASS | 16020 组合穷举 + `redirect && front_stall == 0` 互斥不变量全对 |
| tb_mem_wb_stage / tb_id_ex_stage（RTL 线自写） | PASS | 3 captures / 6 cases |
| 既有 11 个 tb | PASS | CoreMark CPI 2.105 / RV32IM tohost=142879 / soc 软复位重跑，与 9/28 基线逐项一致 |
| coremark 观测行 `errors=1` | 与 9/28 基线逐字节相同 | 既有现象，非回归 |

## 源码评审附注（verify 视角，非阻塞）

- `forwarding.v`：x0 输出 0 优先于一切、enable/used 门控、EX>MEM>WB 优先级、valid/we/ready 全门控——与契约 §8.2/§8.3 及 verify 参考模型一致。
- `hazard.v`：双模停顿方程 `raw_dep && (!enable_forwarding || p_is_load)` 与 §9.2 等价；redirect 含 ex_accept 门控，互斥不变量结构性成立。
- `mem_wb_stage.v`：复位仅清 `mem_valid`（契约 §12.5 明确允许），无 hold 端口，每拍捕获。
- `id_ex_stage.v`：组合级，`decode`/`alu` 以 `.*` 隐式连接（-g2012）。
- 待办提醒：本批为积木模块级，`core_top` 三级化集成（R6+）未开始，`v1_fwd`/`v1_nofwd` 入口尚未出现（契约定结名，届时验收）。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-30 | 首版：R2–R5 独立复验 15/15 PASS，预写 tb 首次闭环 | never-die-cold（verify 线） |
