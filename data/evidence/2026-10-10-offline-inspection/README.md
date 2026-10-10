# FILE_REPLAY 示例证据

2026-10-10；工作区候选实现，待理解/提交。没有连接板卡。

- `fixtures/`：仓库 `sim/vision/generate_inspection_fixture.py` 生成的几何合成图与空背景；无类别真值。
- `runs/synthetic-001/`：真实交付 FP32 权重执行的完整文件回放快照。
- `viewer-exe.png`：打包 EXE 读取该快照的离线 HUD；`viewer.png` 为 Python 展示记录。

合成图检测到 3 个目标，原型预测 bolt=2、nut=0、washer=1；工单要求 1/1/1，
候选阈值 0.8、目标上限 10，判定 CHECK_FAIL。没有真实标签，不计算准确率。
源图/ROI/模型/代码 SHA256 和运行环境以 `runs/synthetic-001/result.json` 为准。
ROI hex 是逐行 uint8 像素，非 INT8 模型权重。

复现、重复请求和改用新请求号的规则见[离板检查说明](../../../docs/offline-inspection.md)。
原始验证日志见[验证记录](../../logs/2026-10-10-offline-inspection/README.md)。
代码或环境变化时请使用新请求号；旧证据不会被自动覆盖。
