# FP32 原型模型

- `cnn-bn64-baseline.pt`、`cnn-border-fill-best.pt`：历史接收的 FP32 CNN 原型，用于软件参考与开发对照。
- 当前 r6 检查点、训练输入与 INT8 payload 见 [CNN r6 包](../data/evidence/2026-10-28-cnn-r6/README.md)。发布与验收状态见[主计划](../plan.md#31-当前状态)。
- HOG/SVM 模型及专用训练入口已退役；原件在 `a631fd2`，接收收据见[历史清单](../data/evidence/2026-10-10-fastener-handoff/README.md)。
