# [2026-10-22] 协作记录：manifest v1、PROVISIONAL payload 与影子 bank 地址适配

> 标签：#coprocessor #manifest #payload #BRAM #数据通路
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`6ef7df1` `1d2a133` `7c5ba07` `f3baea9` `c8d0640` `7a33998`

## 1. 任务与初始提示词

Phase 1：定义 `docs/contracts/coprocessor-manifest-v1.md`，字段含 version、model_id、
kind(PROVISIONAL|RELEASE)、payload_sha256、crc32、total_bytes、逐张量 offset/length/alignment、
bank 映射与生成命令；RTL 只依赖 offset/bank，不解析模型语义。把现有 J02 诊断 payload 原样包成
`kind=PROVISIONAL`（禁止称发布模型），产出负例；实现 DataMover→物理 bank 适配，
越界/未对齐/长度不符零副作用拒绝；补无 PS 的整机数据通路 TB。

## 2. 模型第一版方案

生成 36,032 B 单一 payload（20 个张量，权重区 34,432 B、bias/multiplier 各 640 B、
shift 含对齐 320 B），每项 64 B 对齐；manifest 记录 offset/length/base/bank。
RTL 采用“整包预检 + 影子 bank 写入 + 成功后原子切换”：失败时不写 BRAM、不改寄存器、
只发一拍可见 error 脉冲，保证不存在“半张权重”被计算使用。

## 3. 失败现象

1. 若字节序按高字节优先写入，INT8 分段会错位，结果错但“看起来正常”，CRC 也可能掩盖。
2. 若边收边写目标 bank，失败时会留下“半张权重”，下一轮任务可能使用混合参数。
3. `kind` 只是证据声明：把 PROVISIONAL 改成 RELEASE 不会改变 payload/SHA256/生成链路，
   属于标签伪装，必须禁止。
4. 旧单 ROI 存储在 `ROI_COUNT>1` 时会重复/覆盖同一 ROI（Phase 2 审计发现）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 字序风险 | 按数值低字节优先写入 | 与 C8HW8/O16I8、小端字序一致 | payload_adapter PASS |
| 2 | 半张权重风险 | 不能在目标 bank 原地写 | 整包预检 + 影子 bank + 原子切换 | 三类拒绝状态 diff 为空 |
| 3 | kind 不能当开关 | 证据声明不可伪装 | 固定 PROVISIONAL，升级需重生成 | 文档与 TB 负例 |
| 4 | 旧单 ROI 容量 | 与最大 16 ROI 不一致 | 板顶改用 16 槽激活存储 | `activation_storage` PASS |

## 5. 最终结论

- `manifest_v1`：`PASS: manifest_v1 20 tensors preserve J02 bytes; SHA256/CRC/padding valid; offset and OOB negatives rejected`。
- `payload_adapter`：正常路径 `4304/147/147/147`，未对齐、长度错、越界均 `active-state diff empty`。
- `payload_network`：`PASS: payload_network manifest payload -> DMA -> shadow BRAM -> atomic activate; bytes=36032 crc32=2f760211`，
  随后 zero 73,795 元素逐项一致。
- 当前仍是 `kind=PROVISIONAL` 诊断参数（OPEN-BT-1）；正式 RELEASE 只换 payload+manifest，不改 RTL/软件。

## 6. 经验沉淀

- 触发条件：运行时可装载权重，但地址映射没有唯一权威。
- 排查步骤：先定 manifest 为唯一权威；RTL 只认 offset/length/bank；用影子 bank + 原子切换；
  对越界/未对齐/长度不符做“状态 diff 为空”的负例。
- 适用范围：任何“位流不绑定模型”的加速器；换模型只换 payload/manifest。
#skill候选
