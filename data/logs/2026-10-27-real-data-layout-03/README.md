# 2026-10-27 第 3 组开发留出对照

- 日期：2026-10-27，主机 Asia/Shanghai；基线 dev/riscv / cfbded8 + 当前工作区脚本。
- 用户在前两组训练期间另行摆放；所有本目录图像均未进入本轮训练或 PTQ 校准。使用同一批实物、同一工位，不作为独立正式测试集。
- 固定定位设置沿用先前开发确定的 local / threshold=25 / min_area_ratio=0.00008，没有针对第 3 组改参数。

## 两次真实捕获

1. `uvc/raw.png`：24 次读取后保存一帧，实际仅见 8 件，少一枚螺栓；用户随后确认补入。SHA256 `b75d92beb9b41ff5333a76fab977f87934ebebb928a01c86cb8f7ba414e40c1a`。
2. `uvc-complete/raw.png`：补入后重新捕获，9 个定位框；其余部分摆放也发生改变，不覆盖/冒充原先 8 件图。SHA256 `ff5b165824339bf2ab39d64a1ec1f723d317b6cb7fd387ea0e49a0a2fbddc164`。

每次读取的分辨率/通道/像素及文件哈希在各 `metadata.json`。24 次连续读取不算 24 个独立布局。

## 对照结果

- `original-model/` 与 `adapted-model/` 为第一张 8 框图：原模型 FP32/INT8 一致 8/8，微调模型一致 7/8；保留这一处量化分歧，未用补拍结果掩盖。
- `original-complete/` 与 `adapted-complete/` 为补拍 9 框图：原模型及微调模型分别 FP32/INT8 一致 9/9。
- 微调候选的两张留出图合计一致 16/17，属于同场景开发比较，不是正式量化测试集精度。
- 完整图拟定类别为 bolt 3/5/8、nut 0/4/7、washer 1/2/6；人审确认状态见 annotations-confirmed.json（若尚未生成，则仍待用户核对）。不根据模型预测反推标签。

## 复现命令

```powershell
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-27-real-data-layout-03/uvc-complete/raw.png --package build/board-package-product-20261027-r1 --truth-counts 3 3 3 --output data/logs/<新旧模型比较目录>
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-27-real-data-layout-03/uvc-complete/raw.png --weights sim/build/real-roi-adapt-20261027-r1/fp32.pt --package sim/build/real-roi-ptq-20261027-r1 --reference-package build/board-package-product-20261027-r1 --truth-counts 3 3 3 --output data/logs/<新微调模型比较目录>
git diff --check
```

四个比较日志均退出 0；其含义为完成真实 ROI 比较，不是分类全部正确。
每轮 numbered.png / roi-grid.png / comparison.json 保存框、灰度 ROI、FP32/INT8 logits、模型及输入哈希。
新候选尚未装板；需要继续补真实样本和独立数据验收，未宣称整机识别完成。
