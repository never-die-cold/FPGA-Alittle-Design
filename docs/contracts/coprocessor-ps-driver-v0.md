# C03 PS 驱动使用档（WC 侧实现、与 JL 对齐）

> 状态：2026-10-20，WC 侧按 C03 §4/§5/§8/§13 实现，已在 `cop_mmio_sim` 上跑通；
> **未上板**。权威契约仍是 [C03](coprocessor-integration-v0.md)，本文只冻结
> PS 的**使用方式**和 JL 需要确认/补齐的接口点，不改任何 C03 冻结项。
> 复现：`bash sim/scripts/run_inspection_python.sh`、
> `bash sim/scripts/run_cop_sim_round.sh`。

## 1. 本文回答的四个问题

1. **软件怎么提交任务**：PS 写 shadow + 数据面，`CFG_SEQ` 后 `CFG_COMMIT=1`；
2. **怎么知道算完了**：轮询 `STATUS.DONE/ERROR/TIMEOUT`，不看 `START`、不要求看见 `READY`；
3. **怎么拿结果**：`RESULT_SEQ` 前后双读 + 逐索引 `RESULT_META/LOGITS/SCORE`，再读 `FW_*`；
4. **出错怎么恢复**：ABORT/等待 !BUSY/W1C 清状态，新 `CFG_SEQ` 重试；同一 `JOB_ID` 只发布一次。

## 2. 一次任务的提交序列（PS 侧，C03 §14 A1/A2）

前置：`STATUS.BUSY=0` 且 `STATUS.UNCONSUMED=0`。`UNCONSUMED=1` 时返回
`STALE_RESULT`，**不写新命令**；先按 §3/§4 持久化并 `CONSUME` 旧终态。
PS **不写** `START`、不写 `FW_*`、不写任何结果寄存器；`CTRL[3:4]` 历史清除位已停用。
`READY` 只是 `!BUSY` 的建议性提示，**任何等待/失败判据都不得使用它**。

1. 写 shadow：`MODEL_ID、WEIGHT_CRC32、ROI_COUNT、TIMEOUT_CYCLES、WORK_ORDER、
   WORK_ORDER_REV、JOB_ID、CAPTURE_ID、SOURCE_CONFIG_ID、WEIGHT_ADDR/BYTES、
   TARGET_DESC_ADDR、ROI_ADDR/STRIDE、RESULT_ADDR/STRIDE、MIN_MARGIN_Q`。
2. 数据面（DMA/DataMover）：
   - 权重 payload 必须与 `WEIGHT_BYTES/WEIGHT_CRC32` 完全一致，否则 `MODEL_VALID` 不得置位；
   - ROI 数量 = `ROI_COUNT`，每张 4096 B；
   - 描述符 16 B/目标：`target_id:uint16`、flags、`roi_index:uint32`、保留 0；
     `target_id/roi_index` 唯一且 `roi_index<ROI_COUNT`。
3. 写新的非 0 `CFG_SEQ`（单调递增、可回绕），再写 `CFG_COMMIT=1`。
   - busy 时 commit 返回 SLVERR 且**不排队**；PS 不应在 busy 时提交。
   - 写 `CFG_SEQ` 会立刻撤掉 `CFG_VALID`（OPEN-3 保守默认）。
4. 只轮询 `CFG_APPLIED==CFG_SEQ` 作为配置回执，**不与 READY 联合**。
5. 固件在 `BUSY=0 && UNCONSUMED=0` 时写 `START`，硬件置 sticky `ACCEPTED[11]`。
   PS 用**独立的 NO_ACK 软件看门狗**等 ACCEPTED；超时返回 `NO_ACK`，不依赖 READY，
   也不依赖硬件 timeout 位。
6. ACCEPTED 后，PS 用**第二个独立的 HW_TIMEOUT 软件看门狗**等互斥终态
   `DONE|ERROR|TIMEOUT`。超时返回 `HW_TIMEOUT`（写 ABORT 产生 ERROR 后 CONSUME）。
   - `ERROR/TIMEOUT`：先读 `ERROR_CODE`，再 `CONSUME`，不发布结果。
   - `DONE`：读结果并校验（§3），持久化成功后 `CONSUME`，再发布 OK。
7. 一笔 `CONSUME`（`CTRL[6]=1`）原子清 `DONE/ERROR/TIMEOUT/RESULT_VALID/ACCEPTED/
   ERROR_CODE`；`RESULT_SEQ` 不清。无终态时 CONSUME 返回 SLVERR 且零副作用。
   **落盘失败禁止 CONSUME**，保留 sticky 证据。

PS 负责的业务门（在提交前短路，不送硬件）：

- `ROI_COUNT=0`：v0 无法表达“有效空帧”（OPEN-11），PS 按 C03 §8 在本地给
  `CHECK_FAIL`（actual 三零），不提交；
- 目标数 > 策略上限（默认 10）：`RECHECK/target_limit`，不截断、不提交；
- 同一 `JOB_ID/WORK_ORDER_REV` 只允许一个最终判定；重复键返回缓存，目标指纹不同则报错。

## 3. 完成与结果读取（PS 侧）

`DONE` 后：

1. 读 `RESULT_SEQ`（`seq1`）。首个成功轮要求非 0；之后必须等于
   `last_consumed_seq + 1`（防复用旧结果；硬复位后序号不保证连续，需重启驱动）。
2. 逐索引写 `RESULT_INDEX=i`，读 `RESULT_META/RESULT_LOGITS/RESULT_SCORE`；
   `META[15:0]` 必须等于描述符顺序里的 `target_id`；
3. 再读 `RESULT_SEQ`（`seq2`）和 `STATUS`：要求 `seq1==seq2`、`RESULT_VALID=1`、
   `DONE=1`、`ERROR=TIMEOUT=0`、`BUSY=0`；
4. 读 `FW_ACTUAL_COUNTS/FW_DECISION`：
   - `FW_DECISION[31:16]` 必须等于 `seq1`（OPEN-6 暂定布局）；
   - 按 `cop_work_order.h::cop_judge` 在同一输入上复算，verdict/reasons/actual 必须逐项一致；
   - PS 的 `inspection_rules.judge` 复算结果：计数必须与固件一致；PS verdict 的严格度
     必须 **≥** 固件（`RECHECK > CHECK_FAIL > CHECK_PASS`）。PS 可以因 `touches_border`
     更严格，但绝不能把固件的 RECHECK 放成 PASS。
5. **持久化成功后才 `CONSUME(result)`**；落盘失败（trace/packet 写失败）不得清灯。
6. 16 B 结果区的 `error/detail/target cycles` 目前不在索引窗（OPEN-2），PS 只消费
   META/LOGITS/SCORE；结果 DMA 落地后再补。

结果映射：

- `class_id 0/1/2 → bolt/nut/washer`，其它值 → `class=null`；
- `score = score_q15/32767`（C02-P7 归一化整数 margin，不是概率）；
- invalid/error 目标：`score=0.0`，但保留可读 class 以与 `cop_judge` 的 actual 对齐；
- `MIN_MARGIN_Q = ceil(min_score*254)`，保证 `low_conf=1` 必然对应
  `score < min_score`，两套阈值不打架；
- `touches_border`：J04 固件 `cop_judge` **没有**读描述符，PS 目前把它作为更严格理由；
  JL 补固件前不得把 border 轮当成固件一致。

## 4. 错误、超时与恢复

| 场景 | PS 动作 | 结果 |
|---|---|---|
| `ERROR` / `TIMEOUT` | 读 `ERROR_CODE`；`CONSUME` 清终态；下轮新 `CFG_SEQ` | 本轮不发布；服务 503 |
| `NO_ACK`（ACCEPTED 缺失） | `ABORT` → 等 `BUSY=0`；若有终态则读码并 `CONSUME` | 本轮不发布；服务 503 |
| `HW_TIMEOUT`（已 ACCEPTED 无终态） | `ABORT` → 等 `BUSY=0`；读码并 `CONSUME` | 本轮不发布；服务 503 |
| 模型 CRC/短包 | `MODEL_VALID=0`、配置不被应用；读码、`CONSUME`、重载、新 `CFG_SEQ` | 本轮不发布 |
| busy 中 ABORT | 终止任务，`ERROR`（ABORTED=12），无部分结果 | 不发布 |
| 空闲 ABORT | 置 `ERROR`（ABORTED=12）；PS 必须 `CONSUME` | 不发布 |
| `SOFT_RESET` | 取消在途任务；**不清** sticky 终态/ACCEPTED/`RESULT_SEQ` | PS 仍需 `CONSUME` |
| 提交前发现 `UNCONSUMED` | 不写新命令；先持久化旧终态并 `CONSUME` | `STALE_RESULT` |

`ERROR_CODE` 现由 A2 定义：`1=TASK_ERROR`（含 loader/model）、`12=ABORTED`、
`13=WATCHDOG`。PS 读码只用于诊断/失败 trace，不据此放行；sim 另有更细的
`transport.error_name`，真实硬件不得依赖。`VERSION/CAPABILITY` 仍读 0（OPEN-9）。

**写权限（A2）**：正常轮次 PS 只写 `CONSUME`；恢复流程才写 `ABORT/SOFT_RESET`。
固件不再在 START 前清终态；`UNCONSUMED=1` 时 START 整笔拒绝。C03 §3.2 的历史
“RISC-V 清状态”分工已由增补 A2 修订。

## 5. 模拟硬件 → 真实硬件：只换两个接缝

驱动只依赖：

```text
transport.read32(offset) / write32(offset, value)
dma.load_model(addr, payload) / load_rois(addr, rois, stride) / load_descriptors(addr, descriptors)
```

- 现在：`CopSim` + `SimDmaPlane`（`src/pynq_host/cop_mmio_sim.py`）；
- 上板：`PynqMmio(mmio, <Address Editor 分配的 PS AXI base>)` 包一层
  `pynq.lib.MemoryMappedIO`；**没有默认 base**，核侧本地 `0x8001_0000` 不得当 PS 地址
  （K1 假硬件约束）。数据面按 J08 的 DataMover/物理 bank 实现 `PynqDmaPlane`
  （当前**故意** `NotImplementedError`，不假装已实现）；
- 服务/引擎/报文/EXE 不需要重写；`CopEngine` 继续产出同样的
  `status/targets/decision/width/height`，并写 `cop_trace.json`；
- 真实链路全部就绪前，`prototype=true` 不得关闭；`/v1/status` 的 `engine`
  必须从 `COP_SIM` 改成真实后端标识。

## 6. JL 需要确认/补齐的接口点

| 级别 | 项 | 现状 / 影响 | 需要的动作 |
|---|---|---|---|
| **阻断** | 固件重复作业 | `cop_job.c::main` 仍只跑一次；C03/A2 的 submit/consume 流程要求按新 `CFG_APPLIED` 反复起任务 | JL 把固件改成等待新 `CFG_SEQ/applied` 的循环，或在 C03 增加“每作业启动”寄存器并冻结 |
| **阻断** | 预启动判定的完成通知 | `count==0/>16`、`>10` 时固件只写 `FW_DECISION`，不写 START，因此没有 ACCEPTED/终态；PS 只能等 NO_ACK 或本地短路 | 冻结一个完成/有效位（`FW_DECISION_VALID` 或带 `CFG_SEQ` 的 `FW_SEQ`）；PS 暂以本地门短路 |
| 高 | `FW_DECISION` 布局 | OPEN-6 暂定 `[31:16] seq/[15:8] reasons/[7:0] verdict`；PS 只经 `cop_regs.decode_fw_decision` 解析 | JL 冻结后写进共用头文件；任何改动同步 `cop_regs.py` |
| 高 | `touch_border` | 固件不读描述符；C03 §8 要求 border→RECHECK | 固件加理由位，或书面确认“PS 侧 gate”是 v0 口径 |
| 高 | `ROI_COUNT=0` 有效空帧 | OPEN-11；PS 本地 CHECK_FAIL，不提交 | 冻结“空帧有效”信号 |
| 中 | `ERROR_CODE` 数值 | RTL 用 `1=TASK_ERROR/12=ABORTED/13=WATCHDOG`；C03 §14 未逐值列出 | JL 把数值写进 C03/共用头文件；PS 目前只做诊断映射 |
| 中 | `VERSION/CAPABILITY` | 仍读 0（OPEN-9）；PS 不做版本/能力协商 | 冻结取值/位图 |
| 中 | 描述符 flags 位 | C03 只说“至少含 touch_border/invalid_roi”，未冻结位号；PS/sim 暂用 bit0/bit1（sim-only） | JL 冻结位号并写进 C02/C03 |
| 中 | 结果 DMA / target_id | OPEN-2：索引窗可读，`RESULT_ADDR` DMA 未实现；索引窗的 target_id 已够 PS 关联 | J08 提供 DMA 后，PS 可切换到 16 B 结果区，仍需 target_id 二次关联 |
| 中 | 物理 bank/地址 | OPEN-1；PS 用占位 DDR 地址 | J08 发布权重/ROI/描述符/结果的实际地址与对齐 |
| 低 | IRQ | OPEN-5；PS 轮询 STATUS | 若启用中断，冻结 `IRQ_ENABLE/IRQ_PENDING/IRQ_ACK` 语义 |
| 低 | CDC/复位深测 | OPEN-4/7；PS 已用 `RESULT_SEQ` 双读/期望序号兜底 | 验证队友扩展 TB；PS 不改协议 |

## 7. 证据与边界

- 寄存器模型：`src/pynq_host/cop_mmio_sim.py`；PS 驱动：`src/pynq_host/cop_driver.py`；
  服务引擎：`src/pynq_host/cop_engine.py`。
- 测试（`bash sim/scripts/run_inspection_python.sh`）：
  `test_cop_mmio.py`（A1/A2：ACCEPTED/UNCONSUMED/CONSUME/互斥终态/ERROR_CODE/NO_ACK/HW_TIMEOUT 前置）、
  `test_cop_driver.py`（ACCEPTED 等待/两个软件看门狗/CONSUME 原子性/旧序号/CRC 重载/重复 JOB_ID）、
  `test_cop_engine.py`（定位/ROI/规则/trace/border/low_conf/异常）、
  `test_cop_service.py`（服务+EXE：一轮、落盘后 CONSUME、去重、503、同 ref 重试、记录）、
  `test_cop_exe_round.py`（完整一轮显示/保存/追溯）。
- 一轮证据：`bash sim/scripts/run_cop_sim_round.sh <output-dir>` →
  `data/logs/2026-10-21-cop-a2-round/run/`（`summary.json`、`screen.png`、
  `records.jsonl`、`service/.../cop_trace.json`、ROI 字节哈希链）。
  2026-10-20 的旧证据保留为 A1/A2 之前的历史版本。
- **边界**：模拟硬件使用脚本/图像派生的合成分类器与 `S_input=1/127` 的 sim-only
  量化；C02 要求 `S_input` 来自正式 manifest（J05/J06 未完成）。因此当前成果是
  **模拟跑通 + 软件跑通**，不是板上跑通，也不是识别精度证据。C03 §13 的 fake 验收
  不等于硬件接入；J04b 的物理 bank/结果 DMA/整机时序仍由 JL/NC 接手。

## 8. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-10-20 | WC 初版：按 C03 §13 落 PS 使用档、驱动/模拟硬件/服务引擎/异常矩阵与一轮证据；列出 JL 阻断项 |
| 2026-10-20 | 并入 JL K1（WC 一页纸）与 K2（片上存储 PLAN）：PS 正常轮次不写 CTRL；`PynqMmio` 强制 Address Editor base、不默认 `0x8001_0000`；登记 READY 窗口与“消费后清 DONE”回执两项待 JL 确认 |
| 2026-10-21 | 并入 C03 §14 A1/A2 + K1 新版 + 固件/RTL：READY=!BUSY 仅建议；ACCEPTED/UNCONSUMED/CONSUME；终态互斥；RESULT_SEQ 每轮递增；NO_ACK/HW_TIMEOUT 两个软件看门狗；PS 落盘成功后才 CONSUME；ERROR_CODE 1/12/13 |
