# 外包材料接收清单（历史）

`manifest.csv` 和 `installed.csv` 保留接收时点的路径、大小及校验记录，用于对照 Git 历史 `cd7290e`。它们不是当前工作树的文件完整性清单：后续已退役 YOLO、HOG/SVM 和旧过程材料。

当前保留的 FP32 原型见 [models](../../../models/README.md)，现役 r6 模型、训练输入和 INT8 参数见 [CNN r6 包](../2026-10-28-cnn-r6/README.md)。历史 CSV 原样保留，不用当前目录缺少旧支线文件推断接收失败。
