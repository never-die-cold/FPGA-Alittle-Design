# CNN 协处理器执行计划

> 状态基线：2026-10-18。契约优先于本计划；计划冲突时先改计划，不静默改契约。

## 权威入口

- C02：[`design_v0.md`](design_v0.md)；整数、形状、排布、payload 与资源边界。
- C03：[`docs/coprocessor-integration-v0.md`](../../docs/coprocessor-integration-v0.md)；MMIO、DMA、状态与分工。
- 总验收：[`plan.md`](../../plan.md) 与[三人收口清单](../../docs/project-closeout-three-person-checklist.md)。
- J03 本轮证据：[`data/logs/2026-10-18-j03-closeout/README.md`](../../data/logs/2026-10-18-j03-closeout/README.md)。

## J01–J10 状态

| 项 | 状态 | 当前边界 / 下一门槛 |
| --- | --- | --- |
| J01 | 🟡 | C02/C03、预算与交接索引已有；不代替 WC/NC 签收 |
| J02 | ✅ | 诊断整数参考、导出/解析、逐层黄金与负例可复现；不是 J06 正式模型 |
| J03 | ✅ | 活跃 Conv→GAP→FC 链逐元素对拍；独立、协处理器 all、全仓 all 退出 0 |
| J04 | ⬜ | `cop_top`、实体存储、MMIO/CDC、DMA、核接入和固件均未实现 |
| J05 | ⬜ | 等真实审计 ROI；训练/PTQ/QAT、混淆矩阵与阈值未完成 |
| J06 | ⬜ | 正式模型、真实参数/黄金、版本/哈希发布未完成 |
| J07 | ⬜ | 视频原帧通路+核+CNN 的综合实现和整机回归未完成 |
| J08 | ⬜ | NC 三批交付包未发布，接收方未验收 |
| J09 | ⬜ | 等 NC 板端反馈后离板复现；不得预先声称完成 |
| J10 | 🟡 | 模块 OOC/周期数据已有；整机性能、既有核待办和答辩材料未收口 |

## J03 收口边界

- 现役计算通路是 `mac_array_pipeline` → `conv_engine` → `cnn_sequencer`。
- `mac_lane` 与 `dot8` 仅用于有符号乘法/加法树诊断，未被现役阵列实例化。
- J03 PASS 证明软件黄金与 RTL 算子/整网离板一致，不证明 J04 接口、完整 SoC 时序或板端输出。
- OOC 报告不含实体 BRAM、DMA、SoC 和视频链，不能外推整机 100 MHz。

## J04 进入门槛

1. 将 C03 的 `0x8001_0000` 本地 MMIO 窗口和 SoC 行为回写核契约草案。
2. 由 JL 确认草案；确认前不写 J04 RTL，不改变核数据口无等待语义。
3. 确认后按“寄存器/CDC → 存储/搬运 → `cop_top` → 固件 → 集成”逐步建 TB 和 runner。

