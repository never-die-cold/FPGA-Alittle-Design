# C03：CNN 协处理器、RISC-V 与 PS 的 v0 接口契约

> 状态：**JL 已于 2026-10-11 定稿冻结，允许进入 J02**；仍不是已实现接口或板端验收证据。
> 初稿日期：2026-10-10。整数/张量契约见
> [`src/coprocessor/design_v0.md`](../src/coprocessor/design_v0.md)，核现状见
> [`src/riscv/design_v1.md`](../src/riscv/design_v1.md)。
> 冻结基线：控制面 MMIO + AXI4-Lite，数据面 DMA；v0 不启用自定义指令。

## 1. 范围与硬边界

本文冻结控制权、寄存器语义、DMA 数据对象、任务/结果关联、busy/done/error/timeout、
复位、低置信与工单结果衔接。v0 方案不改变 RV32IM 指令译码、
三级流水、转发、BHT 或已有核回归语义。

现状/边界依据为 [v1 核契约](../src/riscv/design_v1.md)、
[检查 V0 建议稿](inspection-v0-contract.md)与[轮次协议 v1.2](vision-sync-protocol-decisions.md)；
其中 10/16 目标口径已冻结为“硬件/协议能力 16、检查 V0 业务策略 10”。

当前核数据口只有 `addr/wdata/be/we/rdata`，没有 `ready/valid`；DMEM 为同拍异步读、
上升沿写。标准 AXI4-Lite 响应允许等待，因此**不得把现有核数据口直接冒充 AXI master**。
v0 在 `soc_top` 增加单周期本地 MMIO 窗口，通过请求/应答 CDC 与协处理器控制域交换；
PS 侧另用真正的 AXI4-Lite slave 访问同一逻辑寄存器映射。

该方案扩展 SoC 地址译码但不改变 ISA/decode。开始实现前仍须把新增 MMIO 地址和 SoC 行为
回写 `src/riscv/design_v1.md`；其当前“地址空间/端口不变、无总线等待”条款不能静默绕过。

## 2. v0 系统分工

```text
PS 软件 / LIVE 服务
  ├─ 定位、scene-gray-border-padding-v1、INT8 输入导出
  ├─ DDR 中准备权重包、ROI、目标描述符
  ├─ AXI4-Lite：提交 config/model/job 描述
  └─ AXI DMA/DataMover：只搬小 ROI、权重和结果
                         │
RISC-V 固件              │       cop_top（计算域）
  ├─ 本地 MMIO 镜像 ─ CDC ─ control/status/result
  ├─ 校验配置后 START    │       dma_ctrl → BRAM
  ├─ 轮询完成/错误        │       128 MAC + 算子链
  └─ 计数、工单判定 ─────┴────── per-target INT8 result
```

- PS 是数据和配置生产者：准备已预处理/量化 ROI、模型包、target_id 和来源标识。
- RISC-V 是检查调度与判定者：等待配置生效、启动、轮询、按目标结果计数并写工单判定。
- `cop_top` 只做数据搬运与整数 CNN，不定位、不画框、不生成 session UUID。
- LIVE 服务把硬件整数结果与同一轮 bbox/协议字段合并；EXE 仍按既有 v1.2 协议消费。
- `isa_extension.v` 仅保留后续研究入口，v0 不例化、不占 opcode、不改 decode。

## 3. 控制面与时钟域

### 3.1 两个前端、一个逻辑寄存器契约

1. **PS 前端**：标准 AXI4-Lite slave，32 位数据、32 位地址、支持 `WSTRB`；一次只处理一个
   outstanding 读和一个 outstanding 写，非法/未对齐访问返回 `SLVERR`。
2. **RISC-V 前端**：`soc_top` 在 `COP_BASE` 命中时屏蔽 DMEM 写并复用读数据；读为核时钟域
   本地镜像的同拍值，写在上升沿进入命令邮箱，不给核增加 wait state。
3. **CDC**：配置、命令和结果均使用“稳定 payload + toggle/ack”或异步 FIFO；多位总线禁止
   逐位双触发器同步。RISC-V 只有在 `CFG_APPLIED`/`RESULT_SEQ` 改变后读取对应快照。

v0 固定 `COP_BASE=0x8001_0000`、窗口 4 KiB。它避开现有 32 KiB DMEM
`0x8000_0000–0x8000_7FFF` 和计时器 `0x8000_8000`。PS 物理 AXI 基址由 Vivado Address
Editor 分配，但寄存器 offset 必须相同。

### 3.2 写权限

- PS 独占写：模型/DMA 地址、字节数、ROI 数、来源 ID、量化阈值和 `CFG_COMMIT`。
- RISC-V 独占写：`START`、完成/错误清除、固件计数和工单判定。
- PS 仅在服务停止或恢复流程中写 `SOFT_RESET/ABORT`；正常轮次不得与 RISC-V 抢控制。
- 状态、错误、性能和逐目标结果由硬件写，PS/RISC-V 只读。
- 每个前端在 RTL 中实施权限；不能只靠软件约定避免双写。

## 4. 寄存器映射

所有 offset 4 字节对齐。保留位读 0、写忽略；未定义 offset 返回 `SLVERR`（PS）或 0
并置 `BAD_ADDR`（RISC-V 邮箱诊断）。

| Offset | 名称 | 方向/写者 | 语义 |
|---:|:---|:---|:---|
| 0x000 | `IP_ID` | RO | 固定 `0x434F5030`（ASCII `COP0`） |
| 0x004 | `VERSION` | RO | `[31:16]` 契约 major，`[15:0]` minor |
| 0x008 | `CAPABILITY` | RO | MAC=128、最大目标=16、支持 debug dump 等位图 |
| 0x00C | `CTRL` | WO | 见 §4.1 |
| 0x010 | `STATUS` | RO | 见 §4.2 |
| 0x014 | `ERROR_CODE` | RO | 首个未清错误码与阶段 |
| 0x018 | `IRQ_ENABLE` | PS | bit0 done、bit1 error、bit2 timeout |
| 0x01C | `CFG_SEQ` | PS | 本次配置序号，非 0，单调递增可回绕 |
| 0x020 | `CFG_APPLIED` | RO | 已原子应用的配置序号 |
| 0x024 | `MODEL_ID` | PS | 正式 manifest 中的 32 位模型 ID |
| 0x028 | `WEIGHT_CRC32` | PS | 完整对齐参数 payload 的 CRC32；SHA256 由 PS 验证 |
| 0x02C | `ROI_COUNT` | PS | 硬件 1–16；检查 V0 策略另限 1–10 |
| 0x030 | `TIMEOUT_CYCLES` | PS | 从 start 接受到完成的 cop 时钟拍上限，0 非法 |
| 0x034 | `WORK_ORDER` | PS | `[7:0] bolt,[15:8] nut,[23:16] washer,[31:24] policy_max` |
| 0x038 | `WORK_ORDER_REV` | PS | 工单修订号，结果原样返回 |
| 0x03C | `JOB_ID` | PS | 本地 uint32 检查号；PS 映射到协议 check_id |
| 0x040 | `CAPTURE_ID` | PS | 软件取帧号；不冒充 RTL `cop_frame_id` |
| 0x044 | `SOURCE_CONFIG_ID` | PS | ROI/定位所用配置 ID |
| 0x048 | `WEIGHT_ADDR` | PS | 64 B 对齐的 32 位物理地址 |
| 0x04C | `WEIGHT_BYTES` | PS | 完整对齐参数 payload 字节数，与 manifest 完全一致 |
| 0x050 | `TARGET_DESC_ADDR` | PS | 16 B/目标的描述符数组，64 B 对齐 |
| 0x054 | `ROI_ADDR` | PS | 第一张 HW INT8 ROI 的 64 B 对齐地址 |
| 0x058 | `ROI_STRIDE` | PS | v0 固定 4096 B |
| 0x05C | `RESULT_ADDR` | PS | 可选 DMA 结果区，64 B 对齐 |
| 0x060 | `RESULT_STRIDE` | PS | v0 固定 16 B；debug 扩展需升 minor |
| 0x064 | `MIN_MARGIN_Q` | PS | C02 的 0–254 整数 margin 阈值 |
| 0x068 | `CFG_COMMIT` | PS | 写 1 请求原子应用；busy 时拒绝 |
| 0x06C | `RESULT_INDEX` | RISC-V/PS | 选择 0–15 号只读结果快照 |
| 0x070 | `RESULT_META` | RO | target_id、class、valid/low_conf/error |
| 0x074 | `RESULT_LOGITS` | RO | 三个有符号 INT8 logits，最高字节保留 0 |
| 0x078 | `RESULT_SCORE` | RO | `[15:0] score_q15,[23:16] margin_q` |
| 0x07C | `RESULT_SEQ` | RO | 完整结果快照序号；最后写/最后跨域 |
| 0x080 | `PERF_CYCLES` | RO | 本任务 cop 计算域拍数，不含 PS/EXE |
| 0x084 | `DMA_BYTES` | RO | 本任务实际搬运字节数 |
| 0x088 | `FW_ACTUAL_COUNTS` | RISC-V | 与 WORK_ORDER 相同的三个 8 位计数 |
| 0x08C | `FW_DECISION` | RISC-V | 判定、原因位与关联的 `RESULT_SEQ` |
| 0x090–0x0FF | 保留 | — | 读 0、写忽略/报错按前端规则 |

### 4.1 `CTRL` 位

| 位 | 名称 | 语义 |
|---:|:---|:---|
| 0 | `START` | W1S 单拍命令；只由 RISC-V 正常使用 |
| 1 | `ABORT` | W1S；终止当前任务，置 `ABORTED` 错误，不保留部分结果 |
| 2 | `SOFT_RESET` | W1S；清运行状态/结果，不清已校验的权重 BRAM和配置影子 |
| 3 | `CLEAR_DONE` | W1C sticky done/result_valid |
| 4 | `CLEAR_ERROR` | W1C error/timeout/error_code |
| 5 | `IRQ_ACK` | W1C PS IRQ pending；不代替清源状态 |

命令位读回均为 0。`START` 在 busy 时被拒并置 `BAD_STATE`，但不得中断原任务。

### 4.2 `STATUS` 位与状态机

| 位 | 名称 | 语义 |
|---:|:---|:---|
| 0 | `READY` | 配置、模型、ROI 描述合法且当前空闲 |
| 1 | `BUSY` | start 已接受，尚未终止 |
| 2 | `DONE` | 全部目标结果完成，sticky |
| 3 | `ERROR` | 任一非 timeout 错误，sticky |
| 4 | `TIMEOUT` | watchdog 终止，sticky，且 ERROR=1 |
| 5 | `CFG_VALID` | `CFG_APPLIED==CFG_SEQ` 且字段检查通过 |
| 6 | `MODEL_VALID` | 当前 MODEL_ID/CRC 的权重已完整装载 |
| 7 | `RESULT_VALID` | RESULT_SEQ 对应完整、原子可读结果 |
| 8 | `DMA_BUSY` | DataMover/AXI DMA 正在搬运 |
| 9 | `IRQ_PENDING` | 给 PS 中断控制器的电平状态 |

法定状态：IDLE=`BUSY=0,DONE=ERROR=TIMEOUT=0`；RUN=`BUSY=1`；DONE=`DONE=1`；
ERROR=`ERROR=1`；TIMEOUT=`ERROR=TIMEOUT=1`。终止状态下 BUSY 必须为 0。
新 START 前固件显式清旧终止状态；硬件不得因下一任务开始静默抹掉未消费错误。

## 5. 原子配置与启动

1. PS 写全部 shadow 字段和新的 `CFG_SEQ`；
2. PS 写 `CFG_COMMIT=1`；硬件仅在 BUSY=0 时校验对齐、长度、数量、阈值和模型 ID；
3. 完整配置通过 CDC 后，最后更新 `CFG_APPLIED`，并置 `CFG_VALID`；
4. RISC-V 轮询 `CFG_APPLIED==CFG_SEQ && READY` 后写 START；
5. START 沿锁存配置快照；之后 PS 的 shadow 写入不得影响在途任务；
6. 完成时先写全部结果/计数/性能，再最后递增 `RESULT_SEQ` 并置 RESULT_VALID/DONE。

`CFG_COMMIT` 在 busy 时返回 `SLVERR` 且不排队，避免“本轮还是下轮”的歧义。
复用相同模型时可保持 MODEL_VALID；MODEL_ID、权重地址/长度或 CRC 改变即撤销它并重新装载。

## 6. 数据面与 DMA

### 6.1 v0 结构

`cop_top` 不自行实现完整 AXI4 master，而由 Vivado AXI DataMover/AXI DMA 负责
DDR 协议；`dma_ctrl.v` 只产生描述符、检查状态/长度并把 AXI-Stream 数据写入本地 BRAM。
这仍是“AXI4-Lite 控制 + DMA 数据面”，同时缩小自研总线验证范围。

- 参数：按 C02 打包全部 O16×I8 权重、bias、multiplier、shift 和对齐填充，完整 payload
  的精确字节数和 CRC 匹配后 MODEL_VALID=1；
- ROI：每目标固定 4,096 个规范 HW INT8 像素；输入装载器在 conv1 读取时为其余 7 个
  输入 lane 生成 0，不经 DMA 传输填充 lane；
- 中间激活：只在片上 ping-pong BRAM，不默认回写 DDR；
- 结果：16 B/目标写 RESULT_ADDR，同时复制到索引结果窗；
- debug：显式 debug 模式才允许逐层 dump，性能报告必须标明关闭/开启。

全分辨率 1280×720 帧不进入此 DMA。PS 先定位、裁剪和预处理，只搬正式 ROI、权重和小结果。

### 6.2 目标描述与结果格式

每个输入目标描述符固定 16 B：字节 0–1 为 `target_id:uint16`，2–3 为 flags，4–7 为
`roi_index:uint32`，8–15 保留且必须为 0。`target_id` 在一轮内唯一，`roi_index<ROI_COUNT`
且也必须唯一；flags 至少含 `touch_border`、`invalid_roi`。bbox 保留在 PS/协议侧，不送 CNN。

每目标 16 B 结果（little-endian）：

| 字节 | 字段 |
|---:|:---|
| 0–1 | target_id |
| 2 | class_id（0/1/2，非法为 0xFF） |
| 3 | valid/low_conf/error 标志 |
| 4–6 | 三个有符号 INT8 logits |
| 7 | margin_q |
| 8–9 | score_q15 |
| 10–11 | error/detail |
| 12–15 | 该目标计算拍数 |

结果顺序必须与输入描述符顺序一致，同时以 target_id 做第二重关联；任一不符整轮 ERROR，
不得只按数组位置把类别贴到 bbox。

## 7. score、低置信与 LIVE 协议

按已冻结的 C02-P7：

- 硬件输出三个 INT8 logits、margin_q、score_q15 和 low_conf；
- RISC-V 使用同一个 `MIN_MARGIN_Q` 作 RECHECK 判断；
- PS 上报 `score=score_q15/32767.0`，文档标注为 normalized logit margin；
- 协议 class 使用字符串 bolt/nut/washer，不能直接暴露不带版本的裸编号；
- prototype/离线结果仍必须置 `prototype=true`，不能因经过寄存器就冒充实时硬件结果。

score 和阈值属于 MODEL_ID/manifest。换模型但沿用旧阈值时 CFG 校验必须失败。

## 8. RISC-V 工单判定 v0

硬件能力保持协议的最多 16 目标；检查 V0 的业务策略暂限 1–10 件，二者分开：

- 工单三个期望数均为非负，总数必须 1–10；
- 定位得到 11–16 个目标时直接 RECHECK，不截断、不启动部分 CNN；
- 有效空场景对非零工单为 CHECK_FAIL，actual 三类均为 0；它不是 NO_VIDEO；
- 任一 invalid ROI、touch_border、CNN error、非法 class 或 low_conf → RECHECK；
- 全部目标可靠时计数，`delta=actual-expected`，全 0 为 CHECK_PASS，否则 CHECK_FAIL；
- missing=`max(-delta,0)`，extra=`max(delta,0)`；同一 JOB_ID 只能发布一次最终判定；
- 无新帧、配置不匹配、DMA/模型错误或 timeout 为 ERROR/NO_VIDEO，不生成通过记录。

RISC-V 写 `FW_ACTUAL_COUNTS/FW_DECISION`；PS 生成 v1.2 `decision` 对象并逐字段复算/校验，
规则必须与 `inspection_rules.judge` 的仓库内 Python 参考对拍。RISC-V v0 没有外部中断入口，
因此固件轮询 STATUS；IRQ 只接 PS 的中断控制器。

## 9. 错误、超时、背压和复位

v0 错误码：`BAD_STATE、BAD_ADDR、BAD_ALIGN、BAD_LENGTH、BAD_CONFIG、BAD_MODEL、
DMA_READ、DMA_WRITE、DMA_SHORT、RESULT_MISMATCH、ACC_OVERFLOW_GUARD、ABORTED、WATCHDOG`。
错误码只保留本轮首错，detail 可记录目标/层号；后续错误不得覆盖首因。

- timeout 从 START 接受拍开始，以 cop 计算时钟计数；达到上限即停止发新 DMA、丢弃部分结果、
  BUSY 清零并置 ERROR+TIMEOUT+WATCHDOG；
- DataMover 或结果消费者施加背压时必须保持 `valid/data/last`，不得丢字节或重复计数；
- `rst_n` 硬复位清控制状态、邮箱、结果和 MODEL_VALID；不假定 DDR 被清；
- SOFT_RESET 清运行状态/部分结果并完成 CDC 握手，保留已验证权重和 shadow 配置；
- ABORT 是一次任务错误，SOFT_RESET 是恢复操作；两者不得都伪装成正常 DONE；
- AXI 域复位不得把 cop/core 域半事务误报为成功，恢复后 PS 必须重新握手确认 CFG_APPLIED。

## 10. 配置生效、来源关联与版本

每轮结果必须绑定：`VERSION、MODEL_ID、preprocess_id、CFG_SEQ/CFG_APPLIED、JOB_ID、
CAPTURE_ID、SOURCE_CONFIG_ID、WORK_ORDER_REV、RESULT_SEQ`。session_id 和 trigger_ref 由服务
端维护；硬件不生成 UUID。若任一 ID 与当前 LIVE 会话/配置不符，PS 撤框并要求重检。

`MODEL_ID` 是显式分配的 32 位选择编号，不能替代完整 SHA256。preprocess_id 不占独立 v0
寄存器，由 manifest 与 MODEL_ID/SHA256 绑定并由 PS 服务核验；`SOURCE_CONFIG_ID` 只标识
本轮定位/ROI 配置。改变 preprocess 必须形成新的受版本管理模型包并重新校验配置。

major 变化表示不兼容的寄存器/二进制布局变化；minor 只允许向保留区添加能力，旧软件必须
通过 CAPABILITY 判断。模型包、固件、位流和协议版本均进入 J08 交付清单与 SHA256。

## 11. 实现与验收门禁

### 11.1 算子/寄存器级

- reset 默认值、WSTRB、未对齐/越界、权限和 AXI 背压；
- config 原子提交、busy 时拒绝、START 快照、不重复 start；
- DMA 正常/短包/错误/背压、ROI/权重边界和 target_id 保持；
- done/error/timeout sticky、W1C、abort/soft reset 及 IRQ 电平；
- result 最后提交、RESULT_SEQ 原子快照和索引窗口。

### 11.2 核与应用级

- 新增仓库内 MMIO tb 和固件镜像，单独模式及 `run_iverilog.sh all` 均 PASS；
- 原核四档、arch-test、CoreMark、SoC/视觉回归零退化；
- 正常、缺件、多余、错料、空图、低分、触边、超 10、DMA 错、timeout、复位和重复 JOB_ID；
- RISC-V 判定逐字段对拍 Python 参考，不只比较最终 PASS/FAIL；
- 同一输入的 FP32、J02 INT8 软件、RTL 逐层输出和最终结果可追溯。

所有综合 RTL 使用 Verilog-2001。任何 PASS 必须有仓库内 tb/脚本和原始退出码；板上结果由 NC
执行，JL 提供离板可复现包，不能用 PROGRAM PASSED 或 mock/FILE_REPLAY 替代。

## 12. JL 已冻结的 C03 决策

| ID | 决策项 | 已选 v0 基线 / 未采用备选 | 影响 | 证据 / 风险 |
|:---|:---|:---|:---|:---|
| C03-P1 | 核控制通路 | 推荐 MMIO/AXI4-Lite + DMA；备选自定义指令 | 决定核改动面、驱动和验证范围 | MMIO 不改 decode；自定义指令会扩大 ISA/流水回归，v0 收口风险更高 |
| C03-P2 | 核侧总线适配 | 推荐 `0x8001_0000` 单周期本地 MMIO + CDC 邮箱；备选给核增加可等待总线 | 后者须改 design_v1 访存/停顿契约 | 当前核无 ready/valid，不能直接冒充 AXI master |
| C03-P3 | 控制权 | 推荐 PS 配配置/数据、RISC-V 独占 START 与工单判定；备选双主控仲裁 | 决定冲突、恢复和软件职责 | 单写者最容易复现；PS 与核真实并发尚未验证 |
| C03-P4 | DMA 实现 | 推荐外部 DataMover/AXI DMA，`dma_ctrl` 管描述符/流；备选自研完整 AXI master | 影响 RTL 规模、吞吐和 IP 依赖 | 外部 IP 缩小协议验证；需在目标 Vivado/BD 中验证连接与背压 |
| C03-P5 | 完成通知 | 推荐 RISC-V 轮询、IRQ 只给 PS；备选给核新增中断 | 后者扩大核异常/CSR/固件范围 | 当前 core_top 无 IRQ 口，轮询可复用现有语义但占核周期 |
| C03-P6 | 目标上限 | 推荐硬件/协议能力 16、检查 V0 policy 10，超 10 RECHECK；备选全链硬限 10 | 影响协议兼容与 BRAM/结果表 | v1.2 已是 16；10/16 分层已由 JL 在正文 §1/§8 冻结；C04 的应用层一致性评审仍需完成 |
| C03-P7 | 逐目标结果 | 推荐 16 B，保留 target_id、三 logits、margin、score、错误；备选精简结果 | 影响诊断、带宽与错贴框防护 | 16×16 B 很小；只返 argmax 无法逐层/低置信定位 |
| C03-P8 | 配置/结果原子性 | 推荐 seq 最后提交，busy 时 commit 拒绝不排队；备选单级队列 | 决定跨域一致性和轮次归属 | 无 seq 易读到撕裂数据；队列会增加本轮/下轮歧义 |
| C03-P9 | 状态语义 | 推荐 sticky done/error/timeout + W1C，START 不自动抹旧错 | 影响驱动恢复和错误证据 | 明确首错最利于复现；软件必须多一步清状态 |
| C03-P10 | reset | 推荐 SOFT_RESET 保留已验证权重，硬复位清 MODEL_VALID；备选软复位也重装 | 影响恢复时间和状态可信度 | 保留权重需 CRC/model_id 状态保护；尚无 CDC 复位仿真 |
| C03-P11 | score 衔接 | 推荐采用 C02-P7 的整数 margin/score；备选 PS 概率校准 | 影响寄存器字段与 LIVE 语义 | 协议允许 0–1 score，但不自动定义为概率 |

上表各行的“推荐”项均已成为 v0 实现基线；备选只作取舍记录。不改变既有
decode/ISA 语义，且实现必须验证 busy/done/error/timeout/reset，是不得静默改动的硬边界。
