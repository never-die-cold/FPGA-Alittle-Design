# CNN r6：清晰竖立螺母开发候选

- 日期：2026-10-28（Asia/Shanghai）；源码 cfbded8 + 工作区脚本，未提交、未上板。
- 训练输入：前两组 18 个 ROI + 两组纯垫圈 10 个 ROI + 一组清晰螺母 5 个 ROI，共 5 个摆放/33 个 ROI（bolt=6、nut=11、washer=16）。类别来自用户确认；单类新增画面的框由助手复核，纸边误框不入训练。
- 模型：原 64×64 灰度、四卷积/BN/ReLU、GAP、FC 3 类结构，继续符合 C02 参数排布；没有改 RTL 或硬件网络结构。
- 从 r3 继续 80 epoch，lr=0.00005，seed=20261028，BN running statistics 冻结、类别加权、分类 logit 间隔目标 2。r6 在每 10 轮检查点中按训练正确数、再按干净训练交叉熵选择第 70 轮；没有用开发图选择检查点。最后 80 轮拟合为 32/33，所选 70 轮为 33/33。

## 结果与边界

| 场景/用途 | FP32 正确 | INT8 正确 | FP32/INT8 分类一致 |
|---|---|---|---|
| 训练/校准 33 ROI | 33/33 | 33/33 | 33/33 |
| 未入训练的清晰 5 螺母（2 竖立） | 5/5 | 5/5 | 5/5 |
| 第 3 组三类混合开发图 | 8/9 | 8/9 | 9/9 |

混合图的目标 6 仍是 washer→nut。上述对照使用同一工位及同一批实物，并已反复查看，不能作为正式独立测试集精度。两张开发图均没有进入本轮梯度训练或 PTQ 校准。
PTQ 仅使用 33 个训练 ROI；范围因子 1.0/1.05/1.1/1.2/1.35/0.95/0.9 按校准一致数选择，取最接近 1 的并列因子 1.0，不用开发图挑范围。
payload 是 36,032 B PROVISIONAL，model_id 0x4a303257，CRC32 0xa73ee0d9；不是整机包，没有 bit/hwh。

## 文件

- `fp32.pt` / `training.json`：实际候选及完整训练元数据；训练样本列表与原权重/标签 SHA256 均记录。
- `payload/provisional-model/`：INT8 payload、manifest 与哈希侧车。
- `quantization.json` / `calibration.json`：校准样本、逐 ROI 类别、激活范围及范围搜索原始数据。
- `reference/`：此前已实板对齐的旧模型与 roi_001 数值输入，只用于独立检查快速整数计算器的已知输出 [-12,-30,41]，不是新模型的识别结果。
- `manifest.json`：本包文件大小/SHA256、脚本指纹及来源。

## 复现

训练和采样历史见[垫圈记录](../../logs/2026-10-28-washer-collection/README.md)及[竖立螺母记录](../../logs/2026-10-28-standing-nut/README.md)。从仓库根目录运行，输出目录须用新名字：

```powershell
python -X utf8 sim/scripts/fine_tune_real_rois.py --annotations data/logs/2026-10-28-standing-nut/annotations-confirmed-train.json --weights sim/build/real-roi-adapt-20261028-r3/fp32.pt --epochs 80 --lr 0.00005 --seed 20261028 --balance-classes --min-logit-margin 2 --select-training-fit --output sim/build/<新训练目录>
python -X utf8 sim/scripts/calibrate_real_rois.py --weights sim/build/<训练目录>/fp32.pt --annotations data/logs/2026-10-28-standing-nut/annotations-confirmed-train.json --output data/logs/<新的范围搜索.json>
python -X utf8 sim/scripts/quantize_real_rois.py --annotations data/logs/2026-10-28-standing-nut/annotations-confirmed-train.json --weights sim/build/<训练目录>/fp32.pt --model-id 0x4A303257 --activation-headroom 1 --output sim/build/<新PTQ目录>
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-28-standing-nut/focused/raw.png --weights data/evidence/2026-10-28-cnn-r6/fp32.pt --package data/evidence/2026-10-28-cnn-r6 --reference-package data/evidence/2026-10-28-cnn-r6/reference --truth-counts 0 5 0 --output data/logs/<新姿态比较目录>
git diff --check
git diff --cached --check
```

二进制入档理由：冻结实际生成的开发权重与硬件可装载参数，体积不足 0.5 MiB；可由上述脚本和已保存的真实样本重建。未完成：候选的板端数值对拍、纸边误框处理、更多独立实物/会话验证及发布验收。
