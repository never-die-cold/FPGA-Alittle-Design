# [2026-10-06] 协作记录：Part B T2 核 OOC Fmax 复测（11.52ns 过 / 10ns 差 9ps）

> 标签：#riscv #验证 #build #工具链
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：被测 `dev/rtl@b93afaa`（T2）；证据随本条记录入库
> 用途：为 RTL 线裁定 T3/T4 提供核 OOC 实测；记录"先核对被测代码在不在 git"的防错动作

## 1. 任务与初始提示词

RTL 线交接（T2 理解门槛通过，需先做 Vivado 核 OOC 复测再定 T3/T4）：

> 依次运行
> `build_fmax.tcl core_top v1_t2_11p52ns 11.520 src/riscv`
> `build_fmax.tcl core_top v1_t2_10ns 10.000 src/riscv`
> 回传：`FMAX RUN DONE` / `WNS` / `Fmax` / `timing_worst_paths.rpt` 前 3 条路径（source、destination、logic levels、route%）。
> 判据：11.52 ns WNS≥0 → 达 v0 86.8；10 ns WNS≥0 → 达 100；否则据最差路径走向定 T3/T4；SoC 125 MHz 不替代核 OOC 门禁。

## 2. 模型第一版方案

切临时分支到被测提交 → 跑两条 `build_fmax.tcl`（OOC 约束递减）→ 提取 WNS/Fmax/前 3 路径 → 归档证据 → 记录。

## 3. 失败现象（真实偏差）

1. **被测代码一开始不在 git**：RTL 线说"没有 commit"时，远端 `dev/rtl` 仍是 `85b94a5`（`git ls-remote` 确认），工作区无 T2 改动。若照命令直接跑，会拿**T2 之前的代码**、却命名 `v1_t2_*`——正是上次复核批评的"用非被测版本出证据"。**先停、要求 push**，确认 `dev/rtl` 前进到 `b93afaa` 后才跑。
2. **10 ns 未过（结果，非流程失败）**：WNS −0.009 ns（差 9 ps、仅 1 个失败端点）。
3. 关键路径**仍在 `if_stage` 控制→`pc`**：最差路径 source 为 `flush_q`（另含一条 `stall_q`），destination 多为 `pc_reg`——未随 T2 完全移出，T3/T4 判定留给 RTL 线。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | "没有 commit" + 命令 | 被测代码不在 git，直接跑会用错代码 | **先核对** `ls-remote` + 工作区，暂停并要求 push | ✅ 待 RTL push |
| 2 | "现在 push 了" | 远端前进到 `b93afaa` | `ls-remote` 复核后切临时分支 | ✅ 确认 b93afaa |
| 3 | 跑 11.520 ns | — | OOC 复测 | ✅ WNS +0.187（0 失败端点），达 v0 86.8 |
| 4 | 跑 10.000 ns | — | OOC 复测 | ❌ WNS −0.009（1 失败端点），差 9 ps |

## 5. 最终结论

- **11.520 ns（86.81 MHz）WNS = +0.187 ns、0 失败端点 → 约束实际通过**：**实测达到 v0 基线 86.8 MHz**（外推 Fmax ≈ 88.2 MHz）。
- **10.000 ns（100 MHz）WNS = −0.009 ns、1 失败端点 → 约束未通过**：**100 MHz 仅差 9 ps**（外推 ≈ 99.9 MHz）。
- 最差路径前 3 条（source→dest / LL / route%）：
  - 11.52：`flush_q→pc_reg[13]`(LL9/81.2%)、`flush_q→mem_result_reg[13]`(LL9/81.2%)、`instr_hold[3]→mem_addr_reg[31]`(LL13/67.6%)
  - 10.00：`flush_q→pc_reg[15]`(LL11/72.4%, 违例)、`flush_q→pc_reg[13]`(LL11/72.3%)、`stall_q→pc_reg[17]`(LL13/66.0%)
- **走向**：仍是 `if_stage` 控制（`flush_q` / `stall_q`）→ `pc`（PC 选择/目标），按 RTL 规则倾向 T4，但 `stall_q` 出发路径仍在，**T3/T4 由 RTL 线裁定**。
- 证据：`data/logs/2026-10-06-partB-t2-fmax/`（两份日志 + `reports/` 关键报告副本）。本次仅为核 OOC，未做 SoC/上板。

## 6. 经验沉淀

- 触发条件：跨线复测前，被测改动可能尚未入库 #skill候选
- 排查步骤：
  1. **跑之前先确认"被测代码在 git 里"**：`git ls-remote origin <branch>` 拿远端真实 HEAD，并检查工作区 `git status`；版本对不上就**停并要求 push**，绝不拿邻近版本冒充。
  2. 复测命令里的 label 与被测 commit 一起写进证据，避免"名称是 T2、代码是旧的"。
  3. 结论使用**约束通过/失败点**口径，外推 Fmax 只作参考（沿用 `2026-10-05-partB-v1-onboard-verify.md` §7 的教训）。
- 适用范围（换题目/换板卡是否成立）：成立；任何"别人改、你来测"的跨线复测都适用。
