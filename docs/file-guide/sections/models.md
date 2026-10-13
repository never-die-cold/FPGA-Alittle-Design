# models：逐文件说明

3个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。

| 文件 | 一两句话说明 | 关联文件（最多展示5项） |
| --- | --- | --- |
| **models** | | |
| [models/cnn-bn64-baseline.pt](../../../models/cnn-bn64-baseline.pt)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 交接的64×64灰度CNN FP32基线权重；inspection_model等软件工具加载它，不是正式INT8部署包。 | 所在目录说明：[README.md](../../../README.md) |
| [models/cnn-border-fill-best.pt](../../../models/cnn-border-fill-best.pt)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 交接的边缘颜色填充ROI方案CNN FP32权重；需与预处理版本及对应实验结果一起使用。 | 所在目录说明：[README.md](../../../README.md) |
| [models/hog-svm-train-only.yml](../../../models/hog-svm-train-only.yml)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | OpenCV HOG/SVM传统分类基线模型；用于软件对照，不是CNN硬件权重。 | 所在目录说明：[README.md](../../../README.md) |
