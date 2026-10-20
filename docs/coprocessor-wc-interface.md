# CNN 协处理器 WC 一页纸接口

> 唯一契约来源：[C03](contracts/coprocessor-integration-v0.md) 与
> [`design_v1` §17](../src/riscv/design_v1.md#17-j04-协处理器本地-mmio-扩展)。本文只做摘录；
> offset 适用于 PS AXI4-Lite 和离板 mock，PS 物理基址由 Vivado Address Editor 分配。

## 寄存器地址表

| Offset | 名称 | WC 权限/用途 |
|---:|:---|:---|
| `000/004/008` | `IP_ID/VERSION/CAPABILITY` | RO；识别 `COP0`、契约版本与能力 |
| `00C` | `CTRL` | 正常轮次 WC 不写；START/清状态归 RISC-V，PS 仅恢复时 ABORT/SOFT_RESET |
| `010/014` | `STATUS/ERROR_CODE` | RO；ready/busy/done/error/timeout/result_valid 与首错 |
| `018` | `IRQ_ENABLE` | PS 写；done/error/timeout 使能 |
| `01C/020` | `CFG_SEQ/CFG_APPLIED` | PS 写新序号；RO 回执最后提交 |
| `024/028` | `MODEL_ID/WEIGHT_CRC32` | PS 写；模型选择号和完整对齐 payload CRC32 |
| `02C/030` | `ROI_COUNT/TIMEOUT_CYCLES` | PS 写；1–16 与非零 watchdog 拍数 |
| `034/038` | `WORK_ORDER/WORK_ORDER_REV` | PS 写；三类数量、策略上限与修订号 |
| `03C/040/044` | `JOB_ID/CAPTURE_ID/SOURCE_CONFIG_ID` | PS 写；任务、取帧和 ROI 配置关联 |
| `048/04C` | `WEIGHT_ADDR/WEIGHT_BYTES` | PS 写；64 B 对齐地址、manifest 精确长度 |
| `050/054/058` | `TARGET_DESC_ADDR/ROI_ADDR/ROI_STRIDE` | PS 写；描述符、ROI 地址，stride 固定 4096 B |
| `05C/060` | `RESULT_ADDR/RESULT_STRIDE` | PS 写；可选结果 DMA，stride 固定 16 B |
| `064/068` | `MIN_MARGIN_Q/CFG_COMMIT` | PS 写；0–254 阈值，写 1 原子提交 |
| `06C` | `RESULT_INDEX` | RISC-V/PS 写 0–15，选择只读结果快照 |
| `070/074/078/07C` | `RESULT_META/LOGITS/SCORE/SEQ` | RO；逐目标结果与最后提交序号 |
| `080/084` | `PERF_CYCLES/DMA_BYTES` | RO；cop 拍数与实际搬运量 |
| `088/08C` | `FW_ACTUAL_COUNTS/FW_DECISION` | RISC-V 写；WC 只消费/复算核验 |
| `090–0FF` | 保留 | 不新增寄存器；读 0，写按前端规则忽略/报错 |

## 一次完整时序

1. WC/PS 写 shadow、非零递增 `CFG_SEQ`，再写 `CFG_COMMIT=1`；轮询
   `CFG_APPLIED==CFG_SEQ && STATUS.READY=1`。busy 时 commit 返回 `SLVERR`，不排队。
2. RISC-V 等回执和 READY 后写 `CTRL.START=1`；WC 不写 START。离板 mock 可由固件替身执行这一步。
3. 轮询 `STATUS`：BUSY 期间等待；DONE 后确认 `RESULT_VALID=1`，ERROR/TIMEOUT 转恢复流程。
4. 先读 `RESULT_SEQ`；逐目标写 `RESULT_INDEX` 后读 META/LOGITS/SCORE，再复读 RESULT_SEQ；
   序号不变才接受，并按 target_id 与输入描述符二次关联。
5. 消费结果后由 RISC-V 写 `CTRL.CLEAR_DONE=1`（bit 3，W1C），清 DONE 和 RESULT_VALID；
   错误/超时另写 `CLEAR_ERROR=1`（bit 4）。写 1 清灯，读回命令位恒为 0。

## 边界约定

- BUSY：重复 START 零副作用拒绝；配置 commit 拒绝且不排队；在途任务使用 START 时快照。
- 非法写：核侧未对齐、非完整字节使能、越界、写只读均读 0/零副作用，不驻留全局错误；
  PS 侧非法/未对齐访问返回 `SLVERR`。核邮箱 pending 时第二笔写拒绝且不覆盖第一笔。
- 超时：从 START 接受拍计数，达到上限停止新 DMA、丢弃部分结果，清 BUSY，置
  ERROR+TIMEOUT，首错为 WATCHDOG；不得当作 DONE。
- 重复请求：同一 `JOB_ID` 只能发布一次最终判定；邮箱和 CFG_COMMIT 均无隐式队列。
- 旧结果：START 不自动清 sticky DONE/ERROR；新任务前显式 W1C。只在 RESULT_SEQ 改变后读快照，
  不得把旧 RESULT_VALID 或旧结果贴到新 bbox。

## 结果字段

每目标结果固定 16 B、小端：`target_id:u16`，`class_id:u8`（0 bolt/1 nut/2 washer，非法 FF），
valid/low_conf/error 标志，三个 `int8` logits，`margin_q:u8`，`score_q15:u16`，
error/detail:u16，target cycles:u32。`score_q15` 是归一化整数 logit margin，**不是概率**；
LIVE 上报值为 `score_q15/32767.0`，并标注 normalized logit margin。

## 假硬件 mock

mock 只顶替同一逻辑 4 KiB 窗口的已定义 offset `000–08C` 及 `090–0FF` 保留行为；不得伪造新寄存器、
改变权限或把 PS 地址写死为核侧 `0x8001_0000`。它必须模拟 busy 拒 commit、sticky 状态/W1C、
RESULT_SEQ 最后提交、watchdog、`SLVERR` 与恢复序列；START 由固件替身发起。mock PASS 仅表示 WC
适配器离板跑通，不代表实体硬件、综合实现或板级接入通过。
