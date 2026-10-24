# CNN 协处理器 WC 一页纸接口

> 唯一契约来源：[C03](contracts/coprocessor-integration-v0.md) 与
> [`design_v1` §17](../src/riscv/design_v1.md#17-j04-协处理器本地-mmio-扩展)。本文只做摘录；
> offset 适用于 PS AXI4-Lite 和离板 mock，PS 物理基址由 Vivado Address Editor 分配。

## 寄存器地址表

| Offset | 名称 | WC 权限/用途 |
|---:|:---|:---|
| `000/004/008` | `IP_ID/VERSION/CAPABILITY` | RO；识别 `COP0`、契约版本与能力 |
| `00C` | `CTRL` | RISC-V 写 START；PS 写 CONSUME，恢复时可写 ABORT/SOFT_RESET |
| `010/014` | `STATUS/ERROR_CODE` | RO；含 ACCEPTED、UNCONSUMED、互斥终态与首错 |
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

## 现行 submit / 消费时序

`STATUS.READY=!BUSY` 仅为建议性诊断，PS 严禁等待或据此判失败。硬回执是 sticky
`STATUS.ACCEPTED`（bit 11）；`STATUS.UNCONSUMED`（bit 12）等于 DONE|ERROR|TIMEOUT。

1. 若 UNCONSUMED=1，返回 `STALE_RESULT`，不写新命令。否则 WC/PS 写 shadow、递增的非零
   `CFG_SEQ` 和 `CFG_COMMIT=1`，只等待 `CFG_APPLIED==CFG_SEQ`，不与 READY 联合。
2. RISC-V 写 `CTRL.START=1`；WC 不写 START。PS 等 ACCEPTED，独立软件看门狗到期返回 `NO_ACK`。
3. ACCEPTED 后轮询互斥终态 DONE|ERROR|TIMEOUT；第二个软件超时到期返回 `HW_TIMEOUT`，
   不依赖硬件主动置 TIMEOUT。ERROR/TIMEOUT 时先读 ERROR_CODE，再写 `CTRL.CONSUME=1`（bit 6）。
4. DONE 时先确认 RESULT_VALID，读取期望 `RESULT_SEQ`；逐目标写 RESULT_INDEX 后读取
   META/LOGITS/SCORE，并复读 RESULT_SEQ。序号不符即旧结果，拒绝使用。
5. 结果校验并成功落盘后，PS 才写 CONSUME；该一笔原子清 DONE/ERROR/TIMEOUT/
   RESULT_VALID/ACCEPTED/ERROR_CODE，但不清 RESULT_SEQ，然后返回 OK。落盘失败禁止清灯。

## 边界约定

- BUSY 或 UNCONSUMED：重复 START 整笔零副作用拒绝；固件禁止在 START 前清终态。
  配置 commit 在 BUSY 时拒绝且不排队；在途任务使用 START 时快照。
- 非法写：核侧未对齐、非完整字节使能、越界、写只读均读 0/零副作用，不驻留全局错误；
  PS 侧非法/未对齐访问返回 `SLVERR`。核邮箱 pending 时第二笔写拒绝且不覆盖第一笔。
- 终态：DONE/ERROR/TIMEOUT 任意时刻最多一个为 1；TIMEOUT 不再同时置 ERROR。
  硬件 watchdog 仍可进入 TIMEOUT，但不能替代 PS 的 NO_ACK/HW_TIMEOUT 软件看门狗。
- 重复请求：同一 `JOB_ID` 只能发布一次最终判定；邮箱和 CFG_COMMIT 均无隐式队列。
- 旧结果：START 不自动清终态；只有 PS 的 CONSUME 能软件清除。RESULT_SEQ 每轮成功结果递增，
  CONSUME 不清序号；序号不符不得把旧结果贴到新 bbox。

## 结果字段

每目标结果固定 16 B、小端：`target_id:u16`，`class_id:u8`（0 bolt/1 nut/2 washer，非法 FF），
valid/low_conf/error 标志，三个 `int8` logits，`margin_q:u8`，`score_q15:u16`，
error/detail:u16，target cycles:u32。`score_q15` 是归一化整数 logit margin，**不是概率**；
LIVE 上报值为 `score_q15/32767.0`，并标注 normalized logit margin。

## 假硬件 mock

mock 只顶替同一逻辑 4 KiB 窗口的已定义 offset `000–08C` 及 `090–0FF` 保留行为；不得伪造新寄存器、
改变权限或把 PS 地址写死为核侧 `0x8001_0000`。它必须模拟 ACCEPTED/UNCONSUMED、互斥终态、
CONSUME 原子清除、RESULT_SEQ 递增、NO_ACK/HW_TIMEOUT 软件超时、`SLVERR` 与旧序号拒绝；START
由固件替身发起。mock PASS 仅表示 WC 适配器离板跑通，不代表综合实现或板级接入通过。
