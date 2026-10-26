# ROI 数据集交接单（J05 准备）

> 状态：交接格式与结构检查已实现；真实数据、标签真实性、训练效果均为 **UNVERIFIED**。
> 对象：WC 负责标注、生成 ROI 和交付；JL 负责审计后训练/量化；NC 提供合规原帧。

## 1. 交付内容

```text
<dataset>/
├── annotations.csv
├── images/{bolt,nut,washer}/*.png
└── splits/{train,val,test}.txt
```

- `annotations.csv` 表头固定为
  `file,class,source_file,source_width,source_height,x0,y0,x1,y1`。
- `file` 是相对数据集根目录的 ROI 路径；`source_file` 保留可追溯原帧路径。
- 类别只允许 `bolt`、`nut`、`washer`；每个 ROI 是 64×64、8-bit、单通道灰度 PNG。
- bbox 使用原帧坐标的半开 XYXY：`0 <= x0 < x1 <= source_width`，
  `0 <= y0 < y1 <= source_height`；零面积和越界均拒绝。
- 三份 split 清单每行一个 `file`；必须互斥、覆盖全量 ROI，且每份均含三个类别。

## 2. 数量与划分

- 工具的最小结构自测仅要求每类在每个 split 至少 1 个，**不代表可训练或可发布**。
- J05 首轮规划目标：每类至少 300 个可用 ROI；精确数量和类别不均衡必须随报告披露，
  不得为凑数复制图片。此数是待 WC/JL 确认的采集目标，不是冻结精度契约。
- 按采集会话、优先按实物个体分组后约 70/15/15 划分；禁止把相邻帧或同一实物的
  近重复样本拆到不同集合。测试集必须来自独立会话且训练时不可见。
- 上游仍按采集规程准备首轮至少 600 张原帧；原帧数与 ROI 数是不同口径。

## 3. 来源、标注与预处理

- 正式来源必须是已声明的 PYNQ HDMI 原始 PNG；PC 侧 UVC 或 Pi 直采不能静默替代。
  每个 `source_file` 应能追溯到原帧清单及其 SHA256。
- WC 逐目标人工核对类别和 bbox；空场景不生成 ROI，错料/遮挡等拒绝样例另行留档。
- 使用 `src/pynq_host/roi_preprocess.py` 的
  `scene-gray-border-padding-v1`：BGR bbox 转灰度，目标长边缩放到 42 像素，
  `INTER_AREA` 插值，以裁剪边缘中位数填充并居中到 64×64 uint8 画布。
- 生成 ROI 时须记录工具版本/提交和命令。结构审计不复算原帧到 ROI 的像素变换，
  因而不能替代来源、标签和预处理复现的人工审阅。

## 4. WC 交付步骤

1. 生成上述目录、CSV 与三份 split 清单，文件使用 LF 文本和 UTF-8。
2. 执行：

   ```bash
   python3 tools/check_roi_dataset.py <dataset> --output <dataset>/roi-audit.json
   ```

3. 交付数据集、`roi-audit.json`、生成命令、源帧清单和异常说明给 JL。
4. JL 只在报告为 `PASS_STRUCTURE_ONLY` 后接收；仍须另审标签、来源、泄漏与真实精度。

## 5. 自动判据与边界

工具拒绝缺文件、额外/遗漏 ROI、重复或跨 split 文件、非法类别、尺寸/通道错误、
bbox 越界或零面积，并输出逐文件 SHA256、类别和 split 分布。仓库内合成自测入口：

```bash
bash sim/scripts/run_coprocessor_iverilog.sh roi_dataset
```

`PASS_STRUCTURE_ONLY` 只表示结构、几何、划分和哈希一致；不证明标签正确、数据独立、
模型精度、综合实现或板级结果。

## 6. 参考

- 原帧采集与会话划分：`docs/runbooks/fastener-data-collection-protocol.md`
- 既有原帧清单审计：`sim/vision/audit_fastener_dataset.py`
- 预处理实现：`src/pynq_host/roi_preprocess.py`
