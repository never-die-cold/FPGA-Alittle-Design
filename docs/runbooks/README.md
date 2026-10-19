# runbooks —— 执行单与操作手册

> 这里放“照着做就能完成一次操作”的文档：上板、采集、NC 返板、训练、复现、检查。
> 与 `docs/contracts` 的区别：契约回答“接口是什么”，runbook 回答“这一步怎么做”。
> 过期执行单应移到 `docs/archive/`，不要篡改原文。

| 文档 | 说明 |
|:---|:---|
| [`arm-localize-baseline-plan.md`](arm-localize-baseline-plan.md) | PYNQ ARM 定位与逐目标裁剪基线：实施清单 |
| [`arm-localize-results.md`](arm-localize-results.md) | ARM 文件定位/裁剪：最终交付与实测 |
| [`arm-localize-runbook.md`](arm-localize-runbook.md) | ARM 文件定位/裁剪便携包 |
| [`fastener-collection-handoff.md`](fastener-collection-handoff.md) | 紧固件采集交接包：编号规则、采集表与验收矩阵（W01） |
| [`fastener-data-collection-protocol.md`](fastener-data-collection-protocol.md) | fastener-data-collection —— 紧固件数据采集规程（草案） |
| [`coprocessor-j04-handoff.md`](coprocessor-j04-handoff.md) | J04 协处理器实现交接：冒烟入口、指纹、OPEN-1..8 与接手步骤 |
| [`module1-reproduction.md`](module1-reproduction.md) | 模块一复现清单（#skill候选） |
| [`module3-model-training.md`](module3-model-training.md) | 模块三模型训练前期准备（INT8 CNN 训练与量化路线） |
| [`module3-prototype-reference.md`](module3-prototype-reference.md) | 模块三：交付原型的 FP32 逐层软件参考 |
| [`n03-custom-return-runbook-2026-10-14.md`](n03-custom-return-runbook-2026-10-14.md) | N03 custom DDR返板执行单（2026-10-14） |
| [`nc-collection-preflight.md`](nc-collection-preflight.md) | NC采集前准备：无需板卡的部分 |
| [`nc-industrial-acceptance-v0.md`](nc-industrial-acceptance-v0.md) | NC工业与故障验收执行矩阵 |
| [`nc-offboard-workboard-2026-10-14.md`](nc-offboard-workboard-2026-10-14.md) | NC离板工作板：从当前到提交 |
| [`nc-offline-readiness-2026-10-12.md`](nc-offline-readiness-2026-10-12.md) | NC 离板准备与返板顺序（2026-10-12） |
| [`nc-release-demo-preflight.md`](nc-release-demo-preflight.md) | NC发布、演示与提交前检查 |
| [`nc-return-checklist-2026-10-12.md`](nc-return-checklist-2026-10-12.md) | NC 返场执行单与待确认项（2026-10-12） |
| [`offline-inspection.md`](offline-inspection.md) | 离板检查：共享 ROI、FP32 原型与 FILE_REPLAY |
| [`pi-camera-preview-runbook.md`](pi-camera-preview-runbook.md) | Pi 相机预览服务：手动与开机复验 |
| [`pi-dev-roles.md`](pi-dev-roles.md) | 树莓派 4B：开发期角色与红线（pi-dev-roles） |

## 相关入口

- [项目地图](../project-map.md)
- [上板指南](../../board/README.md)
- [复现与仿真](../../sim/README.md)
