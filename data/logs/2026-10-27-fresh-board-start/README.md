# 2026-10-27 新启动与真实场景模型诊断

- 日期：2026-10-27，主机 Asia/Shanghai；板端时钟不作为实际日期。
- 基线：dev/riscv / cfbded8 加本次工作区改动；新 boot_id `30d6fc34-e372-4b0e-b9de-e8f4617b40d6`。本目录只描述该次启动，不复用前次故障结论。
- 用户阶段纠正：当前目标为真实数据、训练及量化对照；3/3/3 是本次人工场景数量，采数不以工单匹配为门槛。缺/多/错料工单验收留到应用阶段。
- 状态入口：[plan.md §3.1](../../../plan.md#31-当前状态)。

## 启动与运行记录

`boot-current.log` 中默认初始化完成后出现 `VISION_BOOT_PASS applied_config_id=1`。
`uvc-baseline/` 和 `uvc-product/` 分别保留视频基线、共存位流的真实 1280×720 BGR 帧。
旧板端包经 SHA256 检查；初次启动辅助脚本仍硬编码 2/3/4，已在执行检查前纠正为当时的 2/4/4（`restart-correct-order.log`）。
用户随后确认场景已变化，并明确本阶段不需工单反复确认。

最终运行使用 `/home/xilinx/cop-app-fresh-20261027-r2`，会话根目录 `/home/xilinx/cop-live-data-20261027-r1`，PID 见 `activate-data-session.log`。
辅助检查器参数设为 3/3/3，但不参与本目录独立的 ROI/模型比较。没有修改自启动配置。
位流仍为已部署的 b2690b0a… 共存版本；本次未综合新 RTL，也未把其多目标分类作为验收证据。

## 本次发现与改动

- 初次 EXE 握手成功；连续保存截图时退出 `preview image save failed`（`exe-check.log`），一次重试不持续保存截图，程序退出 0，但检查返回 HTTP 400，未产生有效批次记录。不能称 EXE 全链通过。
- 本次旧木纹场景原帧定位产生 22 个候选框，超协议最多 16 目标；原 COP 引擎返回全部候选导致协议拒绝。`latest-check-trace.log` 保留实际 capture/target_limit 证据。
- `src/pynq_host/cop_engine.py` 修复：候选 >16 时仍为 RECHECK/target_limit，线上传空列表，全部候选坐标与数量保留 cop_trace.json，不启动 CNN、不发截断列表。10～16 之间的原有未分类展示保留。
- `sim/vision/test_cop_service.py` 增加 16/17/22 边界检查，确认 HTTP 可返回合法 RECHECK、全部坐标留档且不调用推理。修复前负例在缺少 boxes 证据处失败；修复后退出 0。测试原有故障注入所打印的 503 WARN 是预期检查。
- `docs/contracts/vision-live-semantics.md` 同步现有协议内的超限行为；没有新增报文字段。
- 新应用包只从原包替换 cop_engine.py 和当前启动辅助脚本；35 文件 SHA256 在板端通过。首次用 sudo 执行 shell 内建 cd 的校验调用失败，已改普通 SSH 校验，原始失败/成功日志分别保留，不用汇总退出 0 掩盖失败。

## 真实场景独立比较（不依赖工单）

`uvc-counts-333/raw.png` 是用户确认 3 螺栓/3 螺母/3 垫圈后的新画面。
`sim/scripts/check_real_scene_models.py` 使用共享 ROI 预处理、现有 FP32 权重和已导出的 INT8 payload，处理相同的 64×64 ROI；整数计算器先对包内已知 roi_001 检查 logits [-12,-30,41]。

本开发图 local 阈值 20 时纸张接缝也产生候选；阈值 25 配合当前 close/open 得到 9 框。
此参数是在本图上探索的，不代表独立测试集效果，不把数量相同当定位精度证明。

FP32/INT8 argmax 一致 8/9。FP32 预测数量为 bolt=4/nut=5/washer=0，INT8 为 3/6/0；这些是预测，不替换人工真值。两模型均漏预测 washer，说明浮点模型本身尚不适配当前场景；一处量化分类分歧需随新数据重新校准检查。
逐 ROI 类别 GT 尚未人工复核，不计算分类准确率；没有训练新模型，也没有用这张开发图宣称泛化/量化精度通过。
产物 `model-comparison-r1/` 含 numbered.png、roi-grid.png、9 个灰度 PNG 和相应 INT8 字节、完整 logits/输入与模型哈希。

## 复现入口

```powershell
python -X utf8 sim/scripts/capture_uvc_raw.py --output-dir data/logs/<新的采集目录> --frames 24
python -X utf8 sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-27-fresh-board-start/uvc-counts-333/raw.png --package build/board-package-product-20261027-r1 --truth-counts 3 3 3 --output data/logs/<新的比较目录>
python -X utf8 sim/vision/test_cop_service.py
git diff --check
```

原始结果：model-comparison-r1.log 中 roi_count=9、agreement_count=8、COMPARE_EXIT=0；target-limit-after.log 中 PASS/TEST_EXIT=0。
启动脚本含本次 boot_id 与指定旧 PID 根目录保护，作为实际操作记录保存，不能不经核对直接在后续启动重放。
待办：逐物体人工标签、不同摆放/朝向和独立会话采样、训练及验证集划分、FP32 微调、代表性 ROI 校准和 INT8 对照。EXE 手动按钮/CSV、整机工单验收不属于本次训练诊断结论。
