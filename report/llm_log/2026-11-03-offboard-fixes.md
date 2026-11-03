# 2026-11-03 协作记录：最终离板审查修复与发布准备

> 标签：#vision #coprocessor #build #bug修复 #工具链
> 平台：Codex desktop；本记录不推测未暴露的具体模型版本。
> 基线：dev/submission-slim @ ffe0769，加已有网页端未提交改动。
> 相关commit：本记录随修复提交归档，可由`git log -- report/llm_log/2026-11-03-offboard-fixes.md`追溯；实际推送回执见会话。

## 1. 任务与初始提示词

用户要求提交前全量检查仓库代码与文档，对问题、不合适和复杂冗余全部上报，继而要求“应该修的修，应该push的push”。用户说明最终技术文档和海报已由队友在其本地完成；本轮不编辑队友成品、不将本地未跟踪LaTeX初稿冒充最终稿。

用户明确选择“快速模式修复，代码提交前保留理解门槛”。据此豁免gufa的逐步停顿与逐步答题，保留understand-gate的讲解、三题、真实回答和通过后才commit。没有把“continue”视作理解题答案。

后续用户最新原话：“不做理解门槛了，还有什么需要修复改动的吗”。本轮据此取消提交前答题要求，用户当前指令优先；保留讲解及原题，不伪造答案、不标记答题通过，不修改仓库长期技能/AGENTS规则。

## 2. 方案与范围

恢复历史原夹具→网页配置恢复→协议校验→教程解码/退出码→健康与容量保护→工具信任边界→现役说明与汇总回归→理解门槛→提交/普通推送。保留现有RTL与冻结历史证据，暂缓网页/驱动大规模重构。

跨默认目录的改动已在会话声明：web_client、pynq_host、sim/vision、sim/tools、sim/scripts，以及根README/plan、build/README、现役说明与data/report证据。没有修改RTL、下载位流、连接板卡或更改板端服务。

## 3. 失败现象与纠错

原审查登记20项问题与7项维护事项，详情和原始命令见`data/logs/2026-11-03-offboard-audit/AUDIT.md`。包含真实复现的配置恢复/trigger_ref边界、教程解码符号与退出码，以及N03夹具缺失、卫生索引失败；不把文档误述算成RTL逻辑失败。

| 轮次 | 反馈 | 判断与修正 | 证据 |
|---|---|---|---|
| 1 | 新教程测试的AST加载器NameError: R | 仅加载函数漏了模块常量；改为加载ASM_CASES前的完整定义，保持黄金不变 | fixes/codec.log保留初次失败，汇总回归复跑 |
| 2 | 同会话配置恢复后旧手动意图可能仍缓存 | 配置变化与会话变化均撤除旧结果和manualRef；不变时保留同次重试标识 | test_web_refresh.mjs含变化/不变两种用例 |
| 3 | 汇总功能全部通过，最终卫生仍报索引过期 | 日志本身持续增加data/logs目录大小；改为先写sim/build，冻结归档后重建索引 | software-regression.log保留失败尝试；最终记录见修复README |
| 4 | 提交前sha256sum将26条路径末尾回车当作文件名 | PowerShell生成的清单为CRLF，data日志保留原字节；将哈希清单规范成LF再核对，全部通过，业务代码未变 | source-check-before/final.log |

## 4. 验证与边界

实际命令、退出码与结果以`data/logs/2026-11-03-offboard-fixes/README.md`及原始日志为准。统一软件入口为`bash sim/scripts/run_offboard.sh software`；首次功能测试通过、卫生因索引过期退出1，保留原记录，不覆盖为PASS。最终从sim/build记录的整条软件汇总退出0、PASS: offboard software，Node18项通过，卫生0错误/10组既有重复告警；归档到software-final.log。暂存git diff --check通过；提交前理解题原为待回答，已由用户最新指令豁免。

原审查的CoreMark四档、arch 11×4和RTL分项结果不变；原all主动中断，不宣称其命令完整PASS。新增run_offboard的all模式尚未整条执行。新服务健康hook、只读配置、多页面、磁盘故障均需实板复验；离板替身不能代替硬件精度/稳定性验收。

## 5. 理解门槛：完整讲解稿

### 网页交付入口与协议

`src/web_client/serve.py`只监听localhost，静态根目录限定为网页目录，只把约定API转发到指定板端；模块MIME使浏览器能加载`protocol.mjs`。断网转502，板端400/503原样传回，页面不会把服务错误当识别成功。它不把USB视频上传到板端。

`protocol.mjs`校验LIVE报文白名单、session/config、无符号编号、尺寸/半开bbox、唯一目标号、类别/分数和判定结构。trigger_ref新增与Python一致的可选null或1–64 Unicode码点字符串限制。target_limit使数量未知，不能把未完整检测的数量显示成可靠计数。报文来自板端不等于其类别一定正确。

### 页面状态与真实数据

`index.html`保留LIVE、LOCAL DEMO、FILE REPLAY三种来源。LIVE消费真实API，LOCAL DEMO为明确标识的合成数据，回放只读既有报文。UVC是本机预览；没有UVC时使用含session/check的板端快照URL，并等图像加载后显示本轮框，避免新框先落在旧图上。预览FPS是浏览器实际呈现统计，不是CNN推理吞吐。

`connectLive`读取status的当前配置号，支持同session下另一客户端改变配置；新服务连接不写配置。旧服务缺少config_id时兼容初次POST配置，非法config_id直接拒绝。会话或配置变化撤旧结果并取消旧manualRef，不变时保留同次手动重试意图。产品服务用启动时已确认的硬件配置号初始化，避免软件初始0冒充硬件实际配置。

`liveBusy`保证同一页面只发一个在途检查/握手，`modeEpoch`表示当前模式代次，切换模式后忽略旧代次的迟到响应。`autoRound`在暂停自动检查时仍约2秒查询健康；长请求期间顺延。心跳不更新识别结果时间戳，所以在线不等于旧结果重新变新。

`liveRound`对仍新鲜的旧结果保持显示，新结果到达后替换；`freshnessLoop`按接收时刻撤除过期结果，不能每次发请求重置其年龄。检查失败撤旧结果并暂停自动检查。自动轮不加批次，只有有效手动轮按(session,check)去重记录；同次网络重试复用trigger_ref，成功后才结束该意图。当前CSV来自本页内存，刷新会清空，持久存储与异常截图尚未实现。

### 板端服务与保护

`vision_live_service.State.check`保持串行捕获→推理→校验→落盘→CONSUME顺序。完成过的trigger_ref回原报文，避免网络重试重新检查；缓存有16条窗口。新轮先检查磁盘余量，再分配check号和捕获，默认256MiB。余量不足返回503且不新取帧，不删除历史证据；单轮仍可能超过剩余空间，写盘OSError同样映射503。失败后的硬件自动恢复并未因此完成。

新增快照读取只允许当前服务session及指定check目录的capture.png。status只读返回config_id，通过可选health查询捕获健康。产品Captures.health读CAP1的lock/pending位；读失败或失锁呈现不健康，不能把进程活着当硬件正常。FILE替身的prototype语义仍保留，捕获健康也不能证明CNN下一轮成功。

### 教程、工具与可复现入口

`verify_rv32i.py`修正21位JAL立即数的符号判断为bit20，失败自检用退出1让调用方识别。新测试用独立机器字与期望有符号文本，避免“错误解码后再编码仍还原”的自证；还注入错误golden验证非零退出。此处是教程工具，不是核RTL。

N03夹具从历史提交恢复原字节并登记SHA，不生成替代证据。exporter用weights_only=True限制checkpoint加载，再验证模型元数据；当前r6实际加载通过。SSH工具加载known_hosts并用RejectPolicy拒绝未知密钥，BOARD_KNOWN_HOSTS可指定可信文件；开发默认账户边界保留说明，本轮没有连接板卡。

`run_offboard.sh`显式补充原all遗漏的网页、检查链、N03、BRAM/watchdog和arch矩阵；software只跑软件集合，all另含RTL长测。XSim/Vivado仍单独验证。文档区分现役共存包的原彩色捕获/PS ROI和原视觉诊断分析链；原审查缺陷探针仅保存修复前事实，修复后由正式测试承担判据。

## 6. 原理解题与用户豁免

1. 如果第二个页面连接仍先POST /v1/config，两个页面可能怎样互相影响？本次从哪里只读取得配置，配置变化时为何要清掉旧结果和旧手动标识？
2. 为什么磁盘余量不足必须在取帧前拒绝？如果写盘中途仍发生OSError，HTTP和页面旧判定应该怎样处理？为什么这里不自动删除历史证据？
3. 如果自动轮也增加REC，或同次手动重试每次更换trigger_ref，会怎样影响批次记录？为什么等待下一轮时不能重置旧结果的接收时间？

用户未作答，随后明确取消理解门槛，原话见§1。状态：本轮已获豁免，按先前修复/推送授权继续；不记为理解测试通过，不由agent代填答案。

## 7. 经验沉淀

索引包含文件大小时，正在增长的原始日志会让索引自我失效；先在仓库内build目录运行，结束后冻结归档再索引。恢复缺失验证夹具应追溯原blob和哈希，不能为了PASS重造数据。多客户端握手应读取状态而不是隐式提交配置。
