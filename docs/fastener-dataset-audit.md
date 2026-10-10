# 紧固件数据集：清单、集合泄漏与覆盖审计

2026-10-10，开发基线 `dev/model @ b51d46b`；理解题及补测已通过，完整记录见[协作记录](../report/llm_log/2026-10-10-dataset-audit.md)。
对应[采集规程](fastener-data-collection-protocol.md) §4/§6；仅审计数据结构和精确重复，
不执行训练、量化或分类，不验收真实标签、相机来源或模型精度。

## 入口与结果含义

```powershell
python -I sim/vision/audit_fastener_dataset.py data/datasets/fastener-v1 sim/build/vision/inspection/collection-audit.json --source-kind DECLARED_PYNQ --max-targets 10
```

输出须为新文件；已有 JSON 或同名 `.pending` 会拒绝并保留。报告先完整写 pending，再改名。
审计失败返回非零，不产生完整报告；成功返回 0 并打印 `PASS: DATASET_STRUCTURE_AUDIT`。
该 PASS 表示清单、文件和集合约束通过；类别缺口仍会写入报告，不表示数据已适合训练或验收。
重复执行请使用另一个新报告名；本工具没有报告复用或自动覆盖功能。

来源标识必须显式选择，不能靠文件位置推断：

| 标识 | 用途 |
| --- | --- |
| TEST_FIXTURE | 程序测试夹具；本轮图片和目标标签均为虚构 |
| PUBLIC | 外部/公共数据经显式适配后的清单；不是项目相机验收 |
| DECLARED_PYNQ | 提交者声明为项目取帧；工具仍不能证明采集来源真实 |

报告的 `capture_origin_authenticated` 和 `label_accuracy_verified` 始终为 false。
它记录 CSV、原 PNG 和解码 BGR 像素的 SHA256，以及审计代码和 Python/OpenCV/NumPy 版本。
摘要用于复现和修改检测，不提供真实性签名。

## 清单格式

数据根目录必须有 `manifest.csv`；每帧固定引用 `raw/<session>/<frame_id>.png`。
`frame_id` 是 `frame_00001` 一类五位编号，同编号可出现在不同会话，帧身份由会话+编号组成。
session 为 `sess-` 起头的小写字母/数字/连字符名称，禁止路径分隔符。
图像须为 PNG，解码后恰为 uint8 BGR 720×1280×3；不悄悄缩放、去 alpha 或转换 16 位图。
路径解析后必须仍属于数据根目录；raw 内遗漏于清单的 PNG 也拒绝。

必需列：

```text
frame_id,session,split,light,bg,spacing,obj_id,class,x0,y0,x1,y1
```

可选列：`notes`、`specimen_id`；重复列、未知列、缺失单元格拒绝。支持 UTF-8 和 UTF-8 BOM。
split 为 train/val/test；light 为 L0–L3；bg 为 dark/gray/wood。
spacing 是必须填写的条件标签，例如 1D、empty；工具不换算毫米或校验其测量真实性。
class 为 bolt/nut/washer；obj_id 是帧内唯一目标编号，不能代替全局实物编号。
坐标为十进制非负整数字符串，遵循 `[x0,x1)×[y0,y1)`，须在 1280×720 范围内且面积非零。
同一帧的条件信息须一致，目标编号与非空实物编号不能重复；按采集草案拒绝正面积相交的框，边界相接可接受。
每帧上限默认 10，可明确传入 1–16；这是候选采集参数，不替代正式契约冻结。

空场景仍须登记一行：class、obj_id、四个坐标及 specimen_id 全空，条件信息保留。
按现有采集规程只允许空帧进入 test；同帧不能同时有空标记和目标行，也不能重复空标记。
“空标记”是标注声明，工具不会从像素证明没有工件。

## 泄漏与覆盖

以下任一标识出现在不同 split 即拒绝：同会话、同文件字节摘要、同解码像素摘要、同非空实物编号。
因此改文件名或重新压缩同一张 PNG 不能绕过精确重复检查。
同一 split 内重复像素不作为跨集合泄漏，但在 `duplicate_pixel_frames_within_splits` 单独计数。
同一实物编号的类别声明还必须一致。

`specimen_id` 是采集者给真实物体的稳定编号，例如 bolt-a；同物体跨帧应复用编号。
省略该列或留空可以做结构审计，但报告会计入 `missing_specimen_ids`，不能宣称实物隔离已确认。
`all_specimen_ids_present` 为 true 只表示所有目标填写了编号，并不能证明编号与实物一一对应。

报告按 split 统计帧数、目标数、空帧数、三类目标数、光照/背景/spacing 帧数和每帧目标数直方图。
光照等条件每帧计一次，类别按目标计数；缺少的类别写入 `missing_classes`。
本工具不冻结数据量、划分比例或精度门槛，不因缺少某类而伪造其数量。

## 仓库复现与测试证据

```bash
bash sim/scripts/run_inspection_python.sh
```

当前为十三组：原十一组离板检查/参考 + dataset_manifest、dataset_audit 两组。
新增测试涵盖非法行/框、缺帧、灰度/16 位/错误尺寸、遗漏帧、重复编号、重叠/相接、
超限、会话/文件/像素/实物泄漏、缺少实物编号、覆盖缺口、来源必填与报告中断/覆盖拒绝。
独立子进程调用 CLI，不加载模型或 PyTorch。

已有[测试夹具和报告](../data/evidence/2026-10-10-dataset-audit/README.md)可直接复算到新输出：

```powershell
python -I sim/vision/audit_fastener_dataset.py data/evidence/2026-10-10-dataset-audit/fixture sim/build/vision/inspection/audit-review.json --source-kind TEST_FIXTURE --max-targets 10
```

生成全新夹具的仓库入口如下；目录已存在会拒绝。此入口仅生成均匀图和虚构标注，不能训练模型。

```powershell
python sim/vision/generate_dataset_audit_fixture.py sim/build/vision/inspection/new-audit-fixture
```

夹具 CSV 明确写 LF，使仓库的换行规范不改变其摘要；审计器仍对实际读到的原始 CSV 字节计算摘要。
首次 CRLF 夹具的报告和清单字节作为过程记录保留，不作为最终归档报告。
原始结果见[验证记录](../data/logs/2026-10-10-dataset-audit/README.md)。

## 未实现与人工核查

未实现：感知相似/相邻帧检测、GT CSV 与 manifest 交叉核对、朝向覆盖自动统计、
未知件/遮挡压力样本格式、真实标签完整性/清晰度/曝光审查及来源认证。
同一会话不能证明所有帧真正独立重摆；实物编号也依赖人工如实维护。
真实相机数据仍未收到，不能据此复验 FP32 精度、可信 PTQ 或正式 INT8。
CNN RTL、核握手、原分辨率板端取图与 LIVE 闭环仍未实现/未接入。
