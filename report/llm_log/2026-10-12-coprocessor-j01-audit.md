# 2026-10-12 J01-1：C02/C03 交叉审计

> 状态：只读审计完成；未修改冻结契约，未写算法、RTL 或固件。

## 1. 审计范围与权威顺序

- 整数、网络、排布与预算：[C02](../../src/coprocessor/design_v0.md)。
- 核/PS、MMIO、DMA 与结果：[C03](../../docs/coprocessor-integration-v0.md)。
- 训练交付说明：[module3-model-training](../../docs/module3-model-training.md)。
- 模块入口：[coprocessor README](../../src/coprocessor/README.md)。
- C02/C03 是规范权威；训练文档中的冻结前估算不得覆盖它们。

## 2. 已一致项目

| 项目 | 交叉审计结论 |
|:---|:---|
| 首网/类别 | FastenerCNN；`0=bolt,1=nut,2=washer`，4 Conv+GAP+FC，形状一致 |
| ROI | `scene-gray-border-padding-v1`；DMA 输入为 HW INT8 64×64，共 4,096 B |
| 整数语义 | 激活/权重对称 INT8、zero-point=0、INT32 累加、INT64 requant 乘积 |
| score | 三个 INT8 logits、margin、score_q15、low_conf 与 `MIN_MARGIN_Q` 一致 |
| 排布 | 黄金 CHW/OIHW；片上 C8HW8；权重 O16×I8；多字节 little-endian |
| 结果 | 每目标 16 B，保留 target_id、class、logits、margin、score、错误和拍数 |
| 数量边界 | 硬件/协议最多 16，检查 V0 最多 10；11–16 直接 RECHECK，不截断 |
| 核接口 | 本地单周期 MMIO+CDC；PS 为真实 AXI4-Lite；不改 ISA/decode 或加核等待 |
| 状态 | sticky done/error/timeout、W1C、busy 时拒绝 commit/start、结果最后提交 |
| 性能口径 | 128 MAC/100 MHz 是目标；1.014 ms 仅为计算调度估算，端到端待测 |

## 3. 实现前必须补清的交接项

| ID | 缺口 | 风险/门禁 |
|:---|:---|:---|
| J01-G1 | C02 定义权重、bias、multiplier、shift 均 64 B 对齐；C03 的 `WEIGHT_BYTES/WEIGHT_CRC32` 未明确覆盖仅权重还是完整参数 payload | J02-13 前必须冻结 CRC 覆盖范围和精确 payload 边界，否则 PS、DMA、BRAM 会计算不同长度 |
| J01-G2 | C03 要求 manifest 中有 32 位 `MODEL_ID` 和 payload CRC32；C02 包最低清单只明确模型 ID、SHA256，未写 ID 生成/分配规则和 CRC32 字段 | J02-14 前必须定义 32 位 ID 来源并同时保留 SHA256；不得截断哈希后不说明碰撞策略 |
| J01-G3 | C03 要求每轮绑定 `preprocess_id`，但寄存器表没有独立字段 | J01-2 必须明确它由 MODEL_ID/manifest 与 PS 服务绑定，还是新增寄存器；若新增字段须先改 C03 |

上述三项不是授权实现者自行选择的空白；拍板或澄清前不得开始对应 payload/manifest/MMIO 实现。

## 4. 已发现的旧文案

1. 训练文档 §1 仍写“每层前 64 个输出”，C02 §6.1 已冻结为完整张量；前 64 个只能人工抽查。
2. 训练文档 §3.5 把约 0.95 ms 写成“单目标延迟”；C02 已冻结为 0.933 ms 理想下界、
   1.014 ms 阵列调度估算，二者均非端到端实测。
3. C03 决策表 C03-P6 的风险栏仍写 policy 10“须 JL 统一”，但正文 §1/§8 已明确冻结 10/16 分层。

这些文案不改变 C02/C03 正文的当前权威语义，但必须在 J01-2 同步后再交 WC/NC。

## 5. 结论

- 网络、整数计算、ROI、结果、状态和核接口没有发现互相冲突的冻结语义。
- J01-G1～G3 是导出器和驱动实现前的硬门槛；本审计不替 JL 拍板。
- J01-2 应先形成候选与影响清单，经 JL 确认后再同步契约和训练文档。

## 6. JL 拍板与 J01-2 同步（2026-10-13）

JL 确认：CRC32 覆盖完整对齐参数 payload；bias、multiplier、shift 损坏会改变结果，
对齐填充虽不参与计算也是规范传输字节。32 位 MODEL_ID 只作快速标签，不能替代完整 SHA256。同步采用三项方案：
完整 payload 的 WEIGHT_BYTES/CRC32；显式分配 uint32 MODEL_ID、SHA256 作为交付身份；
preprocess_id 绑定 manifest/MODEL_ID/SHA256 并由 PS 核验，不新增 v0 寄存器。
