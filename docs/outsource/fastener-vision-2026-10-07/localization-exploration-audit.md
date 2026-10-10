# 方案探索与反思：定位、分类和芯片实现

日期：2026-10-07。当前分支 codex/localization-prototype，基线 0669960。本轮没有提交 Git、没有改 RTL，没有打开 test 划分训练或选模型。应用补充条件：面向工业流水线，背景可控、稳定、简单，光照理想；渐变照明试验作为压力测试看待。

## 结论

结合受控背景和理想光照的工况，当前最适合项目推进的结构是：**OpenCV 传统视觉定位 → 逐目标 64×64 小 CNN 分类 → 类别/数量核对 → 异常时复检**。该结构轻量且能体现自研 CNN 加速器用途。渐变照明压力测试暴露的是超出常规设定的边界风险，不应据此否定受控工位下的 OpenCV 主线。方案仍需真实工位采图验证，尚不能宣称已达工业验收。

保留 OpenCV+HOG/SVM 作为传统方法基准，YOLOv8n 作为软件识别基准。当前模拟场景上 YOLO 指标最好，但训练资料、预训练及计算成本不同，不能据此直接换成 YOLO 硬件主线。小 CNN 尚未在准确率上取胜，保留它的理由是硬件算子与任务分工适配。

工位既然能控制背景和光照，先按可重复的工位条件调通传统定位最合理。预先保留照明偏移、背景污染、反光、物体接触等异常用例；若真实运行边界超出可控条件，再根据采集到的失败案例评估局部分割或检测器。

继续在同一种渲染数据上反复调参，无法解决真实金属反光、相机成像、未知件和板端缓存问题。下一个最有价值的里程碑是补齐这些证据，再冻结方案。

## 本轮纠正了什么

1. 原 SVM 在训练集+验证集重训，CNN 仅使用训练集，比较不公平。新增 train-only SVM，保留相同的 9 组超参数搜索，验证集只用于选择。
2. seed-52、seed-62 是场景随机种子，不是独立真实数据来源。同一划分的源素材可能重复；此前反复查看过的 test 只作为探索资料，最终需另采按实物、拍摄批次隔离的真实测试集。
3. 原评分先按框匹配再看类别，错误类别的框可能抢占正确类别预测。现改为同类、IoU≥0.5 的贪心一对一匹配；混淆矩阵仍按几何匹配单独诊断。这是固定阈值 F1，不是 COCO mAP。
4. 低分拒识原来只显示 F1 下降，无法说明人工复检价值。新增已接纳预测精度、候选框接纳比例和整图复检比例。漏定位不会自动触发这个置信度复检，因此复检比例不是完整安全指标。
5. 新增整图类别数量完全正确率、全部目标检测正确率和逐图 JSON。数量正确可能由误分类互相抵消，不能代替逐物体正确率；两项均不等于有好/坏工单时的误放行率。
6. 训练和推理共用裁剪预处理；新实验保存预处理模式、模型版本、训练配置、每轮验证指标和数据文件哈希。
7. 原有历史非 BN 权重仍需对应历史网络定义，不能直接用当前 BN 类加载。新实验权重已有架构标记，旧权重兼容未在本轮补齐。

## 相同训练资料下的分类实验

使用 seed-52 train 与 val，各 250 张合成图，每图含 5 个三类目标和 1 个定位销。分类实验忽略定位销，因此训练与验证各 1,250 个目标裁剪。64×64 灰度输入，随机种子 2026。CNN 为四卷积+BN+ReLU+GAP+FC；本轮 40 轮、AdamW、初始学习率 0.001、余弦下降到 0.00001。最佳轮由验证集选择。

| 方法 | 最佳验证裁剪准确率 | 实测训练与验证耗时 | 解释 |
|---|---:|---:|---|
| HOG+RBF SVM，仅训练集 | 93.84% | 14.50 秒 | 9 组搜索，C=100，gamma=0.0006；不重训到验证集 |
| CNN，无额外增强，原填充 | 89.60% | 28.92 秒 | 当前合成图已经包含旋转和尺度变化 |
| CNN，额外翻转/旋转/亮度增强 | 87.68% | 30.56 秒 | 本次预算下未获益；不代表所有增强都无效 |
| CNN，无额外增强，边缘中位色填充 | 90.72% | 29.54 秒 | 较同轮数原填充高 1.12 个百分点，尚无多随机种子复验 |
| 先前 CNN，100 轮，原增强 | 91.52% | 本轮未重训计时 | 不与 40 轮实验作等预算因果比较 |

时间为当前 Windows 桌面 CPU、4 个 Torch 线程下实测，包含数据加载和验证，不含数据生成及文件哈希；不能代表从零构建全项目所需时间。不同算法的增强与超参数搜索量仍有区别，不能称为完全相等算力预算。

BN 重校准试验：只用 seed-52 train 的无额外增强裁剪重新估计 BN 统计量，先前 100 轮模型的验证准确率从 91.52% 降到 90.96%，因此未采纳。

BN 折叠：把原模型的 BN 合入卷积参数，1,250 个验证裁剪上分类结果无差异，最大 logit 绝对差 5.60e-6。已保存 folded-fp32.pt。此为浮点等价检查，INT8、整数逐层语义和板上运行仍未验证。

## 端到端比较：新增整图指标

统一使用 seed-62 **val**：250 张、每张恰好螺栓/螺母/垫圈各 2 个，共 1,500 个目标。全部在 CPU 串行评估，Torch 4 线程、OpenCV 1 线程。合成场景仍过于规则，无空图、未知件和数量变化；这些结果仅用于探索。

| 路线 | 目标级 F1 | 整图三类数量完全正确 | 全部目标检测正确 |
|---|---:|---:|---:|
| OpenCV+SVM，仅训练集 | 88.63% | 50.4% | 48.8% |
| OpenCV+CNN，40轮原填充 | 84.60% | 40.4% | 39.2% |
| OpenCV+CNN，40轮额外增强 | 81.50% | 34.4% | 32.4% |
| OpenCV+CNN，40轮边缘填充 | 85.39% | 44.8% | 41.2% |
| OpenCV+先前100轮CNN | 85.72% | 44.8% | 42.8% |
| YOLOv8n，置信度0.65 | 92.17% | 52.8% | 52.8% |

YOLO 曾用 COCO 预训练及另一批四类合成图训练，不是与前三类分类器相同的数据预算。其定位销输出在这批三类验证图上计误检；整图通过率要求无额外类别预测。以上排序不能当成公平架构竞赛结论。

当前桌面平均耗时约 34–38ms/图，包含首次调用开销；没有单独预热，不据此排列速度，也不能推断 PYNQ-Z2 帧率。720p60 显示输入与分析检查频率是两个指标。

拒识试验：先前 CNN 阈值从 0 提高到 0.65，保留预测精度由 84.80% 上升至 87.82%，保留 90.54% 的候选框，但 47.6% 的图片至少有一个候选框被拒识。F1 从 85.72% 降至 80.38%。说明拒识存在精度/覆盖率代价，当前阈值不能直接作为合格工作站默认值；也未验证未知零件拒识能力。

## 找到了能推翻简化假设的背景反例

新增六个确定性场景：均匀暗背景、左右亮度渐变、中央照明亮斑，每种分别为空图和一个高亮矩形目标。目标灰度230，背景最高约120，仍然高反差。

| 背景 | 空图 | 放一个目标 |
|---|---|---|
| 均匀 | 无误检 | 1个正确框 |
| 左右渐变 | 2个误检 | 1个正确框+2个误检 |
| 中央亮斑 | 1个误检 | 背景与目标合成大框，误检1、漏检1 |

这不是对真实零件的准确率评估，是对“高反差足够保证四角背景分割有效”的反例。现有四角中位颜色假设需要近似均匀背景。增加分类模型容量无法恢复漏掉或合并的目标框。

压力场景下的备选改进方向：

- 若实际工位背景或照明无法持续维持设定：可评估空背景参考和光照补偿，放料后冻结背景更新；相机移动或照明改变后重建参考。需要真机图片验证。
- 若失效来自阴影、渐变照明或角落背景变化：比较局部背景估计、边缘/区域联合分割与轻量检测器，用对应故障场景筛选；不要只增加全局阈值。
- 对面积异常、框触边、疑似粘连/过曝和未知件加入复检逻辑。这些检查未实现，不能声称当前系统已有此防护。

## 追加开发探测：空图和随机数量

使用 val/seed-53 的已有裁剪，生成60张新场景：10张均匀空图、10张渐变空图、40张随机1–8件的分散场景，类别随机，总目标199个。复用已有验证来源，明确不是独立测试集。阈值沿用前文，不按这批图重新调参，源裁剪路径记录在 manifest.json。

| 方法 | 均匀空图正确 | 渐变空图正确 | 随机数量整图正确 | 全组F1 |
|---|---:|---:|---:|---:|
| OpenCV+train-only SVM | 10/10 | 0/10 | 26/40 | 86.46% |
| OpenCV+先前100轮CNN | 10/10 | 0/10 | 21/40 | 79.33% |
| YOLOv8n，0.65 | 10/10 | 10/10 | 29/40 | 95.45% |

两种传统定位路线在渐变空图各产生20个误检。YOLO在这10张图上没有误检，但样本小且背景简化，不能宣称全面鲁棒。不要用不同场景组成下的总F1涨跌说明训练进步。

新增生成入口 `generate_variable_count_probe.py --cache ../datasets/solidworks-crop-cache/val/seed-53 --output ../datasets/variable-count-probe`；评估用前文同一 evaluate_class_aware.py，把 dataset 换成此目录即可，三个原始结果为 probe-hog.json、probe-cnn.json、probe-yolo.json。

## 硬件路径还存在一个应先解决的接口问题

用户提供的是彩色720p60输入；仓库 vision_top 的显示支路保留彩色，而 cop_* 快照支路在灰度分析及可选缩放之后。当前 Python 的 Lab 背景算法需要彩色图，逐目标分类需要足够清晰的原始目标裁剪。

因此应先明确：定位到底读取哪块图像缓存，PS 是否拿得到相应彩色/灰度整帧，目标框如何映射到原图，原分辨率裁剪从哪里读取。**把整幅720p先缩成64×64，再按目标裁剪，不能等价于每个目标拥有64×64输入。** 全图缩成224也需检查最小目标像素数。

候选交接方式为：定位用中等分辨率分析快照，目标分类从保留的足够分辨率帧裁剪；或者在PL定位并采集ROI。PS/PL分工、DDR/BRAM占用、搬运带宽和帧标识仍需团队冻结。本轮没有改变硬件接口。

64输入保留为优先候选：历史96输入仅有很小的精度变化，卷积计算量约2.25倍。网络保持普通卷积/GAP/FC，BN可折叠；更复杂模型应以实测收益和硬件支持为前提。

## 下一轮的收敛条件

1. 已增加变量数量、空场景和照明渐变开发探测；继续补齐未知件、角落目标、接触异常与真实阴影。不能继续只以固定六个物体优化。
2. 真实工位最小采样：记录零件实例和拍摄批次，覆盖高/低光、背景变化和不同朝向。公共渲染数据可预训练，真实相机数据用于模型选择及最终验收；最终测试批次提前隔离。
3. 使用“错误工单被放行率、正确工单一次通过率、复检比例、逐类漏检/混淆、整轮检查延迟”共同选方法，精度门槛按用户约定留到验收前冻结。
4. 64小CNN先做实际INT8 PTQ；若精度损失不能接受再做QAT。导出格式、累加/舍入/饱和规则须与协处理器契约相符，不能只导出权重便称可部署。
5. 用相同相机帧比较 ARM 与硬件路径；记录定位、搬运、分类、工单判定各段时间。真机结果决定定位是否值得下沉到PL。

以上1可继续离线实现；2需要实物/相机，4–5需要硬件契约与板卡。受控工位使传统定位成为更有根据的首选，但仍需通过真实工位采图和板卡实现才能定案。

## 复现与文件

从仓库根目录运行，Python 位于 `../venvs/localization-prototype/Scripts/python.exe`，以下以 `$py` 代替；训练和权重在 `../datasets/training-runs/`，逐图结果在工作区 `outputs/localization-exploration/`。

```powershell
$py = '../venvs/localization-prototype/Scripts/python.exe'
& $py sim/vision/test_class_aware_metrics.py
& $py sim/vision/controlled_classifier_study.py --dataset ../datasets/synthetic-yolo/seed-52 --output ../datasets/training-runs/controlled-hog --engine hog
& $py sim/vision/controlled_classifier_study.py --dataset ../datasets/synthetic-yolo/seed-52 --output ../datasets/training-runs/controlled-cnn-noaugment --engine cnn --epochs 40
& $py sim/vision/controlled_classifier_study.py --dataset ../datasets/synthetic-yolo/seed-52 --output ../datasets/training-runs/controlled-cnn-augment --engine cnn --epochs 40 --augment
& $py sim/vision/controlled_classifier_study.py --dataset ../datasets/synthetic-yolo/seed-52 --output ../datasets/training-runs/controlled-cnn-border --engine cnn --epochs 40 --preprocess-mode border
& $py sim/vision/calibrate_classifier_bn.py --dataset ../datasets/synthetic-yolo/seed-52 --weights ../datasets/training-runs/seed-52-scene-cnn-bn64.pt --output ../datasets/training-runs/controlled-cnn-calibrated
& $py sim/vision/probe_localization_backgrounds.py --output ../../outputs/localization-exploration/background-probes
& $py sim/vision/evaluate_class_aware.py --dataset ../datasets/synthetic-yolo/seed-62/val --engine hog --weights ../datasets/training-runs/controlled-hog/best.yml --output ../../outputs/localization-exploration/hog-train-only.json
& $py sim/vision/evaluate_class_aware.py --dataset ../datasets/synthetic-yolo/seed-62/val --engine hybrid --weights ../datasets/training-runs/controlled-cnn-border/best.pt --output ../../outputs/localization-exploration/cnn-border.json
& $py sim/vision/evaluate_class_aware.py --dataset ../datasets/synthetic-yolo/seed-62/val --engine yolo --weights ../datasets/training-runs/seed-42-yolov8n/weights/best.pt --confidence 0.65 --output ../../outputs/localization-exploration/yolo-reference.json
```

本轮针对评分、重复预测/拒识与预处理一致性的3项回归通过；覆盖两种填充方式及64/96输入。git diff --check 无输出，但相关新文件尚未跟踪，该命令不覆盖未跟踪文件全部内容。正式芯片实现、真实工位验收及旧权重兼容仍未完成。
