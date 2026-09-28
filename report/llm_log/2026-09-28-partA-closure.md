# [2026-09-28] 协作记录：Part A 收口契约冻结（SoC 计时计数器 / DMEM 预载 / 软复位语义）

> 标签：#riscv #soc #coremark #架构决策
> 平台：OpenCode ｜ 模型：deepseek-v4.1-flash
> 相关 commit：（Step 0 契约提交）
> 用途：Part A 完全收口的决策与范围记录；接口冻结全文入 `src/riscv/design_v0.md` §3.3/§5.8

## 1. 任务与初始提示词

> "看一下 PartA 还有什么收口工作没有做呢，我想把 PartA 完全完结"

范围裁决（用户确认，2026-09-28）：

1. **实物收口**：SoC 计时计数器（RTL+仿真）与 DMEM 镜像预载（RTL+仿真）本轮全做；**板上 CoreMark 跑分归 M3**（需重出 bitstream + 板卡时段）。
2. **benchmark v0.1 / CPI harness 骨架**：按 gate #19 原文补，不用 CoreMark 替代。
3. **复位后重跑缺口**（验证线 2026-09-26 反馈）：契约写明 + `tb_soc_top` 增加重跑断言。
4. 本次全部改动走**一个 PR**；`src/riscv/plan_calendar.md` 为未评审草案，不入库。

## 2. 冻结决策（入 design_v0.md）

1. 计时计数器固定 `0x8000_8000`：32 位自由运行、每核时钟 +1、`rst_n=0` 期间清零；**同拍组合读**、只读；写被忽略且**不得落入 DMEM**（该地址 `addr[14:2]` 会撞 DMEM 字 0，必须在写路径关门）。
2. 地址放 32KB 数据区间之外：DMEM 内任何地址都是合法数据地址，MMIO 混入会产生"误写不可见"歧义（沿用 `docs/coremark.md` §3.3 论证）。
3. DMEM 预载：`dmem.v` 增加 `INIT_FILE`（默认空 = 全 0，保持既有模块级 tb 行为）；`soc_top` 增加 `DMEM_INIT_FILE`，与 IMEM 预载同一 hex——哈佛双口加载语义，与 `tb_core_coremark` 仿真模型一致。
4. 软复位语义：`rst_n` 拉低只复位核内寄存器与 PC、清零计时计数器，**不清 IMEM/DMEM**。`hello_v0` 第二次运行以旧 `tohost`（13）为种子 → `sum=65`、`tohost=65`、LED=`0001`；该行为是契约的一部分，与首次 `1101` 主判据分开断言。
5. 板上修订证据边界：09-26 的 LED=`1101` 上板证据对应 `db9fe33`（timer/preload 之前）；本次修订只做仿真验证，**不声称新修订已上板**，板上复验随 M3 CoreMark 跑分一并执行。

## 3. 收口工作分解（古法编程，逐步交付）

| 步 | 内容 | 关键文件 | 验证 |
|:--|:---|:---|:---|
| 0 | 契约冻结 + 本文 | `design_v0.md`、`docs/coremark.md` | `git diff --check` |
| 1 | timer + DMEM 预载 RTL | `soc_top.v`、`dmem.v` | `run_iverilog.sh soc/imem/dmem` |
| 2 | 复位重跑断言 + timer 分层检查 | `tb_soc_top.v` | `run_iverilog.sh soc` |
| 3 | SoC 级预载/计时小固件端到端 | `src/riscv_fw/soc_check.c`、`tb_soc_check.v` | `run_iverilog.sh soc_check` |
| 4 | benchmark v0.1 + CPI harness | `src/riscv_fw/bench_v0_1.c`、`data/scripts/cpi_harness.py` | `run_iverilog.sh bench` |
| 5 | 指标/文档/门禁收口（含 Vivado 重综合） | `metrics.csv`、`plan.md`、`sim/README.md`、issue #19 | `run_iverilog.sh all` + arch-test |

## 4. 当前结论

- Step 0–5 已连续完成：计时器、DMEM 双预载、软复位重跑、真实固件端到端、benchmark/CPI harness 均有仓库内一键复现证据；`docs/coremark.md` #2/#7 已关闭。
- `run_iverilog.sh all`（含 CoreMark、benchmark、两个 SoC tb）及 arch-test `add-01/addi-01/and-01` 全部 PASS。
- Vivado 2026.1：core OOC 10 ns 未收敛（WNS=-1.935 ns，Part B 遗留）；SoC 40 MHz WNS=+1.153 ns、DRC 门禁通过并生成 bitstream。
- 本次修订未下载上板；板上复验仍归 M3，禁止把新 bitstream 记成已上板。
- gate #19 的个人项（HDLBits / 备考 / 每人 ≥2 llm_log）需组长自查确认后签字关闭。

## 5. 实现与证据

- Step 1：`soc` / `imem` / `dmem` PASS。
- Step 2：`tb_soc_top` 增加计时器分层检查与第二次运行 `65/0001` 判据，`soc` PASS。
- Step 3：`soc_check.c` 通过真实 `lw/sw` 验证 `.data` 预载、计时器递增与写别名保护，`soc_check` PASS。
- Step 4：`bench_v0_1.c` checksum=`0x1385CBD1`；3446 cycles / 1205 instrs，CPI=2.860。
- Step 5：全量日志位于 `data/logs/2026-09-28-partA-closure/`；实现报告位于 `build/reports/`。

## 6. 理解门槛记录

用户完成两轮共 6 题并通过：

1. 解释 DMEM 必须与 IMEM 双预载，因为 `start.S` 只清 `.bss`，不会复制 `.data/.rodata`。
2. 推导 `0x8000_8000` 的 `addr[14:2]` 折叠为 0，说明写屏蔽保护 `DMEM[0]`。
3. 指出现有 SoC tb 首版未第二次释放复位，不能证明 `tohost=65`。
4. 说明 before/after 判据不依赖镜像初值，优于硬编码 `DMEM[0]==0`。
5. 解释 posedge active region 与 NBA 更新顺序，以及采样前 `#1` 的必要性。
6. 区分白盒 `force` 的外壳层验证与真实 RISC-V 指令端到端覆盖。

用户随后明确要求 Step 3–5 连续完成；本轮仅豁免逐步等待，仍维持每次修改不超过 100 行，未执行 commit。

### Step 3–5 最终理解题（通过）

1. **`soc_check` 双判据**：用户说明 `preload_word=0x13579BDF` 位于 `.data`，用于发现 DMEM 镜像未预载、镜像错误或链接布局不一致；`mem0_before/after` 则包围真实 timer store，用于发现 `!timer_hit` 写门缺失导致的 `DMEM[0]` 别名污染。两类故障互不蕴含，tb 再从外壳层独立复核。
2. **CPI 显示差异**：用户正确推导 `3446000/1205=2859.75…`；Verilog 整数定点显示截断为 `2.859`，Python harness 以浮点三位小数舍入为 `2.860`。metrics 采用 harness 的规范生成口径，底层测量量仍是同一组 `3446/1205`。
3. **WNS 与上板边界**：用户区分 core OOC 的 10 ns/100 MHz 目标（WNS=-1.935 ns，Fmax≈83.8 MHz）与完整 SoC 的 25 ns/40 MHz 约束（WNS=+1.153 ns）；并指出生成 bitstream 只证明工具链实现通过，未满足“实际下载 + 人工观察 LED”的上板定义，旧提交 `db9fe33` 的实物证据不能转移给本修订。

判定：**3/3 通过**。用户能够从源码、仿真调度、统计公式与时序报告四个层次解释本轮改动；本轮开发理解门槛完成。若后续要求 commit，仍按 `understand-gate` 做最终 diff 范围确认并由用户明确授权提交。

## 7. 经验沉淀

- 触发条件：任何"留下'提案值'的跨团队接口"（本例计时器地址）都会阻塞板上路径；收口时先冻结契约再写码，能让 RTL/tb/固件三处同语义。
- 排查步骤：**MMIO 放界外仍要防写别名**——`addr[14:2]` 索引的 DMEM 会把界外地址卷回字 0，写路径必须显式关门。
- 适用范围：换核/换存储容量仍成立；"软复位不清数据存储器"是所有"用自身状态当输入"固件的通用陷阱。
