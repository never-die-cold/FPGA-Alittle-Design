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
| J04b | 🟡 | 40 MHz compute/storage OOC 已过；生产 payload 地址适配、板顶、整机时序与板验未完成 |
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

## J04 收口边界与后续门槛

1. C03 的 `0x8001_0000` 本地 MMIO 窗口和 SoC 行为已回写 `design_v1.md` §17 草案；核数据口无等待语义未改。
2. J04a（JL 侧实现/冒烟）已完成：`cop_top`、MMIO/CDC、AXI4-Lite、流载入、核接入门和工单固件有仓库内 TB；24 个文件 SHA256 与远端一致，交接单见 [runbooks/coprocessor-j04-handoff.md](../../docs/runbooks/coprocessor-j04-handoff.md)。
3. J04b（完整收口）未完成：40 MHz compute/storage OOC 已于 2026-10-22 分别退出 0，WNS
   +7.460/+18.108 ns；storage 使用 28.5 BRAM Tile。该证据不含生产地址适配、PS/AXI 板顶、
   整机布局布线、bitstream/.hwh 或板验，详见本轮[续档](../../report/llm_log/2026-10-22-board-gate-vivado.md)。
4. 后续进入 J07 整机集成前，先按 J05/J06 完成真实数据、正式 INT8 模型/黄金；不得用诊断权重冒充正式模型。

## 下一执行点

P0 两档 OOC 已通过，但 bitstream/.hwh 被生产前置阻塞。下一执行点按依赖而非旧优先级：

1. J05/J06 发布正式模型 payload/manifest（含唯一权威 offset/length/CRC/SHA256）。
2. JL 按 manifest 实现 DataMover→物理 bank 适配及 Zynq PS/AXI 生产板顶，并补整机 TB。
3. Windows Vivado 整机门禁通过后才产 bitstream/.hwh；随后 NC 下载、WC 真接口联调。

未满足第 1 项前无可安全复制执行的 P2 构建命令；不得用 J02 诊断 golden 代替发布模型。

