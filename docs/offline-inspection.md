# 离板检查：共享 ROI、FP32 原型与 FILE_REPLAY

2026-10-10，基线 `dev/exe @ aa23206`；本轮为工作区实现，待用户理解确认后提交。
不需要板卡。目标是把交付模型接入一条可复现的软件流程，不代替真实工位验收。

## 当前状态

- 已实现并验证：Q01 结果字段白名单；共享 ROI 与交付原函数 24 组像素对拍；
  FP32 原型加载/推理；三类工单候选规则；文件定位/裁剪/推理/判定；证据保存与重复请求复用；
  Python 和 Windows EXE 的文件回放展示。
- 已实现但未验证：上述新模块的 PYNQ 环境兼容性、真实零件精度与工位效果。
- 未实现/未接入：板端原分辨率取帧、LIVE 分类服务、正式模型/PTQ/QAT、CNN 协处理器、
  RISC-V 工单判定和真实工业闭环。现用位流追溯、长时间/冷启动/断连复验仍待补。

## 运行入口

仓库根目录运行；需要 Python、NumPy、OpenCV、PyTorch；前端另需 Pillow。
本次推理环境为 Python 3.12.10、NumPy 2.5.1、OpenCV 5.0.0、PyTorch 2.14.0+cpu；
实际版本以 `result.json` 的 `provenance.runtime` 为准。EXE 使用既有固定依赖构建。
原交付环境不同，本次对拍是在同一个本地环境执行，尚未证明跨环境像素一致。

```powershell
python sim/vision/generate_inspection_fixture.py data/evidence/2026-10-10-offline-inspection/fixtures
python src/pynq_host/inspection_run.py data/evidence/2026-10-10-offline-inspection/fixtures/synthetic.png data/evidence/2026-10-10-offline-inspection/runs --weights models/cnn-border-fill-best.pt --request-id synthetic-001 --order 1 1 1 --min-score 0.8 --max-targets 10
python src/vision_client/preview.py --replay data/evidence/2026-10-10-offline-inspection/runs/synthetic-001/result.json --headless --save sim/build/inspection/viewer.png
```

示例中的 0.8 和最多 10 个目标均为候选参数，未冻结/未校准。运行器支持最多 16，
不放宽既有 MOCK 限制。合成图没有真实类别标注，结果 `CHECK_FAIL` 只证明流程执行，
不是模型准确率证据。CLI 退出 0 表示处理成功，工单失败仍是合法业务结果。
输出目录若已存在，输入内容、权重、参数、实现代码及运行环境必须一致才能复用；
更改任一项请使用新的 `--request-id`，禁止用旧结果冒充重新运行的结果。

完整回归与打包入口：

```bash
bash sim/scripts/run_inspection_python.sh
bash sim/scripts/run_vision_python.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1
python sim/vision/test_inspection_viewer.py --exe sim/build/vision-client/dist/vision_preview/vision_preview.exe
sim/build/vision-client/dist/vision_preview/vision_preview.exe --replay data/evidence/2026-10-10-offline-inspection/runs/synthetic-001/result.json --headless --save sim/build/inspection/viewer-exe.png
```

打包脚本包括既有 MOCK/HTTP 联调和新增 FILE_REPLAY 测试。离板回归使用独立入口，
不将 PyTorch 依赖加入旧八组视觉回归。

后续已增加五组[逐层参考准备测试](module3-prototype-reference.md)，该入口目前共十一组。
原六组历史日志保留；浮点参考包不改变文件回放/网络协议或 EXE 打包入口。

## 数据与模型规则

`roi_preprocess.py` 对半开区间原图框取 BGR 裁剪、OpenCV 灰度、INTER_AREA 缩放和边缘中位数填充。
64 模式长边 42，最后居中为 64×64 uint8；推理统一为 NCHW float32/255。
训练兼容包装保留旧默认 opposite；本轮推理显式采用 border。
测试从[交付原函数快照](../sim/vision/archive/fastener-vision-2026-10-07/train_scene_classifier.py)
提取独立参考，不用共享函数与自身比较。交付清单保留原哈希，完整性检查仍 48/48。

只接受带完整元数据的 `cnn-border-fill-best.pt`：三类顺序 bolt/nut/washer、64 输入、
`scene-gray-border-padding-v1`、border 模式、`fastener-4conv-bn-v1`。
元数据不足的 `cnn-bn64-baseline.pt` 不可直接代替。
实际网络为 4 个 Conv/BN/ReLU、全局平均池化及 Linear 分类；卷积通道依次为
1→16→32→32→64，第 1/3 层步长为 2，输出三类概率。
这是交付 FP32 原型，不是正式 INT8 网络，不能沿用候选硬件网络的 MAC 预算。

工单固定含 bolt/nut/washer 三个非负整数，期望总数为 1 到 max_targets。
delta=实际−工单，missing=max(-delta,0)，extra=max(delta,0)。
低分、未知类别、触边或超目标上限优先 `RECHECK`；无不确定项时，数量一致为
`CHECK_PASS`，否则 `CHECK_FAIL`。超上限不做截断推理，实际数量字段为 null，避免部分结果放行。
阈值只能标记低分，不能识别高分误分类；正式精度和误放行率需要真实有标注数据。

## 证据与回放

每个 request_id 独立目录保存原始文件 `source.bin`、无损 BGR 解码图、标注图、
每目标 uint8 ROI PNG 与逐行 hex、`result.json` 和其 SHA256。
hex 是像素参考，**不是量化权重**。JSON 保存来源/模型/代码哈希、运行环境、工单、
候选参数、分数/概率、数量差与裁剪关联。
CPU 计时只涵盖定位/ROI/推理/规则，排除模型冷加载和文件 IO，不能替代板端性能。

`result.pending` 完整写出后才改名为 `result.json`。重试校验清单和所有产物哈希，
同内容返回既有结果，不追加批次；冲突、缺失、篡改或越目录路径拒绝。
中断造成的未完成目录也拒绝复用；检查保留现场后改用新的请求号。
SHA256 用于意外修改检测，不提供来源签名或真实性认证。
前端回放在创建相机/联网轮次前分流，标明 FILE REPLAY / OFFLINE FILE / PROTOTYPE，
数量显示“实际 / 工单”；不产生新联网批次，也不把这些结果加入现有 MOCK 报文。

原始日志见[本轮验证记录](../data/logs/2026-10-10-offline-inspection/README.md)，
示例快照见[证据目录](../data/evidence/2026-10-10-offline-inspection/README.md)。
缺失原始训练/标注/校准图片仍阻止正式精度复验与可信 PTQ。
