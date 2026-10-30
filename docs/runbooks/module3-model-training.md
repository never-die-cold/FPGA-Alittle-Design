# CNN 模型训练、量化与交付

当前模型与验收状态统一见 [plan.md §3.1](../../plan.md#31-当前状态)。网络和整数语义以 [C02](../../src/coprocessor/design_v0.md) 为准，控制面、DMA 和 PS/核分工以 [C03](../contracts/coprocessor-integration-v0.md) 为准。

## 当前复现入口

冻结 r6 的输入、初始化权重、训练参数、量化命令和开发对照见 [CNN r6 包](../../data/evidence/2026-10-28-cnn-r6/README.md)。初始化检查点和全部 33 个 ROI 已保存在仓库内；新运行使用新的输出目录。

| 工具 | 用途 |
| --- | --- |
| `sim/scripts/collect_single_class.py` | 采集单类实物并保存 ROI；标签须人工确认 |
| `sim/scripts/fine_tune_real_rois.py` | 按已确认标注继续训练，固定随机种子、冻结 BN 统计 |
| `sim/scripts/calibrate_real_rois.py` | 只在训练/校准 ROI 上选择量化范围 |
| `sim/scripts/quantize_real_rois.py` | 从 FP32 权重生成 C02 INT8 参数与 payload |
| `sim/scripts/check_real_scene_models.py` | 同一场景的 FP32/INT8 与实物标签对照 |
| `sim/scripts/prepare_cnn_board_vectors.py` / `check_cnn_board_vectors.py` | 准备实板数值向量并核对逐目标硬件输出 |
| `sim/scripts/build_board_package.py` | 将指定 bit/hwh、模型和用例组装为板端包 |

```bash
bash sim/scripts/run_coprocessor_python.sh all
bash sim/scripts/run_iverilog.sh coprocessor all
```

## 交付边界

- 训练输入为逐目标 64×64 灰度 ROI；预处理、类别顺序、量化与张量排布遵循 C02。
- 发布时保留模型、payload、配置和对应黄金参考的版本关系；使用同一输入比较 ARM 与协处理器结果。
- 训练拟合、FP32/INT8 一致和硬件数值一致分别记录；识别正确性须由独立实物测试验收。
- 定位误检与分类误差分开统计，不能用阈值调整掩盖失败；整机验收条件见主计划。

## 历史工具链演练

`data/scripts/m3_train_drill.py` 与 `m3_brevitas_drill.py` 分别保留手工 PTQ 和 Brevitas INT8/QAT 演练入口。历史参数与原始结论见 `cd7290e:docs/runbooks/module3-model-training.md`；演练不作为正式模型精度。旧 HOG、YOLO 支线已退役，原接收记录见[历史交接清单](../../data/evidence/2026-10-10-fastener-handoff/README.md)。
