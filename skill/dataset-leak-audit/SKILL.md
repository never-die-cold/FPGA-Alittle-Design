---
name: dataset-leak-audit
description: Use when collecting or receiving a labeled image/dataset for training, before training on data split into train/val/test, when auditing a delivered dataset for leakage or structural defects, or when writing dataset manifests and fixtures. 数据集防泄漏审计：会话级划分、实物编号、文件字节+解码像素双哈希、哈希清单与夹具；结构 PASS ≠ 数据齐全 ≠ 来源可信。Trigger on 数据集 / 泄漏 / 划分 / manifest / 标注 / 采集. Not for model training or quantization themselves.
---

# 数据集防泄漏审计（dataset-leak-audit）

一句话规则：**集合划分按"拍摄会话 + 实物个体"而不是按帧；泄漏检查做到解码像素层；哈希清单只做修改检测——结构 PASS ≠ 数据齐全 ≠ 来源可信，三个声明分层写。**

## 四层防泄漏检查（每层独立拒绝）

| 层 | 判据 | 挡住什么 |
|:---|:---|:---|
| 1 来源层 | 同一 `session`（拍摄会话）出现在两个 split | 相邻帧/同布置混入集合 |
| 2 文件层 | 同一 `source_sha256`（原始文件字节）跨 split | 复制文件、改扩展名 |
| 3 像素层 | 同一 `pixels_sha256`（解码后像素字节）跨 split | **改名、重压缩、换格式**——文件字节变了但像素没变仍被拒 |
| 4 实物层 | 同一 `specimen_id`（全局实物编号）跨 split | 同一实物两边出现 |

- 帧身份 = `(session, frame_id)`，不是文件名（同编号可跨会话）。
- `obj_id` 是帧内编号，**不能**当实物身份；缺 specimen_id 只报缺口（`missing_specimen_ids`），不编造身份。
- 同一实物编号的类别声明跨行必须一致。

## 清单与文件规则（可执行校验）

- 清单必需列固定、未知列/重复列/缺格拒绝；坐标半开区间 `[x0,x1)×[y0,y1)`、画面内、面积非零、同帧正面积不相交（边界相接允许）。
- 图像校验 `IMREAD_UNCHANGED` + 头校验：灰度/16 位/错误尺寸**拒绝**，不静默转 uint8。
- `raw/` 里未登记的 PNG 报错——目录与清单必须完全一致（防漏登）。
- 空场景登记一行条件信息、类别/坐标全空、**只允许进 test**。
- 每帧目标数上限显式传参；覆盖统计（类别×光照×朝向×数量档）输出缺口清单作补采依据，**不伪造缺类的数量**。

## 哈希与夹具的换行陷阱

- 报告记录 CSV/PNG/解码像素三套 SHA256 + 工具与运行环境版本；报告先写 `.pending` 再改名，输出文件已存在即拒绝（防覆盖证据）。
- **Git `eol=lf` 规范会在入库时改写文本字节** → 哈希关联的夹具/清单必须显式 `lineterminator="\n"` 生成；首次（改前）摘要存档保留为过程记录。
- 接收外部交付物：逐文件记录去向 + **原字节 SHA256 与文本规范化哈希双哈希**（"仅换行差异"显式分类，不静默合并）。
- 来源声明边界：`source_kind` 只是显式声明；报告中 `capture_origin_authenticated` / `label_accuracy_verified` 恒为 false——**哈希不能证明来源真实、不能证明标签正确**。

## 使用方法

- 参考实现（本仓库，可改编）：`sim/vision/audit_fastener_dataset.py`（CLI 审计器：结构/泄漏/覆盖，报告 JSON）、`sim/vision/generate_dataset_audit_fixture.py`（夹具生成器，显式 LF）；测试 `sim/vision/test_dataset_audit.py`、`test_dataset_manifest.py`，接入 `bash sim/scripts/run_inspection_python.sh`。
- 流程：采集侧按会话交付（先交先标）→ 审计器跑结构+泄漏 → 覆盖缺口回传补采 → 人工复核（清晰度/标签正确性/相似帧）另做，工具不替代。

## 已验证效果

- 13 组回归 PASS（非法行/框、缺帧、灰度/16 位、重复编号、重叠/相接、超限、四层泄漏、缺实物编号、覆盖缺口、来源必填、报告覆盖拒绝）；
- 夹具审计 4 帧/3 目标 PASS；报告 SHA256 与 Git 过滤后 blob 摘要逐文件一致（换行陷阱修复后）；外部交接包 48/48 完整性 + 链接 52 条全过。
- 来源（`report/llm_log/`）：`2026-10-10-dataset-audit.md`、`2026-10-10-fastener-handoff.md`、`2026-10-03-data-collection-protocol.md`

## 失效条件

- 只查精确重复：感知相似/相邻帧（同一摆放微扰动）需人工或专用工具，本方法不覆盖；
- 标签正确性、清晰度、曝光质量、来源认证在工具能力之外（报告恒 false 的原因）；
- 时序/视频数据集的"会话"定义需另行设计（本方法以静态帧为准）。
