# contracts —— 跨模块接口契约

> 这里放“接口/语义已经或准备冻结”的文档；RTL 的核接口权威仍在 `src/riscv/design_v0.md`/`design_v1.md`，视觉在 `src/vision/design_v0.md`。
> 规则：改接口先改契约，再改 RTL/软件；建议稿要标明“建议/草案”，不能当冻结契约引用。

| 文档 | 说明 |
|:---|:---|
| [`c01-capture-implementation-baseline.md`](c01-capture-implementation-baseline.md) | C01 原彩色捕获实现基线 |
| [`c01-capture-status-contract.md`](c01-capture-status-contract.md) | C01 捕获状态接口：实现候选 v0.1 |
| [`c01-ddr-frame-ownership-v0.md`](c01-ddr-frame-ownership-v0.md) | C01 custom DDR帧槽所有权：NC交接候选 |
| [`coprocessor-integration-v0.md`](coprocessor-integration-v0.md) | C03：CNN 协处理器、RISC-V 与 PS 的 v0 接口契约 |
| [`coprocessor-manifest-v1.md`](coprocessor-manifest-v1.md) | payload offset/length 与物理 bank 映射唯一权威；当前仅 PROVISIONAL |
| [`coremark.md`](coremark.md) | CoreMark 基准契约与工作包计划 |
| [`inspection-v0-contract.md`](inspection-v0-contract.md) | 检查 V0：取图、ROI 预处理与首次成功检查契约（建议稿） |
| [`vision-live-semantics.md`](vision-live-semantics.md) | LIVE 检查、显示与来源语义（C04 设计稿） |
| [`vision-sync-protocol-decisions.md`](vision-sync-protocol-decisions.md) | 视频/结果同步协议决策单（EXE 前端 × 板端服务） |

## 相关入口

- [项目地图](../project-map.md)
- [docs 导航](../README.md)
- [WC 协处理器软件接口](../coprocessor-wc-interface.md)
- [协处理器存储规划](../coprocessor-storage-plan.md)
- [JL Vivado 检查清单](../coprocessor-vivado-checklist.md)
- [NC 协处理器交接](../coprocessor-nc-handoff.md)
- 核契约：[`src/riscv/design_v0.md`](../../src/riscv/design_v0.md)、[`src/riscv/design_v1.md`](../../src/riscv/design_v1.md)
- 视觉契约：[`src/vision/design_v0.md`](../../src/vision/design_v0.md)
