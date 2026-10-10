# 定位方法原型对比

日期：2026-10-07。此结果用于验证训练与比较流程，不是项目验收结果。

> 后续审计修正：本文仅保存早期定位实验。种子变化不构成独立外部数据集，后续反复查看过的 test 只能视为探索集；类别比较还存在训练预算不一致。最新受控实验、整图指标、背景反例和部署限制见 [探索审计](localization-exploration-audit.md)。本文“测试集只运行一次”只描述当时那一次实验的流程，不代表整个项目至今保有未接触的测试集。

## 实验设置

- 来源：Solidworks Hackathon 紧固件数据集，按原始照片哈希划分 train/val/test；每类每个划分抽取 64 个源裁剪。
- 合成图：每个划分 400 张 1280×720 RGB 图，每图放置 6 个互不重叠物体，共每划分 2,400 个框。不同场景复用同一划分的 64 个裁剪，随机改变缩放、角度、位置和高反差背景。
- OpenCV：Lab 颜色距离阈值 22，形态学开闭运算，连通区域面积过滤；半开区间 XYXY 框。
- CNN：Ultralytics YOLOv8n 预训练权重，4 类，640 输入，batch 8，CPU 训练 10 轮。训练用时约 507.5 秒；最后一轮验证 mAP50=0.913、mAP50-95=0.889。最佳权重位于 `work/datasets/training-runs/seed-42-yolov8n/weights/best.pt`。
- 选择：只在验证集比较 YOLO 置信度，0.55 在试验的 0.25、0.35、0.45、0.55 中 F1 最佳；测试集只运行最终配置一次。
- 评分：忽略类别，仅按 IoU≥0.5 做预测框与真值框的一对一匹配；同一测试集、同一匹配函数。速度是 Windows 桌面 CPU 的单图平均处理时间，不包括相机采集与显示。

## 独立测试集结果

| 方法 | TP | FP | FN | Precision | Recall | F1 | 匹配框平均 IoU | 毫秒/图 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OpenCV | 2,355 | 145 | 45 | 0.9420 | 0.9812 | 0.9612 | 0.9657 | 28.95 |
| YOLOv8n，置信度 0.55 | 2,352 | 74 | 48 | 0.9695 | 0.9800 | 0.9747 | 0.9592 | 30.65 |

这组数据中，YOLOv8n 的 F1 高 1.35 个百分点，误检更少；OpenCV 的平均框重合度略高，桌面 CPU 耗时也略低。两者的速度差约 1.7 ms/图，不能代表 PYNQ-Z2 上的运行速度。

## 复现入口

以下命令从仓库根目录执行，使用仓库外侧 `work` 中的数据与 Python 环境：

```powershell
..\venvs\localization-prototype\Scripts\python.exe sim\vision\generate_localization_dataset.py --dataset-root ..\datasets\solidworks-hackathon --cache-root ..\datasets\solidworks-crop-cache --output-root ..\datasets\synthetic-yolo --seed 42 --per-class-crops 64 --scenes-per-split 400 --objects-per-scene 6 --width 1280 --height 720
..\venvs\localization-prototype\Scripts\python.exe sim\vision\train_localization_cnn.py --data ..\datasets\synthetic-yolo\seed-42\dataset.yaml --model yolov8n.pt --epochs 10 --imgsz 640 --batch 8 --project ..\datasets\training-runs --name seed-42-yolov8n
..\venvs\localization-prototype\Scripts\python.exe sim\vision\compare_localizers.py --dataset ..\datasets\synthetic-yolo\seed-42\test
..\venvs\localization-prototype\Scripts\python.exe sim\vision\compare_localizers.py --dataset ..\datasets\synthetic-yolo\seed-42\test --engine yolo --weights ..\datasets\training-runs\seed-42-yolov8n\weights\best.pt --confidence 0.55
```

## 限制与下一步

测试集是合成场景，不是 400 张真实相机照片；同一划分内部会重复使用 64 个源零件裁剪。标注没有评估漏标、遮挡、接触、反光和真实阴影。此次 YOLO 对比只评定位，不评类别准确率。尚未测试 PYNQ-Z2、720p60 输入下的分析帧率、功耗或 PL/PS 部署。需要用实物和相机采图后重新划分数据、训练和验收。
