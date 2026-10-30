# 2026-10-28 五螺母、两竖立姿态诊断

- 日期：2026-10-28；dev/riscv / cfbded8 + 当前工作区。
- 用户说明原位为 5 个螺母，新加的两个为竖立姿态；类别是人工真值，不使用模型预测替代。
- `initial/raw.png`：24 帧读取后保存 720p BGR 实拍，SHA256 e672a1cd2dedf6c38b5a2ed1a3068db1a468dd122d10016518e30ad75f97d2bb。
- `settled/raw.png`：再等待并读取 72 帧后重拍，SHA256 66d953c8da53a92efdcd09f6b6ea23e196d24ce4b42d37ae788833cc0aa52db1。两次原图均可见失焦、边缘模糊。

`before-training/numbered.png` 中目标 0 是纸张接缝误框，不是螺母；目标 1/2 为竖立的两个，3/4/5 为平放螺母。
当前 r3 的 FP32 和 INT8 把真实 5 件都判为 bolt（0/5），另外把纸边也判为 bolt；两者结果一致不意味着识别正确。
`model-diagnostic.json` 记录同样的 5 个 ROI：原始模型、r1、r2、r3 的 FP32 均 0/5；r4 仅 1/5，因此不将问题仅归因于本轮继续训练。
这一组暂作为画质/姿态压力记录，未加入训练或校准；已请求用户保持物体原位并调整对焦，清晰后重新抓图。

```powershell
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/<新清晰采集目录> --frames 72
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-28-standing-nut/initial/raw.png --weights sim/build/real-roi-adapt-20261028-r3/fp32.pt --package sim/build/real-roi-ptq-20261028-r3 --reference-package build/board-package-product-20261027-r1 --truth-counts 0 5 0 --output data/logs/<新比较目录>
```

采集与比较 CLI 退出 0，仅证明过程和产物保存完成，不是识别通过。等待采集完成前的一次图像打开失败因文件尚未生成，之后已正确打开实际原帧。
未实现/未完成：自动清晰度拒收、清晰的竖立螺母数据覆盖及其可靠分类；本次由人工视觉检查发现失焦。

## 对焦后采样、训练与 r6 结果（后续完成）

用户回复“已调整对焦，可以重新抓图”。`focused/raw.png` 中轮廓变清晰，定位为 5 件：编号 0/1 竖立、2/3/4 平放。该图的 SHA256 为 59e310fb4d4c4c0306b250451bfc5402976c4898424ce872cfc4dda0a1b53b13，始终未入训练/校准。
r3 在这张图上 FP32 为 3/5（两个竖立仍误判 bolt），INT8 为 5/5，分类一致 3/5；不能因为 INT8 恰好全对而忽略不稳定性。

`series-focused` 的 25 秒连拍没有发生可记录的新独立摆放（0 组、47 次重复姿态拒绝），未把重复视频帧当新数据。之后改为用户确认新位置后静态抓图。
`train-pose/raw.png` 为用户重新摆放并保留两枚竖立后的清晰图，SHA256 fd1bcce9e1fd191fe63af5694f743a772e35bd9899556262b2e5bed4f94fe7bb。该图原定位 6 框，其中目标 0 为纸边，排除；只用 1–5 的真实螺母（2/3 为竖立）训练。
`annotations-confirmed-train.json` 合并之前 28 个 ROI 和这 5 个螺母，共 33 个 ROI；没有加入模糊图或 focused 对照图。

- r5：从 r3 继续 80 epoch，分类加权与 logit 间隔目标 2，最后一轮训练拟合 32/33；PTQ 校准分类一致 33/33。focused-after-r5 对照中 FP32/INT8 均 5/5；混合第 3 组均 7/9。
- r6：重现同一 r3→训练过程，仅增加按训练拟合/干净交叉熵选择检查点。选中第 70 轮（33/33），没有用开发集选权重；最后第 80 轮 32/33 的结果仍留在日志和 training.json。
- r6 PTQ：33 个训练 ROI 校准，范围搜索只在校准输入上做，选 1.0；payload model_id 0x4a303257、36,032 字节、SHA256 ffc2620df59ab0292a4130d6741fb71b73d972696198a992a21a63877d2b12fa、CRC32 0xa73ee0d9，分类一致 33/33。
- focused-after-r6：FP32 与 INT8 均识别 5/5，包括两个竖立螺母，分类一致 5/5。layout03-after-r6：FP32/INT8 均 8/9，目标 6 的垫圈仍判 nut，分类一致 9/9。

原始训练、量化、范围搜索、比较日志分别保留 training-r5/r6.log、ptq-r5/r6.log、calibration-r6.log 和各比较目录；CLI 均退出 0，不把过程完成等同于正式分类验收。
候选归档：[CNN r6](../../evidence/2026-10-28-cnn-r6/README.md)。当前可识别这张清晰图中的竖立姿态，但更多朝向/实物与独立会话仍须采样；新模型尚未上板，纸边误框和自动清晰度拒收仍未实现。

## 2026-10-30 重复图片去重

下列编号图与保留图逐字节相同；比较 JSON、ROI 和原帧保持不变。原路径可从 `a631fd2` 恢复。

- `layout03-after-r6/numbered.png` → [layout03-after-r5/numbered.png](layout03-after-r5/numbered.png)
- `focused-after-r5/numbered.png` → [archive-check-r6/numbered.png](archive-check-r6/numbered.png)
- `focused-after-r6/numbered.png` → [archive-check-r6/numbered.png](archive-check-r6/numbered.png)
- `focused-before-training/numbered.png` → [archive-check-r6/numbered.png](archive-check-r6/numbered.png)
