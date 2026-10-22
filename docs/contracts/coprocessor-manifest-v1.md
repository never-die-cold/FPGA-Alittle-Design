# Coprocessor payload manifest v1

> 状态：v1 布局契约。当前实例必须标为 `kind=PROVISIONAL`，只承载 J02 诊断网络，
> 不是发布模型。正式权重到位后只替换 payload 与 manifest，不改变 RTL 或软件协议。

## 1. 权威边界

- manifest 是 payload 的 offset、length、alignment 与物理 bank 映射的唯一权威。
- RTL 只依赖 offset/length/bank，不解析层名、类别、精度或其他模型语义。
- `score_q15` 是有符号整数分数，不是概率。
- 所有 offset、length、alignment、total_bytes 均以字节计；payload 内多字节整数为小端序。
- payload 空洞及张量尾部对齐填充必须为零；张量区间不得重叠或越过 `total_bytes`。

## 2. JSON schema

顶层必须包含：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `version` | string | 固定 `coprocessor-manifest-v1` |
| `model_id` | uint32 | 快速选择编号；完整身份仍由 SHA256 给出 |
| `kind` | enum | 仅 `PROVISIONAL` 或 `RELEASE`；当前诊断包只能是 `PROVISIONAL` |
| `payload_file` | string | 相对 manifest 的 payload 文件名 |
| `payload_sha256` | string | payload 原始 36,032 B 的 64 位小写十六进制 SHA256 |
| `crc32` | string | `0x` 加 8 位小写十六进制；CRC-32/ISO-HDLC，与 `zlib.crc32` 一致 |
| `total_bytes` | uint32 | 完整 payload 长度，含全部零填充 |
| `tensors` | array | 下述张量项；按 offset 严格递增 |
| `generation_command` | string | 从仓库根目录可复制执行的生成命令 |

每个 `tensors[]` 项必须包含：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `name` | string | 唯一诊断名；RTL 不解析 |
| `offset` | uint32 | 64 B 对齐且 `offset + length <= total_bytes` |
| `length` | uint32 | 仅有效张量字节，不含到下一张量的填充 |
| `alignment` | uint32 | v1 固定 64 |
| `bank` | object | `kind` 与 `base`；定义首元素的物理位置 |

`bank.kind` 只允许 `WEIGHT16`、`BIAS32`、`MULTIPLIER32`、`SHIFT6`。
`bank.base` 对 `WEIGHT16` 是 128 B 权重组号，对其余三类是首输出通道索引。

## 3. 固定物理映射

| bank.kind | payload 单元 | 物理写入 |
| --- | --- | --- |
| `WEIGHT16` | 连续 8 B | `bank=(relative_byte/8)%16`；`group=base+relative_byte/128` |
| `BIAS32` | 小端 4 B | `init_kind=2, init_address=base+relative_byte/4` |
| `MULTIPLIER32` | 小端 4 B | `init_kind=3, init_address=base+relative_byte/4` |
| `SHIFT6` | 1 B，值须 `<=62` | `init_kind=4, init_address=base+relative_byte` |

权重 8 B 单元映射为 `init_kind=1, init_address={group,bank}`。DataMover 的每拍
`store_strb` 必须是从 bit 0 起连续的有效字节；跨张量、越界、未对齐或长度不符的请求必须
整笔零副作用拒绝，并产生可见单拍错误事件。

## 4. v1 固定张量集合

五层依次为 `conv1`、`conv2`、`conv3`、`conv4`、`fc`，每层各有
`weight`、`bias`、`multiplier`、`shift`，共 20 项。有效长度由 C02 固定 shape 导出；
每项从 64 B 边界开始。J02 参数值保持原样，只增加零填充形成单一 payload。

当前固定布局总长为 **36,032 B**：权重区 34,432 B，bias 区 640 B，
multiplier 区 640 B，shift 区含逐层对齐共 320 B。逐项 offset/length/base 必须由生成器
写入实例 manifest，不得从本段摘要反推或手工维护第二份表。

## 5. 生成与升级

仓库入口由 manifest 的 `generation_command` 给出；生成器必须同时写 payload、manifest、
manifest 的 `.sha256` 侧车文件及可复现负例。负例至少覆盖 offset 篡改和 length 越界。
生成器先校验全部区间、对齐、总长、bank 容量，再写最终 manifest。

`PROVISIONAL` 升级为 `RELEASE` 必须由正式模型流程重新生成 payload/manifest 并分配相应
`model_id`、CRC32 与 SHA256；不得只改 `kind` 字段，也不得把当前诊断包改称发布模型。
