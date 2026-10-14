# NC 返场执行单与待确认项（2026-10-12）

依据[三人收尾清单](project-closeout-three-person-checklist.md)，基线 `dev/model@3e2e1c9`；本次离板续工。
用户已报告硬件连接完成；本轮未重新读取板端状态、加载位流或打开串口/UVC。
本轮新增文件与原始输出见[证据](../data/logs/2026-10-12-unattended-offline/README.md)。原有暂存与未暂存改动保留。
2026-10-14续核：最终custom单帧驱动已离板验证，精确版本/返板步骤见[执行单](n03-custom-return-runbook-2026-10-14.md)；C04的Q1/Q3和Q5的NC原则已本人确认，Q5交JL对齐、修复后再验收。

## 1. 回来后按这个顺序执行

| 顺序 | NC 动作 | 必须留下的结果 / 进入下一项的条件 |
| --- | --- | --- |
| 1 / N01 | 只读核查 boot_id、PL 路径、bit/hwh 哈希、连接图与真实输入模式 | 确认实际运行版本；电脑上的候选哈希不能代替板端版本 |
| 2 / N02 | 原 vision 冒烟与 UVC 内容核对，然后逐例长测、软件断源恢复、Overlay 重载和冷启动 | 每例独立日志、前后 boot_id、状态和画面；物理拔插用例由 NC 在场执行，保留异常重启历史 |
| 3 / C01 | 按[既有实现基线](c01-capture-implementation-baseline.md)验证候选显示/状态 | 显示/状态通过仅作诊断；不把 stream_seq 或 Halted 当 DDR 写完 |
| 4 / N03 | 选择 base 诊断；custom 须先收到 WC 所有权适配及 JL 兼容确认 | base 与 custom 整片位流互斥；记录完整 BGR、副本、释放和恢复，不能混填后端 |
| 5 / N04 | 尺标、五档距离、背景/光照与间距定标 | 原帧及实际 mm/px、最小零件像素尺寸、曝光/对焦设置；实测后再选支持条件 |
| 6 / N05 | 交第一个已定标会话的原 PNG、采集表与实物对照表 | 先交 WC 标注/ROI，再交 JL 训练；独立 test 会话/实物不得用于调参 |

完整记录字段沿用[离板准备 §3](nc-offline-readiness-2026-10-12.md)；N02/N03 未通过前，不签正式取帧/工业验收。

## 2. C04 待确认清单（本轮仅审查，不代签冻结）

| 项目 | 已核对事实 | 下次交接须给出的决定或实现 |
| --- | --- | --- |
| Q1 软件帧号 | FILE 后端 seq 每次捕获递增，frame_id 使用该 seq；文件轮换仍为 PROTOTYPE | NC 确认软件序号语义；真实后端每轮新取帧及独立副本必须另验 |
| Q3 权威快照 | 服务保存 capture/packet 与逐轮目录；EXE 有 FILE_REPLAY，真实 LIVE 快照查看未实现 | WC 给出 session/check 对应的快照读取与哈希核对方案，由 NC 确认 |
| Q4 来源统计 | NC 已确认分组原则，JL 一致性确认仍待完成 | JL 确认 LIVE / prototype / MOCK / FILE 分组；材料与导出不能混计 |
| Q5 数量边界 | C03 为 16 目标能力 / 10 件策略；FILE 服务默认 max-targets=16 | WC/JL 对齐业务上限、超限 RECHECK、部分计数标识与 CSV/界面口径；NC 验收 |
| Q6 判定来源 | 当前 FILE/PS 软件判定，核工业固件未实现 | JL 给出迁移到 RISC-V 的实现和同输入对拍入口 |
| 请求重试 | State.check 每次递增 check_id，trigger_ref 仅回显；latest 复用不等于 POST 幂等 | WC 明确重试键、冲突行为与失败重试；新增协议字段另走版本评审 |
| 重启去重 | BatchRecords.keys 仅在进程内，未从旧 records.jsonl 重建 | WC 给出重启后同键不重复记录的实现与仓库负例 |
| 配置回执 | /v1/config 只接受 control 并推进软件 config_id；工单来自启动参数 | WC/JL 接通当轮工单内容与真实硬件配置确认，不能把软件编号当 R12 回执 |

源码依据：[服务](../src/pynq_host/vision_live_service.py)、[记录](../src/vision_client/records.py)、[前端](../src/vision_client/preview.py)。
既有 Q2 及 NC 已确认部分保持有效；以上未决项不由离板回归 PASS 自动闭环。

## 3. 采集口径同步结果与实测边界

2026-10-12 续步已同步规程、交接包和 CSV 模板；[续步证据](../data/logs/2026-10-12-collection-readiness/README.md)另存，上一轮审查证据不改写。

1. [采集规程](fastener-data-collection-protocol.md)已引用 C02 的 64×64 冻结尺寸；≥128px、≥600帧等仍为建议/待实测值。
2. 会话目录编码统一为小写 `l0..l3`，`light` 列保持大写 `L0..L3`，与现有审计器一致；既有原帧/目录不改名。
3. 规程已同步 NC 采集、WC 标注/定位/ROI、JL 训练/量化分工。
4. [CSV 示例](fastener-collection-log-template.csv)已补齐 washer-a；示例仍不是实测记录。正式会话列全实际实物并预留 test 专用个体。
5. base诊断/采集与custom集成验收分别记录；custom单帧适配已有离板异常验证，完整安全取帧仍未实机验收。
6. 工具只提供类别缺口摘要；逐格数量、朝向、GT/标签与真实支持条件仍须人工复核，W01/N04/N05 不因文档同步自动通过。

## 4. 保持未实现 / 未验收

未实现：正式INT8模型/生产黄金、CNN实体缓存/MMIO/DMA集成、核工业固件、真实硬件LIVE后端、请求幂等/持久去重/真实LIVE快照查看。DDR单帧适配及CNN算子/整网控制器/诊断黄金已于10/13实现并离板验证。
未完整验收：N02/N03、N04/N05 真实工位数据、C04 整体、M2 首网硬件输出、工业闭环与目标环境发布。
