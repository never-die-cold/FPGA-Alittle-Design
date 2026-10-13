# data-scripts：逐文件说明

6个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。

| 文件 | 一两句话说明 | 关联文件（最多展示5项） |
| --- | --- | --- |
| **data/scripts** | | |
| [data/scripts/.gitkeep](../../../data/scripts/.gitkeep)<br>目录占位 · 已纳入Git（含暂存） | 让Git保留尚无正式内容的目录；它不包含设计、数据或验收结果。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/scripts/coremark_score.py](../../../data/scripts/coremark_score.py)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 按固定CoreMark迭代与时钟口径计算性能指标；用于核报告的数据整理。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[docs/coremark.md](../../../docs/coremark.md) |
| [data/scripts/cpi_harness.py](../../../data/scripts/cpi_harness.py)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 解析固件testbench的PASS/周期/退休输出并计算CPI；与run_cpi_matrix的原始日志配套。 | 所在目录说明：[data/README.md](../../../data/README.md) |
| [data/scripts/img2hex.py](../../../data/scripts/img2hex.py)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 把真实输入图片转成灰度hex测试向量；数据生成后由视觉testbench加载。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[data/golden/vision/scaler_ds/input_gray.hex](../../../data/golden/vision/scaler_ds/input_gray.hex) |
| [data/scripts/m3_brevitas_drill.py](../../../data/scripts/m3_brevitas_drill.py)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 演练Brevitas QAT、INT8参数导出和整数结果复现；帮助对齐量化工具，不替代C02首网正式参数。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[docs/module3-model-training.md](../../../docs/module3-model-training.md) |
| [data/scripts/m3_train_drill.py](../../../data/scripts/m3_train_drill.py)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 用简化网络演练训练、量化和hex导出；它的高准确率不代表正式紧固件模型精度。 | 所在目录说明：[data/README.md](../../../data/README.md)<br>文本引用：[docs/module3-model-training.md](../../../docs/module3-model-training.md) |
