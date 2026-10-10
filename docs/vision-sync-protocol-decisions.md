# 视频/结果同步协议决策单（EXE 前端 × 板端服务）

> 是什么：Windows EXE 与板端结果服务之间"检查轮次"同步契约的决策底稿——补全根目录 [plan.md](../plan.md) §1.3 悬置的"视频与网口结果对应关系"。
> 给谁看：watercopper（EXE 前端，本文维护者）、板端真实服务实现者（主责待定，见 D7）、never-die-cold（frame_id 硬件来源在快照通路）。
> 怎么用：评审逐项追认；冻结后回写 [vision_client README](../src/vision_client/README.md) 与 `vision_protocol.py`（schema 代码改动另起步骤，不在本单内动手）。
> 基线：dev/bench @ 01b3750（2026-10-06）。mock 接口 v1 现状见 [vision_client README](../src/vision_client/README.md) §模拟接口 v1。

## 0. 决策总览

| # | 决策项 | 状态 |
|---|---------|------|
| D1 | 关联粒度 | ✅ 2026-10-06 watercopper 拍板：轮次级起步，报文保留 frame_id |
| D2 | 检查轮次定义与触发 | ✅ 2026-10-06 watercopper 确认沿用预填推荐 |
| D3 | 有效性判据与过期/断联语义 | ✅ 2026-10-06 watercopper 确认沿用预填推荐 |
| D4 | 传输形态与服务地址 | ✅ 2026-10-06 watercopper 确认沿用预填推荐 |
| D5 | 会话生命周期 | ✅ 2026-10-06 watercopper 确认沿用预填推荐 |
| D6 | 报文 schema v1.1 | ✅ 2026-10-06 watercopper 确认沿用预填推荐；代码另起步骤 |
| D7 | 板端真实服务负责人 | ✅ 2026-10-06 NC（组长）本人确认接任；plan.md §3.4 已同步 |
| D8 | 批次记录：触发 | ✅ 2026-10-08 随离板实现落地：仅手动触发轮次是记录候选（0.3s 防抖） |
| D9 | 批次记录：去重 | ✅ 2026-10-08 落地：键 = (session_id, check_id)，一次确认的检查只记一条 |
| D10 | 批次记录：存储与标识 | ✅ 2026-10-08 落地：records.jsonl + screenshots/；MOCK 记录带 `mock_` 前缀 |
| D11 | 异常事件日志 | ✅ 2026-10-08 落地：状态迁移/会话变化/重握手失败 → anomalies.jsonl + 异常截图 |

## 1. 问题背景（为什么需要本单）

- 显示通路 `display_frame_id` 随像素进 HDMI 线后不可读取；PS 侧唯一可得的帧身份是快照通路 cop_buf 回放携带的 frame/config id（[design_v0.md](../src/vision/design_v0.md) §3.1）。
- USB 采集卡内部缓冲 1–2 帧（端到端延迟上界 125ms 实测见 `data/logs/2026-10-03-vision-onboard/`），时长不定——EXE 收到的画面与板卡帧号之间不存在可知映射。
- 根目录 [plan.md](../plan.md) §1.3：视频与网口结果必须建立帧/检查对应；过期结果、断联或无法确认的画面不得显示为当前检查通过。
- 结论：逐帧精确对齐在当前硬件形态下物理不可得；轮次级关联 + 年龄窗口是可验收的替代。

## D1 关联粒度（已拍板）

- **拍板状态**：✅ 2026-10-06 watercopper 选定轮次级起步。
- **结论**：结果按"检查轮次"组织与消费；EXE 在年龄窗口内把最新一轮结果叠加到采集卡画面并标注轮次号；过期/断联立即撤框。报文保留 frame_id（透传快照通路硬件帧号），M3 评审若需逐帧对齐（板端 OSD 烧帧号角标 + EXE 解码）再升级，不改报文结构。
- **适用前提**：固定机位、检查期间被检零件静止（与[采集规程](fastener-data-collection-protocol.md)同前提）。零件检查中移动的场景不承诺框画面对应。

## D2 检查轮次定义与触发

- **背景**：plan.md §1.3 交接表已定触发方向 EXE→PS（检查触发、工单配置）；"RISC-V 判定、EXE 展示记录"分工已冻结。
- **推荐**：
  - 一轮检查 = EXE 触发一次 → 板端抓一帧快照完成定位（M3 起含分类与工单判定）→ 回包。一次确认的检查只记一条批次（M3）；重复画面因触发驱动天然不累计。
  - check_id 由板端服务生成，uint32 单调递增回绕；EXE 触发请求可携带 trigger_ref 透传字段，服务端原样回显，供 EXE 关联自己的请求。
  - PS 周期自动模式（EXE 只订阅）列为可选增强，不进首版。
- **影响**：GET /v1/latest（拉模式）保留为调试口；正式触发走 POST /v1/check（schema 见 D6）。

## D3 有效性判据与过期/断联语义

- **推荐**：
  - EXE 侧有效性判据 = session_id 一致 + config_id 与 EXE 当前确认生效的配置一致 + created_at 年龄 ≤ max_age（默认 1.0s，与 mock v1 `is_current` 一致，命令行可调）。**frame_id 不参与匹配，仅透传展示**——这是对 mock v1 的语义修订，代码步骤同步。
  - 撤框条件（任一即撤）：年龄超窗；session 不匹配；config_id 不符（结果产生于旧配置，坐标可能失效）；HTTP 连续失败 ≥3 次；/v1/status 返回 hardware_connected=false。
  - 撤框后横幅显示"等待新结果"，不得保留旧框；恢复后以新轮次重新叠加。
  - 实现注记（2026-10-06，经 WC 质询修正）：EXE 触发间隔必须**小于**年龄窗口（默认 interval
    0.5s < max_age 1.0s），EXE 启动时校验——否则每轮结果在下轮触发前过期，画面周期性空窗；
    若改用大间隔则须同步放大窗口，会把"过期仍显示"的红线拉长，两害取其前。
  - 实现注记（2026-10-08 实机 flap 修复）：新鲜度改按 **EXE 接收时刻**（received_at）计量
    （overlay 与批次记录），不与服务端 created_at 跨机比较（板卡/EXE 时钟不同源）；同迭代
    "先取钟再请求"的负年龄不判超龄。created_at 保留在报文与记录中供诊断。
- **影响**：EXE 画面必须常显当前状态（轮次号 + 结果年龄），杜绝"静默旧框"。

## D4 传输形态与服务地址

- **推荐**：HTTP/JSON 既定——mock v1 三端联调已过，`vision_protocol.py` 校验复用；带宽无压力（16 目标 JSON < 4KB，轮次频率远低于视频帧率）。UDP/TCP 二进制不采用，列 M4 后增强项。
- 服务地址由 EXE `--endpoint` 传入，默认 `http://127.0.0.1:8765`；生产端口与发现机制待板端服务实现时冻结。

## D5 会话生命周期

- **推荐**：沿用 mock v1——session_id 由服务端生成（uuid）；板端复位、Overlay 重载或换视频源 → 新会话；EXE 不得跨会话复用结果（校验强制），检测到 session 变化即清空本地状态，并重新确认配置生效后才恢复叠加。

## D6 报文 schema v1.1（2026-10-06 已确认；实现缺口另批裁决）

- 保留 mock v1 全部字段与校验规则：version、mode、session_id、frame_id、config_id、width、height、created_at、status、targets（16 目标上限、**半开区间 bbox `[x0,x1)×[y0,y1)`**——宽=x1-x0、右下端点可恰为 w/h，与[定位外包需求](outsource/localization-requirements.md) L2 一致；退化/反向/越界拒绝、重复 target_id 拒绝）。
- 新增：check_id（uint32，轮次标识，见 D2）；trigger_ref（可选回显字段）。
- 预留：status 枚举 M3 起从 LOCATION_ONLY 扩展 CHECK_PASS / CHECK_FAIL / RECHECK（工单判定，枚举值届时冻结）；真实服务 mode=LIVE 且 hardware_connected=true——EXE 对 MOCK 结果恒加"MOCK ONLY"横幅（plan.md §3.4：样例结果可联调界面，不得记为板上识别）。
- 不动：单报文 ≤64KB；未知字段拒绝（严格校验不放宽）。

核查注记（2026-10-09，Q01）：上述 schema 与“未知字段拒绝”覆盖**结果报文**，
不能解释为只针对 POST 请求。v1.1 落码证据见[原验证记录](../data/logs/2026-10-06-vision-sync-schema/README.md)。
核查当时 `src/pynq_host/vision_protocol.py:validate_packet` 未实施完整结果字段白名单；
`vision_mock_service.py` 对请求字段的拒绝不能替代结果报文校验，现有 tb 未覆盖该负例。
本轮只登记，不改协议、Python 或 tb；最小修复和负例测试须用户另批裁决。

修复进展（2026-10-10，用户授权离板执行）：工作区已补齐顶层与逐目标字段白名单，
非对象与未知字段统一拒绝；保留现有可选 trigger_ref 和空目标列表。
仓库内 test_vision_protocol.py 覆盖3个合法/12个非法用例，旧代码先复现FAIL；
run_vision_python.sh 八组退出0，证据见[data/logs](../data/logs/2026-10-10-q01-result-fields/README.md)。
代码尚未提交，理解门槛待用户回答；此修复不开放 LIVE、分类或工单判定字段。

## D7 板端真实服务负责人（已定）

- EXE 前端 = watercopper（已定）。板端 PS 上的真实 HTTP 服务（消费 cop_* 快照、响应触发、MMIO 配置）主责 = **never-die-cold（2026-10-06 NC 本人确认接任）**。理由——EXE 开发机无网口，实机网口联调依赖队长环境；队长已有上板操作经验（2026-10-03 vision onboard 由其执行）。plan.md §3.4/§5.3 已同步。
- 过渡方案：服务未就绪期间，EXE 联调用 mock 服务（PC 或 Pi 宿主，pi-dev-roles R2），结果恒标 MOCK。

## D8–D10 批次记录（M3 起步，2026-10-08 随离板实现落地）

- **D8 记录触发**：只有**手动触发**（`c` 键/检查按钮，0.3s 防抖）的轮次是批次记录候选；
  自动间隔轮次（演示模式）永不落记录——结构性满足 M3"重复帧不增加批次计数"，
  视频帧/自动轮询再多也不产生记录。
- **D9 去重**：记录键 = (session_id, check_id)；同键重复写入被拒，"一次确认的检查只记一条"。
  结果未到/过期/断联不记录（异常事件与异常截图列 M3 项，独立于批次）。
- **D10 存储与标识**：`records.jsonl`（一行一条：schema_version / mode / session_id / check_id /
  config_id / frame_id / recorded_at / result_age_s（EXE 接收时基）/ created_at（原始服务端
  时间戳）/ target_count / targets / verdict 预留 / screenshot）+ `screenshots/` 逐条 PNG
  （记录时的含框画面）。**MOCK 记录截图带 `mock_` 前缀且 mode=MOCK——不得用作板上识别证据**
  （plan.md §3.4）。导出 = 记录目录本身；CSV 导出列 M3 增强。
- **D8 补充（记录资格时间点，2026-10-08 经理解题推演修正）**：手动标记在**报文被采纳**时
  才生效——断联中的手动触发失败后，残留旧报文不得冒充手动轮结果被记入批次档案。
- **D11 异常事件日志**：overlay 状态迁移（no_result/outage/stale/config/offline/ok，含恢复）、
  会话变化、重握手失败 → 同目录 `anomalies.jsonl`（kind/prev/check_id/fails）+ 异常截图
  `screenshots/anomaly_*.png`（MOCK 带前缀）。与批次记录同一导出件。

## 与验收的映射

- M2（10/12）：本单评审冻结 + EXE 轮次级叠加原型（mock 结果联调，明确标注来源）。
- M3（10/20）：真实板端结果叠加；撤框/断联/过期用例测试记录入档；重复画面不增加批次计数。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-10-06 | 首版：D1 拍板（轮次级起步），D2–D6 预填推荐待评审，D7 风险项 | watercopper（EXE 前端） |
| 2026-10-06 | 理解门槛问答通过后：D7 更新为提议定 NC（队长），待 NC 评审确认 |
| 2026-10-06 | 契约收口：D2–D6 watercopper 确认沿用推荐；D7 NC 本人确认接任，plan.md §3.4/§5.3 同步 | watercopper（EXE 前端） |
| 2026-10-06 | D3 增实现注记：EXE 触发间隔须小于年龄窗口（0.5s < 1.0s，启动校验）；取值经 WC 质询修正 | watercopper（EXE 前端） |
| 2026-10-08 | D6 bbox 端点语义对齐：闭区间 → 半开区间 `[x0,x1)×[y0,y1)`（对齐[定位外包需求](outsource/localization-requirements.md) L2，宽=x1-x0）；协议校验、测试与 EXE 画框同步 | watercopper（EXE 前端） |
| 2026-10-08 | 新增 D8–D10 批次记录（手动触发才记录 / 键去重 / JSONL+截图，MOCK 带 `mock_` 标识）；离板实现与测试随 EXE 落地 | watercopper（EXE 前端） |
| 2026-10-08 | D8 补记录资格时间点（采纳点语义，修"断联中手动轮残包冒充记录"）；新增 D11 异常事件日志（anomalies.jsonl + 异常截图） | watercopper（EXE 前端） |
| 2026-10-08 | 实机 flap 修复（WC 人工按键测试暴露）：新鲜度改按 EXE 接收时刻计量（D3 注记）；记录增 created_at 原始时间戳（D10） | watercopper（EXE 前端） |
| 2026-10-09 | B08：D6 标题同步已确认状态；登记 Q01 结果报文未知字段拒绝缺口，不放宽冻结条款、不修改代码 | Codex |
