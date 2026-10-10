# LIVE 检查、显示与来源语义（C04 设计稿）

> 是什么：G0 冻结项 C04——统一 LIVE 检查在「关联 / 显示 / 来源标识 / 统计」四件事上的应用层语义；
> 补全 [plan.md](../plan.md) §1.3 最后一条（视频与结果轮次关联）在应用层的可执行边界。
> 给谁看：never-die-cold（板端服务实现与确认，N09/N10 验收口径）、jianglibo（C03 接口确认）、watercopper（EXE/服务实现）。
> 怎么用：逐项评审（文末确认清单 Q1–Q6）→ 确认后回写 plan.md §3.4/§5.3、[EXE README](../src/vision_client/README.md) 与验收矩阵。
> **本文不新增任何报文字段**——报文以[协议决策单](vision-sync-protocol-decisions.md) D6 v1.2 为唯一出处；新增字段一律走 §6 版本评审。
> 状态：设计稿 2026-10-10，待 NC/JL 确认（G0 门：C01–C04 书面一致）。
> 边界：首版＝静止工位、人工触发、轮次级关联；逐帧精确关联与连续运动不纳入首版（决策单 D1 前提）。

## 1. 术语与对象

| 术语 | 说明 |
|:---|:---|
| session_id | 服务端会话（uuid，D5）。复位 / Overlay 重载 / 换视频源 → 新会话，EXE 清空本地状态 |
| check_id | 检查轮次（uint32，服务端生成、单调递增回绕）；**(session_id, check_id) 唯一标识一次检查** |
| capture | 本轮检查所用的**完整原帧副本**（V0：base overlay 取帧后 PS 保存的 BGR 原图，[检查V0 §1](inspection-v0-contract.md)）；一轮一个新 capture |
| frame_id | 报文透传字段。V0 语义待定格（Q1）：建议＝服务的软件采集序号；**不得冒充 cop_frame_id** |
| 工单 | 三类非负整数需求 + 候选参数（min-score / max-targets）。首版总需求 1–10 件（候选，未冻结），不开放零需求 |
| config_id | EXE 确认生效的配置版本（D3 判据之一）；EXE 本地工单修订号随记录保存，不进报文 |
| 来源标识 | 输入来源（UVC / 文件回放 / 合成演示）× 结果来源（无 / MOCK / LIVE）× prototype 布尔 |

## 2. 关联模型

链条：**EXE 触发（带工单配置）→ 服务会话 → check_id → capture（本轮新帧）→ 定位/分类/判定 → 回包 → EXE 叠加与记录**。

### 2.1 轮次 ↔ capture：一轮一帧，禁止旧帧冒充

- 每次 `POST /v1/check` 必须产生**一个新 capture（新取帧）**；禁止复用上一轮帧重发（否则「重复画面不累计」的语义被破坏，服务侧缓存回放同样违规）。
- V0 实现约定（**待 NC 确认 Q1**）：`frame_id` 填本轮 capture 的软件序号（服务自增），服务 README 显式声明“软件编号，非 cop_frame_id”；capture 原帧以文件保存，路径 + SHA256 进本轮产物目录。
- M3/V1 接入 cop 快照通路后 `frame_id` 改回硬件帧号语义 → 按 §6 版本评审，不改报文结构。
- EXE 不因 `frame_id` 匹配（D3 已冻结）；frame_id 仅展示与记录。

### 2.2 轮次 ↔ 工单配置

- 工单与参数由 EXE 提交，服务端返回 applied_config_id；EXE 以确认生效的 config_id 为准（沿用现有 `/v1/config` 流程）。
- 每轮结果锁定：session_id + check_id + config_id + **当轮工单内容（expected 计数）**。记录必须保存当轮 expected 与 config_id——只存 config_id 无法复现判定依据（W07）。
- 配置不符即撤框（D3，`rounds._state` config 分支已实现）；换工单后旧轮结果不得显示。
- **工单 ≤10 件（V0 候选）与协议 16 目标上限互不替换**：结果最多 16 个目标；超工单上限不截断放行——按[检查V0 §3](inspection-v0-contract.md) 转 RECHECK（**Q5** 确认表述）。

### 2.3 记录 ↔ 服务产物（W05 实现要求）

- 服务端每轮产物必须可由 **(session_id, check_id) 唯一定位**：capture 原帧、逐目标 ROI、判定依据、结果 JSON（含哈希）；目录布局由 W05 定并写入服务 README（**Q3**）。
- EXE 记录（`records.jsonl`）引用：记录键 (session_id, check_id)（D9）+ 上下文截图；快照原帧属服务产物，EXE 按引用展示，不复制冒充自采。

## 3. 显示语义：连续视频与检查快照的边界

### 3.1 双图像职责（谁是谁的证据）

| | 连续视频（UVC 采集卡画面） | 检查快照（capture 原帧） |
|:---|:---|:---|
| 身份 | 上下文显示；**不承诺与任何轮次同帧**（D1） | 该轮检查的权威图像，与结果坐标**严格同帧** |
| 叠加 | 轮次结果叠加：框 + 类别 + 判定；常显 ROUND / 年龄 / 来源徽标 | 框与类别为原图坐标天然对应，无映射误差 |
| 用途 | 实况操作、等待与撤框状态 | 记录与证据、复核（W06 快照查看） |
| 前提 | 画面域须与结果坐标同域（当前均为 1280×720）；**设备模式不符时禁止叠加**并显式提示 | 快照上只画本轮框，不画其它轮次 |

- 记录截图（D10）语义明确为：**记录时刻的含框画面（UVC 上下文）**，文件名前缀标来源；证据的权威图像是快照原帧，二者不得互换。
- 禁止清单：UVC 截图冒充检查证据；低分辨率分析快照冒充原图 ROI（C01）；用快照证明“实时”；空窗期保留旧框（D3 已禁）。

### 3.2 来源标识：四态清晰区分（W06 目标态）

| 输入来源 | 结果来源 | 顶栏徽标 | 叠加内容 |
|:---|:---|:---|:---|
| UVC 实况 | LIVE（prototype=false） | `LIVE`（绿） | 框 / 类别 / 分数 / 判定横幅 |
| UVC 实况 | LIVE + prototype=true | `LIVE` + **`PROTOTYPE`（恒显，不可关闭）** | 同上 + 离线产物标注 |
| UVC 实况 | MOCK | `MOCK ONLY`（琥珀） | 仅框（协议 MOCK 无类别/判定） |
| UVC 实况 | 无有效结果 | `WAITING FOR RESULT` | 无框 |
| 文件回放 | 离线产物 | `FILE REPLAY \| OFFLINE FILE`（+`PROTOTYPE`） | 框 / 类别 / 分数 / 实际-工单 |
| 合成演示 | MOCK | `MOCK ONLY` | 仅框 |

- `PROTOTYPE` 与 `MOCK ONLY` 同级：只要叠加的是**离线产物代实时结果**，徽标必须常显（D6 对齐 MOCK 的诚实约束）。
- 撤框条件沿用 D3（超龄 / 会话不符 / 配置不符 / 连续失败 / LIVE 未联接）；撤框即清框，只显示等待态。

### 3.3 叠加细节与现状缺口

- 目标标注：T 序号 + bbox + `class`（null → “未分类”）+ `score`（两位小数；缺失不显示）。
- 判定横幅：status（CHECK_PASS / CHECK_FAIL / RECHECK）+ 差额（missing / extra，取自 decision）；LOCATION_ONLY 显示“仅定位，无判定”。
- **现状（dev/exe @ fb168b1）**：已实现＝框 / ROUND / TARGETS / REC / FRESHNESS / 撤框与等待 / MOCK ONLY / LIVE 徽标位 / 文件回放视图；
  **未实现＝LIVE 类别/分数、工单差额、PROTOTYPE 徽标、快照查看、判定横幅（均为 W06 范围）**。

## 4. 统计表达（不完整统计的诚实约束）

- 任何展示或导出的统计数字必须带：**来源子集（LIVE 实录 / LIVE-prototype / MOCK / FILE）× 样本量 × 时间范围**；缺任一项不得展示。
- 未测量 → 显示“未测”，**不得填 0**；部分分类（class=null）计入“未分类”桶，不进类别计数；RECHECK 轮不计入 pass/fail，单列复检率。
- 首版不提供自动误报/漏报率——该统计需要人工 GT 对照（W02/W03）；只有在样本与真值齐备、且标出来源后才可显示。
- CSV 导出与 W10 材料引用同口径：PROTOTYPE / MOCK / 软件基线**不并入** LIVE 实机统计（plan.md §1.4 M4“目标与实测分开”）。

## 5. 记录与证据（D8–D10 的应用）

- 只有手动触发的有效轮次落记录（D8）；键 (session_id, check_id) 去重（D9）。
- 每条记录必须能回答：**哪个 session/round、用哪张 capture、按哪版工单、什么来源、判定依据是什么**。
- 现状缺口（W07）：
  - `records.jsonl` 的 `verdict` 预留字段读取顶层 verdict——v1.2 判定在 `decision` 内，现恒为 None；修正为保存 `decision` 原样。
  - 新增字段：`source` / `prototype` / 当轮工单内容；`schema_version` 递增为 2（**Q2**）。
  - 截图前缀：MOCK=`mock_`（已有）；PROTOTYPE 建议 `proto_`（**Q2**；MOCK 与 prototype 互斥——协议仅 LIVE 可带 prototype）。

## 6. 版本评审条款（不绕过白名单）

- 报文：任何新增字段/枚举 → 决策单登记 + 版本号递增 + `vision_protocol.py` 常量/校验/测试三处同步 + 合法与非法用例 + NC/JL 评审后冻结。EXE“未知字段拒绝”不得放宽。
- 记录：`schema_version` 独立递增，但每条记录必须能与协议版本对应（记录内保存 mode 与来源）。
- 禁止：以私有扩展字段（HTTP 头、附加键、文件名约定）传递未经评审的数据；EXE 侧不做“宽容解析”。
- 本文不新增报文字段；§2–§5 全部用 v1.2 已有字段 + 本地记录实现。

## 7. 确认清单（G0 互交）

| # | 待确认 | 对象 | 影响 |
|:---|:---|:---|:---|
| Q1 | V0 服务 `frame_id` = 软件 capture 序号（每轮必新帧；README 声明非 cop_frame_id） | NC | 关联可追溯；M3 换硬件帧号另走评审 |
| Q2 | PROTOTYPE 截图前缀 `proto_` 与记录 schema v2 字段（source/prototype/工单） | NC | W07 实现 |
| Q3 | 快照原帧 + ROI 由服务产物提供，EXE 按 (session_id, check_id) 引用 | NC | W05 接口 |
| Q4 | 统计口径分组（LIVE / prototype / MOCK / FILE）与 W10 材料一致 | NC/JL | 报告口径 |
| Q5 | 工单 ≤10 件与协议 16 目标的边界表述 | NC/JL | 验收矩阵 |
| Q6 | V0 的 status/decision 由 PS 软件判定产出，V1 迁 RISC-V 后同契约消费 | JL | C03 衔接 |

## 参考

- [协议决策单](vision-sync-protocol-decisions.md)（D1–D11，唯一报文出处）
- [检查 V0 契约](inspection-v0-contract.md)（取图 / ROI / 成功定义）
- [离板检查](offline-inspection.md)（FILE_REPLAY 与证据规则）
- [EXE README](../src/vision_client/README.md)（当前实现与入口）
- [plan.md](../plan.md) §1.3 / §1.4 / §3.4

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-10-10 | 首版设计稿：关联模型、快照/视频边界、来源四态、统计约束、记录扩展、版本评审条款；Q1–Q6 待 NC/JL 确认 | watercopper（EXE 前端） |
