# 2026-10-28 CNN r6 新混合摆放对照

- 日期：2026-10-28，Asia/Shanghai；基线 dev/riscv / cfbded8 + 当前工作区。
- 固定 CNN r6 权重和 INT8 参数，未针对本图训练、校准或调整定位阈值。
- 用户按混合场景准备后允许抓图，随后说明“我刚才放多了一个。。。”。原图视觉核对为 3 bolt、4 nut、3 washer，共 10 件；按实际摆放记录，不强求预设 3/3/3。
- 原帧为真实 USB Video 索引 1 的 1280×720 BGR；72 次读取后只保存一帧，不计为 72 个独立布局。SHA256 `7f34fb94915196dd36898ba72d029fdb4fee64e0bf81cfb7161e7cc523f7ff46`。

## 结果

编号图可见：bolt 0/6/8，nut 1/4/5/9，washer 2/3/7；其中 nut 4/5/9 为竖立姿态。框覆盖本次实际 10 个零件，没有纸边误框。
按这一视觉标签复核，FP32 和 INT8 均匹配 10/10；两者分类一致 10/10，预测计数均为 3/4/3。逐编号标签来自对原图的视觉复核，用户只确认了额外摆放一件，未单独确认每个编号，故标注状态为 DEVELOPMENT_VISUALLY_REVIEWED。
本图为同工位的新开发对照，不是独立实物/会话测试，也不证明整机已通过；新模型仍未装板。

`comparison/comparison.json` 的 human_scene_counts=3/3/3 是命令沿用的采集预设，不是实际计数；原始程序输出不改写。修正后的实际场景计数与标签在 `reviewed-result.json`，用于本图结论。

## 实际命令

```powershell
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/2026-10-28-mixed-standing-r6/uvc --frames 72
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-28-mixed-standing-r6/uvc/raw.png --weights data/evidence/2026-10-28-cnn-r6/fp32.pt --package data/evidence/2026-10-28-cnn-r6 --reference-package data/evidence/2026-10-28-cnn-r6/reference --truth-counts 3 3 3 --output data/logs/2026-10-28-mixed-standing-r6/comparison
git diff --check
git diff --cached --check
```

重跑时输出使用新目录，修正后的计数参数应为 `--truth-counts 3 4 3`。实际原始结果 comparison.log 中 roi_count=10、agreement_count=10、COMPARE_EXIT=0。
产物包括原帧及捕获元数据、编号图、ROI 网格、10 个灰度 ROI PNG/INT8 输入、两模型 logits、哈希与复核标签。本步仅新增数据记录并更新 plan.md，业务代码与模型参数没有改动。
待办：r6 板端数值对拍、更多独立摆放/实物/会话验证、旧低对比度垫圈问题；本图不加入训练集。
