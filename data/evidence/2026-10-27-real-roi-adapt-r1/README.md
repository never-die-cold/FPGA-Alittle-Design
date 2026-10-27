# 真实 ROI 开发微调与 PTQ 候选 r1

- 日期：2026-10-27；源码基线 cfbded8 + 工作区 `sim/scripts/fine_tune_real_rois.py`、`quantize_real_rois.py`。
- 用途：保留本轮由 18 个已确认标签的真实 ROI 生成的 FP32 权重和 C02 参数，供继续训练、量化对照；不是正式发布模型。
- `fp32.pt` 保存原网络结构和元数据；`training.json` 保存初始权重、标签哈希、seed、超参、训练样本列表和每阶段训练拟合。
- `payload/` 只保留有效模型容器/manifest/哈希；36,032 B，PROVISIONAL，model_id 0x4a303252。`quantization.json` 保存校准输入、激活峰值、逐 ROI 浮点/整数类别。
- 训练拟合 11/18 → 17/18；PTQ 校准一致 18/18。第 3 组未用于训练/校准；同场景留出一致合计 16/17，完整图分类真值确认见运行目录。
- 二进制入档理由：固定实际生成模型，避免后续训练覆盖候选；权重约 0.15 MB，payload 36 KB；完整 SHA256/长度及源码指纹在 manifest.json。
- 复现入口与训练数据：[训练记录](../../../data/logs/2026-10-27-real-data-layout-02/README.md)；[留出记录](../../../data/logs/2026-10-27-real-data-layout-03/README.md)。
- 未实现/未完成：本候选的硬件输出对拍、更多实物/会话的正式验证及发布验收。没有包含 bit/hwh，不将模型包误称为整机包。
