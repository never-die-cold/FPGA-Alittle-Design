# 交付原型 FP32 软件参考包

2026-10-10，未提交工作区实现。`fp32-reference-v1/` 为完整生成件，约 3.5 MB。
无需硬件或原始训练图片；诊断图不带类别真值，不能验收分类精度。

包含 BN 折叠后的四层权重/偏置与 Linear、三个 uint8 输入（零/固定随机/条纹）、
归一化 input、四层 ReLU 输出、GAP 和 logits 的原始 PyTorch 完整期望张量。
所有张量均有 NPY 和逐行 hex；FP32 hex 是 IEEE754 位模式，不是 INT8 权重。
详见 manifest.json 的模式、来源模型、代码哈希、层审计与容差。

在当前目录运行，或把整个 `fp32-reference-v1` 复制后运行：

```powershell
python -I fp32-reference-v1/tools/check_model_reference.py fp32-reference-v1
```

检查器仅需 NumPy，不需 PyTorch、原 .pt 权重或仓库其他代码；逐元素检查容差为
atol=1e-4 / rtol=2e-5。三组归档包最大绝对差 0.00016784668，类别与原模型一致。
哈希、NPY/hex 位模式与逐层数值共同检查；这不是来源签名或硬件验证。

完整复现与解释见[逐层参考说明](../../../docs/module3-prototype-reference.md)，
原始日志见[验证记录](../../logs/2026-10-10-model-reference/README.md)。
