# LIVE 检查、显示与来源语义（C04 设计稿）

> 是什么：G0 冻结项 C04——统一 LIVE 检查在「关联 / 显示 / 来源标识 / 统计」四件事上的应用层语义；
> 补全 [plan.md](../plan.md) §1.3 最后一条（视频与结果轮次关联）在应用层的可执行边界。
> 给谁看：never-die-cold（板端服务实现与确认，N09/N10 验收口径）、jianglibo（C03 接口确认）、watercopper（EXE/服务实现）。
> 怎么用：逐项评审（文末确认清单 Q1–Q6）→ 确认后回写 plan.md §3.4/§5.3、[EXE README](../src/vision_client/README.md) 与验收矩阵。
> **本文不新增任何报文字段**——报文以[协议决策单](vision-sync-protocol-decisions.md) D6 v1.2 为唯一出处；新增字段一律走 §6 版本评审。
> 状态：设计稿 2026-10-10，待 NC/JL 确认（G0 门：C01–C04 书面一致）。
> 2026-10-14 NC本人确认Q1软件采集序号、Q3本轮capture权威原帧、Q5超10复检/未完整计数标识/映射零值非实测；[评审单](c04-nc-review-2026-10-14.md)记录原话。Q5待JL对齐及实现修复后验收，C04整体未冻结。
> 边界：首版＝静止工位、人工触发、轮次级关联；逐帧精确关联与连续运动不纳入首版（决策单 D1 前提）。

## 1. 术语与对象

| 术语 | 说明 |
|:---|:---|
| session_id | 服务端会话（uuid，D5）。复位 / Overlay 重载 / 换视频源 → 新会话，EXE 清空本地状态 |
| check_id | 检查轮次（uint32，服务端生成、单调递增回绕）；**(session_id, check_id) 唯一标识一次检查** |
| capture | 本轮检查所用的**完整原帧副本**（V0：base overlay 取帧后 PS 保存的 BGR 原图，[检查V0 §1](inspection-v0-contract.md)）；一轮一个新 capture |
| frame_id | Q1已由NC确认：服务的软件采集序号；不得冒充cop_frame_id，也不承诺与UVC同帧 |
| 工单 | 三类非负整数需求 + 参数（min-score / max-targets）。C03已冻结检查V0总需求1–10件、不开放零需求；C04应用层对齐仍待评审/实现 |
| config_id | EXE 确认生效的配置版本（D3 判据之一）；EXE 本地工单修订号随记录保存，不进报文 |
| 来源标识 | 输入来源（UVC / 文件回放 / 合成演示）× 结果来源（无 / MOCK / LIVE）× prototype 布尔 |

## 2. 关联模型

链条：**EXE 触发（带工单配置）→ 服务会话 → check_id → capture（本轮新帧）→ 定位/分类/判定 → 回包 → EXE 叠加与记录**。

### 2.1 轮次 ↔ capture：一轮一帧，禁止旧帧冒充

- 每次 `POST /v1/check` 必须产生**一个新 capture（新取帧）**；禁止复用上一轮帧重发（否则「重复画面不累计」的语义被破坏，服务侧缓存回放同样违规）。
- V0 实现约定（**2026-10-14 NC确认Q1**）：`frame_id`填本轮capture的软件序号（服务自增），声明“软件编号，非cop_frame_id，不承诺与UVC同帧”；capture原帧以文件保存，路径+SHA256进本轮产物目录。实时后端仍未接入。
- M3/V1 接入 cop 快照通路后 `frame_id` 改回硬件帧号语义 → 按 §6 版本评审，不改报文结构。
- EXE 不因 `frame_id` 匹配（D3 已冻结）；frame_id 仅展示与记录。

### 2.2 轮次 ↔ 工单配置

- 工单与参数由 EXE 提交，服务端返回 applied_config_id；EXE 以确认生效的 config_id 为准（沿用现有 `/v1/config` 流程）。
- 每轮结果锁定：session_id + check_id + config_id + **当轮工单内容（expected 计数）**。记录必须保存当轮 expected 与 config_id——只存 config_id 无法复现判定依据（W07）。
- 配置不符即撤框（D3，`rounds._state` config 分支已实现）；换工单后旧轮结果不得显示。
- **工单 ≤10 件（V0 候选）与协议 16 目标上限互不替换**：结果最多 16 个目标；超工单上限不截断放行——按[检查V0 §3](inspection-v0-contract.md) 转 RECHECK（**Q5** 确认表述）。C03 已冻结口径：16 为目标检测能力、10 件为检查 V0 业务策略候选（[三人清单](project-closeout-three-person-checklist.md)）；**能力上限不自动成为业务放行条件**。Q5 剩余项 = WC/JL 对齐超限 RECHECK 与部分计数标识（CSV 已加 `reasons` 列暴露 `target_limit`；界面口径待 NC 验收）。
- 超限映射注记（2026-10-10，W05 骨架实现，**待 NC/JL 追认**）：检查链候选超限时 decision 计数为
  `null`（"未完整计数"语义），而报文契约要求五计数 dict 必填；服务端（`vision_live_service.complete_decision`）
  映射为按报文内已列目标重算 actual/delta/missing/extra，verdict/reasons 保持 RECHECK——
  "不截断放行"语义不变，计数口径变化仅此一处，评审通过后回写本条为已冻结。
  10/14复核：FILE引擎超限实际返回空目标列表，映射会产生零计数与缺件差额；这些不是完整实测数量。现有EXE未区分该语义，见[待修项](c04-nc-review-2026-10-14.md)。

### 2.3 记录 ↔ 服务产物（W05 实现要求）

- 服务端每轮产物必须可由 **(session_id, check_id) 唯一定位**：capture 原帧、capture 字节哈希（`capture.sha256` 侧车）、逐目标 ROI、判定依据、结果 JSON；目录布局由 W05 定并写入服务 README（**Q3**）。
- 2026-10-15 FILE 原型性能策略：自动轮询只保留最新报文，手动携 `trigger_ref` 或
- EXE 记录（`records.jsonl`）引用：记录键 (session_id, check_id)（D9）+ 上下文截图；快照原帧属服务产物，EXE 按引用展示，不复制冒充自采。
  2026-10-14 NC确认Q3以本轮capture原帧为权威证据；真实LIVE快照读取/查看仍未实现，确认原则不代替功能验收。
- **快照读取与哈希核对（2026-10-13 实现，待 NC 确认）**：读取方按 (session_id, check_id) 定位轮次目录，依次核对 packet 白名单与绑定（session/check 与请求一致）、`capture.png` 字节哈希 == `capture.sha256`、引擎存在时 `result.json` 的 `provenance.source_sha256` 与 capture 哈希一致；任一不符大声失败。实现 `src/pynq_host/round_artifacts.py`（含 CLI：`py src/pynq_host/round_artifacts.py <root> <session_id> <check_id>`，供 NC 板端核对）。2026-10-13 之前的旧轮次无 `capture.sha256`，核对器按缺件拒绝。
- **记录重启去重（2026-10-13 实现，NC 点名项）**：`BatchRecords` 启动时从既有 `records.jsonl` 重建去重键与计数（键跨进程有效）；异常事件截图序号同样续编；损坏记录行大声失败。

### 2.4 请求重试语义（草案，待 NC/JL 确认，2026-10-13）

- 现状：每次 `POST /v1/check` 递增 check_id 并新取一帧；`/v1/latest` 复用只是调试口，**不等于 POST 幂等**（NC 评审登记项）。
- 草案（不新增协议字段，`trigger_ref` 已存在）：
  - **重试键 = `trigger_ref`**：EXE 每次"触发意图"生成唯一值，网络失败重试沿用同一值。
  - 服务对已完成轮次的 trigger_ref 在**本会话内存**保留窗口（候选 16 条）：命中返回原轮报文，不新取帧、不递增 check_id——重试不产生第二次检查。
  - **服务重启后保留表丢失**：同 ref 重试按新轮处理（session 已更换，EXE 本就不跨会话复用结果）。
  - **冲突**：trigger_ref 仅作关联、不携带参数，无参数冲突；重复 ref 且原轮未完成时，按"等待完成回原结果"或"回 409"二选一，由服务实现择一并写入 README。
  - **失败重试**：POST 超时/连接断时服务可能已执行——重试同 ref；已执行回原结果、未执行新轮，两种情况对 EXE 都是"一次采纳"（记录键 (session, check_id) 兜底不重复）。
- 实现前需 NC/JL 确认窗口大小与"重启后按新轮"的接受度；沿用现有字段，不动报文结构。

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
- **现状（2026-10-12，集成基线 `3e2e1c9`）**：已实现并离板验证＝框 / ROUND / TARGETS / REC / FRESHNESS / 撤框与等待 / MOCK ONLY / LIVE与PROTOTYPE徽标 / 文件回放 / LIVE类别与分数 / 工单差额 / 判定横幅。
  **未实现/未验收＝检查快照查看、真实硬件取帧/分类后端及完整LIVE实机闭环**。替身/FILE结果不替代硬件验收。

## 4. 统计表达（不完整统计的诚实约束）

- 任何展示或导出的统计数字必须带：**来源子集（LIVE 实录 / LIVE-prototype / MOCK / FILE）× 样本量 × 时间范围**；缺任一项不得展示。
- 未测量 → 显示“未测”，**不得填 0**；部分分类（class=null）计入“未分类”桶，不进类别计数；RECHECK 轮不计入 pass/fail，单列复检率。
- 首版不提供自动误报/漏报率——该统计需要人工 GT 对照（W02/W03）；只有在样本与真值齐备、且标出来源后才可显示。
- CSV 导出与 W10 材料引用同口径：PROTOTYPE / MOCK / 软件基线**不并入** LIVE 实机统计（plan.md §1.4 M4“目标与实测分开”）。

## 5. 记录与证据（D8–D10 的应用）

- 只有手动触发的有效轮次落记录（D8）；键 (session_id, check_id) 去重（D9）。
- 每条记录必须能回答：**哪个 session/round、用哪张 capture、按哪版工单、什么来源、判定依据是什么**。
- W07实现（2026-10-12核对）：schema v2 保存 `status`、原 `decision`（含当轮工单）、`prototype`、`protocol_version`；来源以现有 `mode+prototype` 表达，未新增报文字段。
  - 截图前缀已实现：MOCK=`mock_`、LIVE+prototype=`proto_`、真实LIVE无前缀；CSV兼容v1旧记录。
  - NC在本轮PR审查的理解题①②中明确认可来源标记和有效轮次证据绑定，[全文记录](../report/llm_log/2026-10-12-three-pr-review.md)。该确认不代替其他C04未决项或JL评审。

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

2026-10-12评审状态：Q2的PROTOTYPE前缀/记录v2来源语义已有NC明确确认，Q4的来源分组原则已有NC明确确认；Q4仍需JL一致。Q1/Q3/Q5/Q6及超限计数映射继续待相应责任人确认，C04整体仍为设计稿。C03已冻结16能力/10策略，但这不自动替代C04的应用层一致性评审。

2026-10-14更新：Q1/Q3已获NC本人确认；Q5获NC确认“超过10统一复检、未完整计数明确标注、映射零值不计实测”，继续与JL对齐，相关实现修复后再验收。Q4的JL一致、Q6及完整应用验收仍待完成。

## 参考

- [协议决策单](vision-sync-protocol-decisions.md)（D1–D11，唯一报文出处）
- [LIVE 接口样例（G0 互交件）](../data/evidence/2026-10-12-live-interface-sample/README.md)（合成数据非板上识别；含报文→显示映射与复现命令）
- [检查 V0 契约](inspection-v0-contract.md)（取图 / ROI / 成功定义）
- [离板检查](offline-inspection.md)（FILE_REPLAY 与证据规则）
- [EXE README](../src/vision_client/README.md)（当前实现与入口）
- [plan.md](../plan.md) §1.3 / §1.4 / §3.4

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-10-10 | 首版设计稿：关联模型、快照/视频边界、来源四态、统计约束、记录扩展、版本评审条款；Q1–Q6 待 NC/JL 确认 | watercopper（EXE 前端） |
| 2026-10-10 | W06/W07 落码：EXE LIVE 显示（PROTOTYPE/判定横幅/类别分数/实际工单）、记录 schema v2（decision/prototype/proto_ 前缀）；W05 骨架开工，登记超限映射注记待追认 | watercopper（离板应用链） |
| 2026-10-12 | 按PR整合与实际回归更新W06/W07状态，记录已有NC来源/有效轮次确认；不新增协议字段，不代签C04整体冻结或实机验收 | NC离板续工 |
| 2026-10-13 | 服务落 `capture.sha256` 侧车 + `round_artifacts.py` 快照核对器（§2.3，待 NC 确认）；新增 §2.4 请求重试语义草案（待 NC/JL 确认）；记录重启去重落地（§2.3，NC 返场执行单点名项） | watercopper（离板应用链） |
| 2026-10-14 | 补充Q1/Q3/Q5源码复核与专项证据；同步C03已冻结10/16分层，登记超限零计数缺口；C04仍待确认 | NC离板续工 |
| 2026-10-14 | NC本人确认Q1/Q3与Q5原则；Q5继续交JL对齐并在实现修复后验收，未代签完整C04或硬件通过 | NC本人 / Codex记录 |
