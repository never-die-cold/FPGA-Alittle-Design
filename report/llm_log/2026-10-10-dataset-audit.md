# 2026-10-10 协作记录：数据集清单与泄漏审计

> 标签：#vision #数据审计 #离板验证
> 平台：Codex desktop
> 开发基线：dev/model @ b51d46b；第39–50题及补测51全部通过，进入提交收口。

## 1. 任务与初始提示词

用户继续要求 continue；硬件仍不在手上。上一轮理解补测通过后已完成 PR #67 合并和五分支同步。
本轮阅读 workflow、主计划/核计划与 v0/v1 契约、训练准备及采集规程，核对干净工作区后选择
无需真实数据即可实现和测试的采集审计入口。先公告三类状态、目录和拆步，继续使用古法编程；
用户要求理解题最后一起给，持续有效，提交仍须本轮理解确认。
范围：src/pynq_host、sim/vision、sim/scripts、docs、data/evidence/logs、report/llm_log。
不改 RTL、核接口、MOCK/LIVE 协议或正式量化参数。

## 2. 方案与小步实现

1. 行级校验与仓库测试接统一入口：字段、名字、三类、半开框与显式空帧。
2. 清单读取与真实文件结构测试：720p uint8 BGR PNG、路径、帧条件、编号/框/目标上限。
3. 集合审计与测试：会话/文件/像素/实物泄漏、类别冲突、覆盖缺口与来源边界。
4. 补齐负例：遗漏 PNG、重复实物、灰度/16 位/空字节、重复表头；测试夹具保持仓库内。
5. CLI 与隔离子进程：来源必填，保存代码/环境，pending 写完改名，已有报告/中断现场拒绝覆盖。
6. 夹具生成与附加测试：四帧/三虚构目标/空场景、同 split 精确重复统计、来源与覆盖报告。
7. 归档复核的一行可移植性修复：CSV writer 显式 LF；原 CRLF 字节与首份报告保留。

每个实现步新增/修改非空非注释代码不超过100行。原估计约250行，补齐负例后实际六个主要小步
加一行可移植性修复，合计约380行代码与测试；扩步在执行前已说明。
文档整理不混入实现步计数。所有验证均使用仓库测试/CLI与仓库内输出。

## 3. 失败现象与纠错轨迹

功能测试未出现失败。归档复核发现 fixture CSV 使用默认 CRLF，审计报告摘要正确对应当时字节，
但 Git 的 eol=lf 入库规范会改写清单，使检出后的报告摘要不一致。
修复只让测试夹具 writer 明确写 LF，不让审计器改写用户真实输入。
首次 manifest 字节保存为 initial-manifest.bin（binary），首次报告保留；最终夹具归一为 LF 后重新审计。
后续重新跑新增两组并复核文件字节，不将首次报告当最终报告。

## 4. 四件套

① 文件：新增两个 host 模块、两个测试、审计 CLI 与夹具生成入口；统一入口增加两组。
新增审计说明、测试证据与本记录，更新采集/训练/离板指南及 host README 中已合并的状态。
② 验证：统一十三组 PASS/退出0；LF 修复后新增两组及最终十三组重跑 PASS/退出0；归档夹具审计4帧/3目标 PASS。
原始日志见[验证目录](../../data/logs/2026-10-10-dataset-audit/README.md)。
③ git diff --check：退出0；未跟踪文本末尾空白/合并标记检查：PASS。
归档报告复算逐字节一致，报告 SHA256 为 `3bc568723ae0aaf035fb67d51b14bdb79ef8d9ddcfaa3f2e58f6e82a9da31ee6`；
Git filter 与原字节逐文件 blob 摘要一致，证据入库不会被换行转换改写。
④ 未实现：相似帧/相邻帧检测、GT CSV 对照、朝向统计、未知/遮挡样本扩展、来源认证。
真实数据/标签完整性/分类精度未验收；可信 INT8、CNN RTL、核握手和 LIVE 闭环仍未实现/未接入。

## 理解门槛：逐段讲解

### A. 清单行

清单一行对应一个目标，或一个明确标记的空场景。允许列和必需列分开，避免可选备注变成必填。
会话与帧名只允许固定名字格式，不能当自由路径。坐标是半开区间，宽高直接作差。
空场景必须清空所有目标字段，并按现有草案只进 test；不能把漏写的目标自动当空场景。

### B. 帧与目录

同会话+帧号的多行归入一个帧，条件必须一致。只读取 PNG 原字节并解码一次，同时计算文件和像素摘要。
用 UNCHANGED 保留位宽/通道再检查，不把灰度、alpha、16位或错误尺寸悄悄适配成合法数据。
目标编号与实物编号帧内不能重复；框正面积重叠拒绝，相接不重叠。
raw 内所有 PNG 要与清单一致，避免默默丢掉没有标注的帧。

### C. 集合泄漏与覆盖

同会话的相邻帧不能分别进 train/test。相同文件字节及相同解码像素也不能跨集合，重新压缩绕不过像素检查。
obj_id 是帧内编号，specimen_id 才用于不同帧里的同实物隔离；缺少它时只报告缺口，不能编造身份。
条件按帧计数、类别按目标计数。三类数量缺口是后续补采依据，STRUCTURE_PASS 不等于训练资料齐全。

### D. 负例边界

邻接框可以同时存在，但两条目标行使用同一个已知实物编号会违反“一物一号”的声明。
同 split 的精确重复留统计供人工去重；跨 split 则直接拒绝。
本工具不靠像素识别有没有零件，也不检测仅仅很相似的两张图，更不证明人工标签真实。

### E. 报告入口

必须选来源标签以避免测试夹具冒充相机采集；来源是声明，报告始终标记未认证。
报告保存清单/帧/像素/代码和版本信息，便于同输入复算；不记录准确率。
pending 完成后才成为正式 JSON；旧报告和中断文件拒绝自动覆盖。命令失败的退出码必须非零。

### F. 夹具与可移植性

四张均匀图和虚构标签只检查清单/空帧/覆盖流程，不是真实分类数据。
报告可出现结构通过和类别缺口同时成立，两者分别描述“格式合法”和“数据缺什么”。
CSV 的 CRLF/LF 也是文件字节，入库转换会改变摘要；生成夹具必须与仓库换行规范一致。
对实际用户清单仍按原字节哈希，不用归一化后的另一份字节冒充来源。

## 理解门槛：集中题目（39–50）

39. 一张空场景为何仍要有清单行？若 class 为空但 obj_id 或坐标仍有值，为什么必须拒绝？
40. 同一 frame_00001 能否出现在两个不同会话中？真正的帧身份是什么，为什么不能仅按文件主名合并？
41. 720p 的16位 PNG 若按 COLOR 读取再转 uint8，为什么可能漏掉非法输入？本实现怎样避免？
42. raw 中多了一张未登记的 PNG，为何不能只审计 CSV 里列出的文件后宣布通过？
43. 把 train 图片改名、重压缩后放入 test：文件 SHA 可能不同，哪一道检查仍会拒绝？
44. obj_id 每帧都从 obj01 开始，能否用它证明实物 train/test 隔离？缺少 specimen_id 时应怎样报告？
45. 两个框右边/左边恰好相接是否算重叠？如果两个不同 obj_id 声称同一个 specimen_id，为什么仍拒绝？
46. 同 split 有相同像素帧，与跨 split 有相同像素帧，处理有何不同？能否据此说近似相邻帧检测已完成？
47. 报告标为 DECLARED_PYNQ 且哈希都一致，是否证明真实相机来源和人工标签正确？为什么？
48. 已有 report.json.pending 时为什么不覆盖？只看到终端 PASS 而进程后来退出非零，回归门应怎样处理？
49. TEST_FIXTURE 的 STRUCTURE_PASS，同时 train 缺 nut/washer，是否能开始正式精度或 PTQ 验收？分别缺什么？
50. CSV 从 CRLF 变 LF 后为什么摘要会改变？应修正夹具生成还是让审计器忽略原始换行，为什么？

用户首轮已回答；以下完整保留原答案，包括第43题需要修正的表述。首轮判定：11题通过，第43题待补测；当时未执行 commit/push/PR。补测通过见下文。

### 用户完整答案（编号1–12对应题39–50）

已按新文件核对，12 题简要回答如下：

---

1. **空场景仍需清单行，是为了声明该帧存在且归入 test；类别为空但编号/坐标/实物 ID 任一非空则矛盾。**
   `src/pynq_host/dataset_manifest.py:27-31`：空帧时 `class` 必须为空，同时 `obj_id`、四个坐标、`specimen_id` 也必须全空；否则报 “empty frame must not contain a target”。空帧还只能出现在 `test` split。

2. **两个会话可以都有 `frame_00001`；真正的帧身份是 `(session, frame_id)`。**
   `src/pynq_host/dataset_manifest.py:64` 用 `(row["session"], row["frame_id"])` 作为 key；`docs/fastener-dataset-audit.md:33` 明确同编号可跨会话。

3. **不能自动把 16 位 PNG 转 uint8，因为采集契约要求“无损 uint8 BGR PNG”，静默转换会改变像素语义。**
   `src/pynq_host/dataset_manifest.py:69-73` 先用 PNG 文件头校验，再用 `cv2.IMREAD_UNCHANGED` 读取，并断言 `shape == (720,1280,3)` 且 `dtype == np.uint8`，16 位图会直接拒绝。

4. **raw 里未登记的 PNG 不能忽略，因为契约要求 raw 与清单完全一致；未登记 PNG 可能是隐藏数据或遗漏。**
   `src/pynq_host/dataset_manifest.py:97-101` 把 `raw` 下实际 `.png` 路径集合与清单列出的集合比对，不相等就报 `unlisted raw PNG frames`。

5. **改名会改文件字节 SHA256，但无损重压缩后的解码像素不变；`pixels_sha256` 仍能发现泄漏。**
   `src/pynq_host/dataset_audit.py:29-31` 检查跨 split 是否出现相同 `pixels_sha256`（解码后的 BGR 像素字节摘要），也检查 `specimen_id` 跨 split；`docs/fastener-dataset-audit.md:58-59` 明确此条。

6. **每帧复用 `obj01` 不能证明实物隔离，`obj_id` 只是帧内目标编号。**
   `docs/fastener-dataset-audit.md:47,63-65`：`specimen_id` 才是全局实物编号。缺少 `specimen_id` 会累计到 `missing_specimen_ids`，`all_specimen_ids_present` 为 false。

7. **两框边界相接不算重叠；但不同目标编号使用同一非空 `specimen_id` 仍拒绝，因为同一实物不能出现两次。**
   `src/pynq_host/dataset_manifest.py:86-90`：相交判断用 `max(x0,a) < min(x1,c)` 且 `max(y0,b) < min(y1,d)`，边界相等（相接）不触发；但 `same_specimen` 为真时直接拒绝。

8. **跨集合相同像素 → 拒绝（泄漏）；同集合相同像素 → 计入 `duplicate_pixel_frames_within_splits`，不拒绝。**
   `src/pynq_host/dataset_audit.py:29-31` 跨 split 检查；第 50 行统计同 split 重复。这只是按解码像素字节 SHA256 的精确重复检查，**不等于感知相似帧检测**（`docs/fastener-dataset-audit.md:99-100`）。

9. **`DECLARED_PYNQ` 加正确哈希不能证明相机来源和标签真实。**
   `src/pynq_host/dataset_audit.py:45` 中 `capture_origin_authenticated` 和 `label_accuracy_verified` 始终为 false；`docs/fastener-dataset-audit.md:19-29` 说明 `source_kind` 只是显式声明，哈希仅用于修改检测。

10. **已有 `.pending` 不覆盖，是为了保留中断现场、避免产出不完整报告。**
    `sim/vision/audit_fastener_dataset.py:23-26`：输出文件或 `.pending` 已存在直接报错。回归门 `vision_run_checked` 要求退出码 0、日志有 `^PASS:`、且无 `FAIL/FATAL/ERROR` 行；仅打印 PASS 但退出非零仍不通过（`sim/scripts/vision_gate.sh:6-17`）。

11. **不能开始正式精度或 PTQ 验收。**
    `STRUCTURE_PASS` 只说明清单/文件/集合约束通过；缺失类别会写入 `missing_classes`（`src/pynq_host/dataset_audit.py:48-49`、`docs/fastener-dataset-audit.md:68-69`）。PTQ 需要真实、有标注、具代表性的 ROI 校准集，而当前夹具是虚构标签和合成图（`docs/module3-model-training.md:18-24,79-84`、`docs/offline-inspection.md:93`）。

12. **CRLF/LF 改变摘要，因为 `manifest_sha256` 直接对读到的原始 CSV 字节计算。**
    `src/pynq_host/dataset_manifest.py:56,102` 使用 `read_bytes()`。应**修正夹具生成**而非让审计器忽略：夹具 CSV 显式用 `lineterminator="\n"` 写入 LF（`docs/fastener-dataset-audit.md:94`），审计器仍按实际原始字节算摘要。

### 逐题判定

| 题号 | 用户编号 | 判定 | 依据 |
| --- | --- | --- | --- |
| 39 | 1 | 通过 | 明确空帧仍需登记，并拒绝矛盾目标字段。 |
| 40 | 2 | 通过 | 正确使用会话与帧号组合身份。 |
| 41 | 3 | 通过 | 正确保留原通道/位宽再检查，不静默转换。 |
| 42 | 4 | 通过 | 正确要求 raw PNG 集合与清单一致。 |
| 43 | 5 | 待补测 | 像素摘要判断正确，但仅改文件名不会改变内容摘要。 |
| 44 | 6 | 通过 | 正确区分帧内目标编号与全局实物编号，说明缺失报告。 |
| 45 | 7 | 通过 | 正确区分边界相接与重复实物声明。 |
| 46 | 8 | 通过 | 正确区分跨集合拒绝、同集合统计与未实现的相似帧检测。 |
| 47 | 9 | 通过 | 正确说明来源声明和哈希不认证来源或标签。 |
| 48 | 10 | 通过 | 正确保留 pending 现场，并要求退出码和日志同时满足。 |
| 49 | 11 | 通过 | 正确区分结构通过与真实精度/PTQ验收条件。 |
| 50 | 12 | 通过 | 正确按原始字节摘要，并修正夹具生成的换行规范。 |

### 第43题纠错与新补测题51

`source_sha256` 使用 `hashlib.sha256(pixels_raw)`，其中 `pixels_raw` 是 PNG 文件内容。
文件名和目录没有参与该摘要。因此只改名或逐字节复制文件，文件内容摘要和解码像素摘要都不变。
重新编码可能改变 PNG 文件字节；在字节确实改变、解码 BGR 完全不变时，文件摘要改变而像素摘要不变。
原答案关于像素摘要发现重压缩泄漏的结论正确，需要修正的是“改名会改文件字节 SHA256”。

51. 两个不同会话分别属于 train 和 test，清单均合法且不填 specimen_id。
    将 train 的 PNG 逐字节复制到 test，只改变会话目录和帧文件名：
    source_sha256 和 pixels_sha256 各是否变化，审计先在哪项身份检查拒绝？
    若改为重新编码，使 PNG 字节改变但解码 BGR 完全相同，拒绝位置怎样变化？

### 第51题用户完整答案

两种情形都基于 `src/pynq_host/dataset_audit.py:20-31` 的跨集合泄漏检查：按 `session`、`source_sha256`、`pixels_sha256` 顺序，任一标识值跨 split 即拒绝。

---

**情形一：逐字节复制同一 PNG，只改目录/文件名**

- `source_sha256`：**不变**（它是原始 PNG 文件字节的摘要，`dataset_manifest.py:75`）。
- `pixels_sha256`：**不变**（它是解码后 BGR 像素字节的摘要，`dataset_manifest.py:76`）。
- 因为 `source_sha256` 在 train/test 出现相同值，审计会最先在这里拒绝：
  `ValueError: cross-split leakage: source_sha256`（`dataset_audit.py:30-31`）。

---

**情形二：重新编码，文件字节改变但解码 BGR 完全相同**

- `source_sha256`：**改变**（文件字节变了）。
- `pixels_sha256`：**不变**（解码 BGR 相同）。
- 此时 `session` 和 `source_sha256` 都不跨 split 冲突，拒绝位置后移到 `pixels_sha256`：
  `ValueError: cross-split leakage: pixels_sha256`（`dataset_audit.py:30-31`）。

---

**补充**：未填 `specimen_id` 不会触发泄漏拒绝，但会累计到 `missing_specimens`（`dataset_audit.py:27-28`），并导致 `all_specimen_ids_present` 为 false。

判定：通过。两个摘要及两种情形的首个拒绝位置均正确，正确区分局部缺失计数与实物泄漏检查。
第43题的内容摘要缺口已补齐；本轮12题和1道补测全部完成理解确认，允许提交代码。
提交前只有理解记录及状态说明发生文档修改，已有十三组最终回归证据继续有效。

### 远端收口前检查

fetch 后发现 dev/exe 比开发基线新增 `7101a33`（LIVE 报文契约 v1.2 冻结）。
合并与同步必须保留此提交，不能把该分支回退到旧基线。具体 PR、提交和同步结果由本轮最终回复给出。

## 5. 经验沉淀

集合隔离要检查来源/像素/实物三个层面，文件名不是身份；结构一致性仍不能证明标签正确。
带来源摘要的文本必须考虑 Git 换行转换，初次正确的摘要也可能在检出后失配。
