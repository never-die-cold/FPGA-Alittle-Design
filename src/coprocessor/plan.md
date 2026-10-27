# CNN 协处理器执行计划

> 状态基线：2026-10-22。契约优先于本计划；计划冲突时先改计划，不静默改契约。

## 权威入口

- C02：[`design_v0.md`](design_v0.md)；整数、形状、排布、payload 与资源边界。
- C03：[`docs/contracts/coprocessor-integration-v0.md`](../../docs/contracts/coprocessor-integration-v0.md)；MMIO、DMA、状态与分工。
- 交接索引：[`docs/contracts/coprocessor-handoff-v0.md`](../../docs/contracts/coprocessor-handoff-v0.md)。
- 总验收：[`plan.md`](../../plan.md) 与[三人收口清单](../../docs/project-closeout-three-person-checklist.md)。
- J03 本轮证据：[`data/logs/2026-10-18-j03-closeout/README.md`](../../data/logs/2026-10-18-j03-closeout/README.md)。

## J01–J10 状态

| 项 | 状态 | 当前边界 / 下一门槛 |
| --- | --- | --- |
| J01 | 🟡 | C02/C03、预算与交接索引已有；不代替 WC/NC 签收 |
| J02 | ✅ | 诊断整数参考、逐层黄金、文件/来源 SHA256 与篡改负例可复现；不是 J06 正式模型 |
| J03 | ✅ | 活跃 Conv→GAP→FC 链逐元素对拍；显式使用仓库 venv 时，独立、协处理器 all、全仓 all 退出 0；裸系统 Python 缺 NumPy 时不成立 |
| J04a | ✅ | JL 侧实现、模块/顶层冒烟、J02 zero、工单固件与交接单已落库；24 个文件 SHA256 与远端一致 |
| J04b | 🟡 | manifest/16 ROI 板顶已离板验证；CDC/结果提交 RTL 合并后，A 变体须重跑整机门禁；仍缺描述表与 NC 固件/payload/结果验收 |
| J05 | ⬜ | 等真实审计 ROI；训练/PTQ/QAT、混淆矩阵与阈值未完成 |
| J06 | ⬜ | 正式模型、真实参数/黄金、版本/哈希发布未完成 |
| J07 | 🟡 | 视频取帧/VDMA/HP1 离板集成已进入 B 变体；综合、实现与板上均 UNVERIFIED |
| J08 | 🟡 | 首包待验收；`f856d5861db0`/`759744b99891`/`5653d5911b76` 已作废，等待 A 新构建 |
| J09 | ⬜ | 等 NC 板端反馈后离板复现；不得预先声称完成 |
| J10 | 🟡 | 模块 OOC/周期数据已有；整机性能、既有核待办和答辩材料未收口 |

## J03 收口边界

- 现役计算通路是 `mac_array_pipeline` → `conv_engine` → `cnn_sequencer`。
- `mac_lane` 与 `dot8` 仅用于有符号乘法/加法树诊断，未被现役阵列实例化。
- J03 PASS 证明软件黄金与 RTL 算子/整网离板一致，不证明 J04 接口、完整 SoC 时序或板端输出。
- OOC 报告不含实体 BRAM、DMA、SoC 和视频链，不能外推整机 100 MHz。

## J04 收口边界与后续门槛

1. C03 的 `0x8001_0000` 本地 MMIO 窗口和 SoC 行为已回写 `design_v1.md` §17 草案；核数据口无等待语义未改。
2. J04a（JL 侧实现/冒烟）已完成：`cop_top`、MMIO/CDC、AXI4-Lite、流载入、核接入门和工单固件有仓库内 TB；24 个文件 SHA256 与远端一致，交接单见 [runbooks/coprocessor-j04-handoff.md](../../docs/runbooks/coprocessor-j04-handoff.md)。
3. J04b 的 2026-10-26 整机门禁是合并前历史证据；新 CDC 三级控制同步与结果提交状态进入后，
   A 变体综合/实现重新变为 UNVERIFIED。仍缺任意 `TARGET_DESC_ADDR` 描述表、NC 板上
   固件活性/payload/结果验收，且正式模型未到；不得沿用旧数字或用 Vivado PASS 代替板验。
4. manifest v1 固定 offset/length/bank schema；当前 payload 明示 `kind=PROVISIONAL`，只用于结构验证。
   正式权重到位后只替换 payload 与 manifest，不改 RTL/软件协议；不得把诊断权重称为发布模型。
5. 生产板顶候选已接入 16×4096 B ROI 槽、权重影子 bank 和 100→40 MHz CDC；当前
   `target_id == roi_index` 仅支持恒等映射，任意 `TARGET_DESC_ADDR` 描述表尚未接入，不得作为完整契约验收。

## 下一执行点

P0 两档 OOC 已通过，manifest schema 已定且内容仍为 PROVISIONAL。下一执行点：

1. JL 用全新 `COP_BUILD_NAME`、不设置 `COP_WITH_VIDEO` 重跑 A 变体整机门禁；门禁前不打新包。
2. A 通过后再打 PROVISIONAL 首包给 NC；loader 按 HWH 区分 direct 40 MHz 与
   MMCM 输入→40 MHz cop 输出，STATUS 首读仍须为 `0x1`，BOARD 保持 UNVERIFIED。
3. IMEM 历史门禁已验证首字/非零/零 warning；新 A 构建必须重新给出同三项，随后再由 NC
   验证 FW_DECISION/ACCEPTED 活性。B 变体不得混入 A 包或借用 A 报告。
4. J05/J06 正式权重到位后，用同一 schema 换 payload+manifest，重新记录 CRC/SHA256 与黄金证据。

当前 J02 payload 只解锁板级结构与地址通路，不构成 RELEASE、精度或板上验收证据。

