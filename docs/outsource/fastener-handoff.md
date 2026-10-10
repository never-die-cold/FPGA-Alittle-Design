# 紧固件视觉外包交接索引

供模型、板端和联调负责人使用；说明交接材料拆分位置、与项目文件的关系及复现缺口。
接收日期：2026-10-10，核对基线：`dev/exe @ 051aefa`；本次完成文件接收，未进行算法或实机验收。

## 拆分位置与项目入口

交接材料已按项目职责拆分，整包目录已移除。7 份原始说明文档保存在 [外包文档目录](fastener-vision-2026-10-07/README.md)，该目录只含 Markdown；模型、脚本与实验结果分别并入根目录对应目录。48 项交付材料均有逐文件去向和 SHA256，不修改原始文档。原文中的原仓库路径、包内路径和历史相对链接保留为交付快照；当前项目入口以下表为准。

| 内容 | 拆分位置 | 项目维护入口 |
|---|---|---|
| 进展与部署方案 | `docs/outsource/fastener-vision-2026-10-07/`，原文保留 | [进展汇报](../工作进展汇报.md)、[受控流水线方案](../修订方案-受控流水线.md)，项目维护版 |
| 实验与数据审计 | 同上，原文保留 | [探索审计](../localization-exploration-audit.md)、[数据审计](../localization-dataset-audit.md)，已有同内容版本 |
| 定位、训练和评估代码 | 根目录 `sim/vision/` | 接收时 16 个脚本逐字节一致，合并去重；共享 ROI 改造后训练原件另存快照，见下文 |
| FP32 CNN、HOG/SVM 原型 | 根目录 `models/` | [BN 基线](../../models/cnn-bn64-baseline.pt)、[边缘填充模型](../../models/cnn-border-fill-best.pt)、[HOG/SVM](../../models/hog-svm-train-only.yml) |
| 逐图评估、训练记录、背景反例 | 根目录 `results/`、`results/images/` | [CNN 评估](../../results/cnn-border.json)、[HOG 评估](../../results/hog-train-only.json)、[空背景反例记录](../../results/images/report.json) |

接收时共 28 个文件与项目同路径文件逐字节一致；17 个仅换行/末尾空白不同，16 个 JSON 经解析核对内容一致；3 个为包 README 与两份中文报告的不同版本。脚本及同内容模型/结果合并去重；仅文本格式不同的模型/结果采用交付原字节，算法和数值内容未变。项目维护版说明独立于外包原文。

## 采用的方案与未完成项

主线为受控背景、稳定照明、互不遮挡的零件：OpenCV 定位 → 原分辨率逐目标裁剪 → 64×64 灰度小 CNN → 工单检查。HOG/SVM 为分类基线，YOLO 为软件对照。PS 定位先作部署评估，PL 下沉须由实测决定；量化先测 PTQ，精度不足再做 QAT。

- 原型权重是 FP32，不是正式 INT8/hex 文件；训练文档的候选网络和 MAC 预算不能直接套用这些权重。
- 未实现/未接入：正式板端定位、原分辨率 ROI 获取、CNN 协处理器与工业闭环；连续运动的触发、关联、去重未实现。
- 未验收：真实工位效果、INT8 精度、PYNQ-Z2 延迟与资源、工单误放行率；CPU 合成图数字不能替代这些指标。
- [定位委托需求](localization-requirements.md) 的接口、独立自测、ARM 计时和冻结合格线仍需逐项验收，本次方案包接收不等于 LOC-R1—R18 验收通过。
- 已有 [检查 V0 建议稿](../inspection-v0-contract.md) 提出取图与 ROI 规则，仍为未冻结建议，不由交接包自动替换现有接口。

## 复现前提与完整性检查

完整实验缺少原始图片/标注、生成场景、裁剪缓存与 YOLO 权重。原始 README 中的包内目录描述是交付时快照，当前路径以本表为准；其中 `../datasets/` 属于交付方环境。本次不使用工作区外数据作验证依据，后续需将获准数据、依赖与配置纳入仓库内可复现入口后再复跑，执行脚本以仓库根目录为当前目录。原环境为 Python 3.12、PyTorch 2.5.1 CPU、OpenCV 4.10.0、NumPy 1.26.4、Pillow 12.3.0、Ultralytics 8.3.17，未证明兼容 PYNQ 镜像。

接收前清单为 [manifest.csv](../../data/evidence/2026-10-10-fastener-handoff/manifest.csv)，拆分后去向为 [installed.csv](../../data/evidence/2026-10-10-fastener-handoff/installed.csv)。SHA256 保存原字节；TextSHA256 对文本统一 LF、忽略末尾空白，以兼容仓库的 Git 换行规则。从仓库根目录执行以下 PowerShell 命令可复核全部交付文件（不是算法验证）：

```powershell
$rows = @(Import-Csv 'data/evidence/2026-10-10-fastener-handoff/installed.csv')
$sha = [Security.Cryptography.SHA256]::Create()
$bad = @($rows | Where-Object {
    if (!(Test-Path -LiteralPath $_.InstalledPath)) { return $true }
    if ((Get-FileHash -LiteralPath $_.InstalledPath).Hash -eq $_.SHA256) { return $false }
    if (!$_.TextSHA256) { return $true }
    $text = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $_.InstalledPath)).Replace("`r`n","`n").TrimEnd()
    return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))).Replace('-','') -ne $_.TextSHA256
})
$sha.Dispose()
if ($bad.Count -or $rows.Count -ne 48) { throw 'Installed integrity FAIL' }
"Installed integrity PASS: $($rows.Count)/$($rows.Count) files"
```

拆分核对结果：`Installed integrity PASS: 48/48 files`。描述文档、模型、脚本和结果已分别放置，不再保留混装的整包目录。

## 2026-10-10 离板改造注记

当前 `sim/vision/train_scene_classifier.py` 的预处理已转发至共享模块
`src/pynq_host/roi_preprocess.py`；原签名和默认 `opposite` 模式保留，文件回放显式采用 `border`。
交付原字节保存在 `sim/vision/archive/fastener-vision-2026-10-07/train_scene_classifier.py`，
`installed.csv` 仅调整这一项去向，原始哈希不变，48/48 完整性检查仍通过。
快照用于审计和像素对拍，不作为独立训练入口；活跃训练入口仍在 `sim/vision/`。
新共享实现与交付原函数的 24 组像素对拍通过，证据见[离板检查](../offline-inspection.md)。
这些测试不包含缺失的原始数据集训练、准确率复验或板端部署。
