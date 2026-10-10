# 紧固件视觉方案交接包

生成日期：2026-10-07。适用条件：工业流水线背景稳定、简单可控，照明理想。当前建议原型为 OpenCV 定位 + 逐目标小 CNN 分类。

## 先看这些

1. `docs/工作进展汇报.md`：可转发的简要进度。
2. `docs/修订方案-受控流水线.md`：按流水线工况调整后的技术方案。
3. `docs/方案探索报告.md`：实验设置、数据和限制的详细说明。

## 包含内容

- `sim/vision/`：数据准备、定位、HOG/SVM 与小 CNN 训练、评估和探测脚本，以及轻量回归用例。
- `results/`：逐图评估 JSON、各轮训练记录及背景反例图。
- `models/`：一个 train-only HOG/SVM 模型和两个 FP32 小 CNN 原型权重。它们用于复现实验，不是已验收的产品模型或 INT8 部署文件。
- `docs/`：进展、受控流水线修订方案、详细实验审计和数据集审计。

## 未包含内容及复现前提

为控制包体并避免重复分发公开数据，未包含原始 Solidworks 图片/标注、生成的场景图片、裁剪缓存、YOLOv8n 权重、训练日志图表。完整实验需准备这些文件，并保持目录约定：

- `../datasets/solidworks-hackathon/`
- `../datasets/solidworks-crop-cache/`
- `../datasets/synthetic-yolo/seed-52/` 和 `seed-62/`
- `../datasets/training-runs/seed-42-yolov8n/weights/best.pt`

脚本以原 Git 仓库根目录为当前目录编写；解压后把 `sim/vision/` 放回同名路径，并按上面约定放置数据后运行。数据缺失时，不能直接重现表中的完整评估数字。

原实验环境：Python 3.12、PyTorch 2.5.1 CPU、OpenCV 4.10.0、NumPy 1.26.4、Pillow 12.3.0、Ultralytics 8.3.17。CPU 耗时不代表 PYNQ-Z2 性能。受控数据上的分数不代表真实产线验收；本包不含真实相机采集数据、INT8 导出物或板端 RTL/测试证据。

## 接收方建议先确认

1. 产线检查时工件是否停稳；若连续运动，需要线速、目标最小间距、触发方式和跨帧去重设计。
2. 相机实际输出、工件在画面中的像素大小，以及 PYNQ-Z2 如何取得足够清晰的 ROI。
3. 用目标背景和实际零件采样验证 OpenCV 定位后，再冻结模型输入与验收门槛。
