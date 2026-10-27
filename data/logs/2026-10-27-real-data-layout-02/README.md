# 2026-10-27 真实摆放 02、确认标签与首轮微调

- 基线：dev/riscv / cfbded8 + 当前工作区脚本；日期为主机 Asia/Shanghai。
- 用户保持同批三类各 3 件，重新摆放后允许抓图；不以工单匹配作为采集门槛。
- 本轮 24 次 UVC 读取只保存一张末帧，不计为 24 个独立样本。原帧 1280×720 BGR、PNG，SHA256 `88d85f53c37b6625694174e3452eb1c8b3badba6f9d9a67050ea97907fb99d79`。
- `comparison/` 保存 9 个 ROI、相应 INT8 字节、编号图、对照图及 logits；原模型 FP32/INT8 分类一致 9/9，但垫圈仍被判为 nut。一致率不等于准确率。

## 逐物体标签

`annotations-draft.json` 是视觉标注草稿；用户随后原话确认“两组标注都正确”，落为 `annotations-confirmed.json`，作为训练输入，未改动原草稿。

- 第 1 组：bolt 0/1/7，nut 3/6/8，washer 2/4/5。
- 第 2 组：bolt 1/2/5，nut 0/4/6，washer 3/7/8。
- 共 18 个真实 ROI，同一工位/实物的开发训练样本；未分配独立正式验证/测试集。

## 实际训练与量化

```powershell
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/<新采集目录> --frames 24
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-27-real-data-layout-02/uvc/raw.png --package build/board-package-product-20261027-r1 --truth-counts 3 3 3 --output data/logs/<新比较目录>
python -X utf8 sim/scripts/fine_tune_real_rois.py --annotations data/logs/2026-10-27-real-data-layout-02/annotations-confirmed.json --output sim/build/<新训练目录>
python -X utf8 sim/scripts/quantize_real_rois.py --annotations data/logs/2026-10-27-real-data-layout-02/annotations-confirmed.json --weights sim/build/<训练目录>/fp32.pt --output sim/build/<新量化目录>
git diff --check
```

本次实际输出分别为 `sim/build/real-roi-adapt-20261027-r1`、`sim/build/real-roi-ptq-20261027-r1`。
`training-r1.log`：固定 seed=20261027、80 epoch、lr=0.0001、冻结 BN running statistics，原图与旋转/亮度增强共同训练；训练拟合从 11/18 提升到 17/18，退出 0。不是验证精度，也没有选用第 3 组来选 epoch 或调学习率。
`ptq-r1.log`：只用前两组已经预处理的 64×64 ROI 校准，避免重复 letterbox；C02 五层参数、36,032 字节 PROVISIONAL payload，FP32/INT8 校准分类一致 18/18，退出 0。
FP32 SHA256 `0f68c6354cb3c258e73c8ae8b3a512f67192c7023fa1b70290f6a56a3b622a72`；payload SHA256 `58b3d8c684534c98138e48caf3a8a8f67ca51ebf79090804a66215a4bc84c945`，CRC32 `0x6f4d2bf7`，model_id `0x4a303252`。

## 产物及边界

候选模型与参数的精选存档见 [开发模型包](../../evidence/2026-10-27-real-roi-adapt-r1/README.md)。
本步新增 `sim/scripts/fine_tune_real_rois.py`、`quantize_real_rois.py`，并让 `check_real_scene_models.py` 可通过显式 `--reference-package` 对已验证旧包检查整数计算器后评估新参数。
没有运行 RTL 仿真、综合或将新权重装板；旧包当前运行状态不被此离板训练改写。第 3 组仅用于后续开发对照，详见[留出摆放记录](../2026-10-27-real-data-layout-03/README.md)。
待办：更多真实位置/朝向/光照及独立会话/实物采样、少数 nut/washer 混淆、量化分歧、板端数值对拍和正式模型验收。
