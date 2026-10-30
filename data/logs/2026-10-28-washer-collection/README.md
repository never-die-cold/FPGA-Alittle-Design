# 2026-10-28 CNN 继续训练与本地实验隔离

- 基线：dev/riscv / cfbded8 + 既有工作区改动；主机 Asia/Shanghai。
- 用户确认当前摆放 5 个垫圈，后续明确“我们就用CNN了，YOLO相关的都移除库，只保留在本地”。本轮主线为既定 64×64、四卷积 CNN 与 C02 INT8；没有运行 YOLO 训练。
- 当前板端 `8765` 在线，仍为上一运行包；本轮没有切换位流、装载新权重或运行 RTL 仿真/综合。

## 真实样本

`initial/` 的 720p BGR 原帧经视觉检查为 5 个垫圈。`series-r1` 的运动过滤过严，25 秒保留 0 组；原始失败留档。
`series-r2` 修正全局亮度漂移影响并放宽运动阈值后保留 1 个新摆放、5 个 ROI；其余 35 次因候选数不符、12 次重复位置而拒绝，不能算新增训练样本。
连同初始静态摆放，本次实际新增 2 个摆放/10 个 ROI。`annotations-confirmed-train.json` 合并前两组用户确认的 18 个 ROI，共 4 个摆放、28 个 ROI；类别数 bolt=6、nut=6、washer=16。
新样本类别来自用户明确的单类场景，定位框由助手对原图视觉核对；没有用模型预测反推类别。第 3 组未加入训练或校准。

## 训练和 PTQ 原始结果

| 候选 | 训练拟合 | 校准 FP32/INT8 一致 | 第3组 FP32 正确 | 第3组 INT8 正确 | 第3组 FP32/INT8 一致 |
|---|---|---|---|---|---|
| r1（此前） | 17/18 | 18/18 | 8/9 | 8/9 | 9/9 |
| r2 | 28/28 | 25/28 | 8/9 | 8/9 | 9/9 |
| r3 | 28/28 | 26/28 | 8/9 | 8/9 | 9/9 |
| r4 | 28/28 | 28/28 | 7/9 | 7/9 | 7/9 |

真值来自第 3 组用户已确认的 bolt 3/5/8、nut 0/4/7、washer 1/2/6。完整对照在 development-summary.json；逐框 logits 在 layout03-r2/r3/r4/。
该开发集已反复查看和诊断，虽然没有用于梯度或 PTQ 校准，也不能当作未触及的正式测试集。r4 校准改善没有转化为开发集提升，不宣称训练已完成或量化验收通过。

- r2：从 r1 继续 80 epoch，lr=0.00005，seed=20261028，冻结 BN running statistics，按类别数量加权，避免垫圈新增造成训练偏置。
- r3：从 r2 再训练 80 epoch，加正确类别 logit 间隔目标 2（权重 0.25），改善分类对量化扰动的稳定性。
- r4：从 r3 再训练 80 epoch，增加相对背景的低对比度与轻微模糊增强。
- 量化范围搜索只读这 28 个训练/校准 ROI，因子 1/1.05/1.1/1.2/1.35/0.95/0.9，按校准一致数和最接近 1 的规则选 1.0，未用第 3 组选择量化因子。
- 原始日志 training-r2/r3/r4.log、ptq-r2/r3/r4.log、calibration-r4.log；实际 CLI 均退出 0。PTQ_COMPLETE 只表示容器导出/比较完成，不保证一致率达到发布标准。

## 复现入口

```powershell
python -X utf8 sim/scripts/collect_single_class.py --label washer --count 5 --seconds 25 --output data/logs/<新采样目录>
python -X utf8 sim/scripts/fine_tune_real_rois.py --annotations data/logs/2026-10-28-washer-collection/annotations-confirmed-train.json --weights sim/build/real-roi-adapt-20261027-r1/fp32.pt --epochs 80 --lr 0.00005 --seed 20261028 --balance-classes --output sim/build/<新r2训练目录>
python -X utf8 sim/scripts/fine_tune_real_rois.py --annotations data/logs/2026-10-28-washer-collection/annotations-confirmed-train.json --weights sim/build/<r2训练目录>/fp32.pt --epochs 80 --lr 0.00005 --seed 20261028 --balance-classes --min-logit-margin 2 --output sim/build/<新r3训练目录>
python -X utf8 sim/scripts/fine_tune_real_rois.py --annotations data/logs/2026-10-28-washer-collection/annotations-confirmed-train.json --weights sim/build/<r3训练目录>/fp32.pt --epochs 80 --lr 0.00005 --seed 20261028 --balance-classes --min-logit-margin 2 --camera-augment --output sim/build/<新r4训练目录>
python -X utf8 sim/scripts/calibrate_real_rois.py --weights sim/build/<r4训练目录>/fp32.pt --annotations data/logs/2026-10-28-washer-collection/annotations-confirmed-train.json --output data/logs/<新的范围比较.json>
python -X utf8 sim/scripts/quantize_real_rois.py --annotations data/logs/2026-10-28-washer-collection/annotations-confirmed-train.json --weights sim/build/<r4训练目录>/fp32.pt --model-id 0x4A303255 --activation-headroom 1 --output sim/build/<新PTQ目录>
git diff --check
git diff --cached --check
```

## 本地保留与改动范围

YOLO 三个原跟踪文件只执行 git rm --cached，仍留在原路径；字节 SHA256 在 local-only-detector-inventory.json，实际复核 3/3 保留未变。新增专用脚本、预训练模型和实验日志由 .gitignore 排除，sim/build/ 本已忽略。
混合评估器 compare_localizers.py / evaluate_class_aware.py 去掉 YOLO 分支和依赖，原版备份在 `sim/build/yolo-local-backup-20261028/`。
历史交付文档与 manifest 保留来源记录，并标注 48/48 接收快照不再是当前树的完整性门禁。
本轮未提交或推送；Git 索引中有 3 个撤出项，其他业务改动和新样本仍待整理入库。

验证：真实采集/训练/量化 CLI、6 个脚本 AST、两个评估器 --help、YOLO 文件保留哈希、忽略规则、已跟踪执行代码无 ultralytics 导入；git diff --check 和缓存区检查均通过。
未完成：新候选的板端数值对拍、稳定的跨姿态/光照真实精度；后续竖立螺母的失焦画面已单独保留，等待清晰重拍，不把压力图直接作为合格训练输入。

## 2026-10-30 重复图片去重

下列编号图与保留图逐字节相同；比较 JSON、ROI 和原帧保持不变。原路径可从 `a631fd2` 恢复。

- `layout03-r2/numbered.png`、`layout03-r3/numbered.png`、`layout03-r4/numbered.png` → [相同编号图](../2026-10-28-standing-nut/layout03-after-r5/numbered.png)
