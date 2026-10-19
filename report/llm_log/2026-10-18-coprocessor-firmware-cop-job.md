# [2026-10-18] 协作记录：riscv_fw 固件模块——协处理器工单 `cop_job`（MMIO 驱动 + 共用判定）

> 标签：#coprocessor #riscv_fw #验证 #架构决策
> 平台：Codex（VS Code 插件，WSL，夜间自主）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`src/riscv_fw/cop_job.c`（新增）、`src/riscv_fw/Makefile` 随本轮提交；背景见 `2026-10-18-j04-closeout.md`、`2026-10-18-night-autonomous.md`

## 1. 任务与初始提示词

J04 固件：让 **RISC-V 通过本地 MMIO 窗口（`0x8001_0000`）驱动协处理器工单**——提交/轮询、逐目标读结果、跑与主机测试**共用的 PASS/FAIL/RECHECK 判定**、把统计与决策写回寄存器，并用 `tohost` 标记完成。夜间模式：单步闭环、本地 commit、不 push。

## 2. 模型第一版方案

`cop_job.c`（52 行）：
- MMIO 寄存器偏移：`CTRL/STATUS/ROI_COUNT/WORK_ORDER/RESULT_INDEX/RESULT_META/RESULT_SEQ/FW_COUNTS/FW_DECISION`；
- `cop_write`：写前等待 `STATUS_PENDING` 清零、写完再等清零（单笔原子）；
- `count = ROI_COUNT & 31`；`count<=10` 时先 `CTRL=24`（清状态）再 `CTRL=1`（启动），轮询 `DONE|ERROR|TIMEOUT`；
- 逐目标读 `RESULT_META` 组 `class_id/valid/low_conf/error`；调用 `cop_judge(targets, count, order)`（`cop_work_order.h`，与主机测试共用）；
- 写 `FW_COUNTS`（三类数量）与 `FW_DECISION`（`seq<<16 | reasons<<8 | verdict`）；`tohost = 0x4a303400 | verdict`。
- `Makefile`：新增 `COP_TARGET=cop_job`、`COP_SRCS=start.S cop_job.c`，用 `ARCH_I`（RV32I）编译。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败：`make cop_job.elf CROSS=riscv64-unknown-elf-` 成功（`-march=rv32i -mabi=ilp32`）。
2. **未决**：整机/上板未验证；`cop_job` 与 `cop_top` 的真实 AXI/MMIO 联调、核心时序均未跑。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | MMIO 写入需互斥 | 写前写后都要等 `PENDING` 清零 | `cop_write` 双等待 | ✅ 固件构建通过 |
| 2 | 判定规则要与主机一致 | 固化规则应共用同一头文件 | `cop_work_order.h` 复用 | ✅ `firmware` host test PASS |
| 3 | 超业务上限如何处理 | >10 直接 RECHECK，不截断 | `count>10` 走 RECHECK | ✅ 10/16 policy PASS |

## 5. 最终结论

`cop_job` 固件落地：RV32I 编译通过；固件主机测试 `PASS: cop work-order PASS/FAIL/RECHECK, low-confidence and 10/16 policy`。它把 J04 的 MMIO 控制面/结果面串成一条可执行的 RISC-V 工单路径。**整机/上板、与 `cop_top` 的联调仍未验证。**

## 6. 经验沉淀

- 固件与主机测试**共用同一判定头文件**，避免“软件判定”和“RTL 侧判定”两套漂移；
- MMIO 写要**写前写后都等 pending 清零**，保证单笔原子；
- 超过业务上限（>10）直接 **RECHECK**，不截断、不启动部分计算。 #skill候选
