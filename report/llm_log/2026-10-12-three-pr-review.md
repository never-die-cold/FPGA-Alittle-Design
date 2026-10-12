# 2026-10-12 三个 PR 审查、理解门槛与分支同步

用户请求：审查当前三个 PR，合并并同步各个分支。

开工分支 dev/model@17e9ec0，工作区干净。完整读取 AGENTS.md、docs/workflow.md、主计划、核计划、v0/v1 契约及古法编程/understand-gate 技能。范围是已有 PR #69/#70/#71 的审查、仓库内回归、单行冲突解决和分支同步，不新增产品功能。

## 设计意图讲解

- C01：capture_stream_monitor 仅观察 TVALID/TREADY 握手；x/y 跟踪完整行帧，seq 只表示几何完整，故障优先于完成。capture_fault_cdc 保持像素域 overflow 请求直到 AXI 域确认，两个方向均两级同步，停钟不清历史。capture_status_axi 在 FCLK0 中保留计数与锁定状态；分离缓存 AW/W，拒绝所有写；读响应在背压时保持。并联捕获与原显示独立，不代表 DDR 帧槽已归 PS。对应捕获状态契约及实现基线。
- W05：FILE 后端每轮复制文件，prototype 恒 true。State 的互斥锁串行化检查/config；check_id、capture 序号和会话标识用于追溯；capture/packet 用 pending+replace 落盘，latest 只返回已完成轮次。默认引擎连接既有 inspection_run，超限保持 RECHECK。它是软件骨架，真实硬件后端未接入。
- W06/W07：live_view 从已校验报文生成判定、工单差额和类别/分数；preview 恒显 PROTOTYPE，失效结果撤框。BatchRecords 只记录被采纳的手动有效轮次，键为 session/check；schema v2 保存 decision、status、prototype 与协议版本；截图前缀跟随来源；CSV 兼容旧记录。对应 D3/D8–D11 与 C04 候选语义，不自动冻结 C04 未决项。
- INT8：标量量化使用 ties-away，饱和范围为 [-127,127]；bias 必须精确落在 INT32，requant 使用 INT64 乘积后舍入/饱和，参数整数值须入 manifest。张量遵循 CHW/OIHW，per-channel weight scale；卷积索引包含 stride/padding，不翻核，从 bias 起逐项累加并拒绝 INT32 溢出。Python PASS 不证明整网、RTL、综合或硬件性能。对应已冻结 C02 §3–§6。
- 合并冲突：仅 run_vision_python.sh 的 for 测试名单冲突。保留 #70 两个 LIVE 测试和 #69 三个捕获/UART 测试，共 13 组；不舍弃任一方测试。只改一行执行代码，集成快照先验证再落到分支。

## 理解题（原文）

合入前请简答三题（也可明确要求本轮快速模式、豁免出题）：① FILE 后端发 LIVE 报文时，为什么仍必须恒显 PROTOTYPE，并用 proto_ 区分截图？② 一次手动检查失败后，为什么不能把上一轮成功结果当作这次结果记录？③ INT8 卷积的 bias+乘加超出 INT32 时，黄金参考应拒绝、回绕还是饱和，为什么？

## 用户答案（全文）

① FILE 后端发 LIVE 报文，为什么仍必须恒显 PROTOTYPE、用 proto_ 区分截图

因为「协议模式」和「数值来源」是两个必须分开声明的维度，标识必须跟着数据走。

协议只有 MOCK / LIVE 两种 mode，而 FILE 后端（目录内 PNG 按序轮换当本轮 capture）走的是正式服务形态——HTTP 轮次、每轮新取帧、发 LIVE 报文，所以 mode 必然是 LIVE。但 LIVE 徽标本身会让人默认「这是板上硬件的实时识别结果」，这个印象不能靠 mode 推导。于是 prototype 布尔专门承担来源声明：由捕获后端结构性决定，FILE 后端恒 true，无开关（sim/build/pr-review/integration/src/pynq_host/vision_live_service.py:7，FileCaptures.prototype = True）；只有真实取帧后端（N03）接入后才允许 false。D6 冻结条款写得很直白：板端服务以离线产物代实时结果时必须置 true，EXE 恒加 PROTOTYPE 标识，"对齐 MOCK 的诚实约束"（docs/vision-sync-protocol-decisions.md D6）。

EXE 侧对应两条落地：顶栏 PROTOTYPE 恒显、不可关闭（C04 §3.2 表中 LIVE+prototype 一行；实现见 src/vision_client/preview.py:131 注释"离线产物代实时结果，恒显不可关闭"）；记录截图前缀 proto_——MOCK=mock_、LIVE+prototype=proto_、真实 LIVE 无前缀（src/vision_client/records.py:28，C04 §5/Q2）。

proto_ 前缀存在的理由是截图会脱离界面流通：发给同学、进报告、当验收材料时，界面上的徽标已经丢了，文件名是随文件走的那一层标识。这样任何人扫一眼截图目录就能分辨哪些不是真机识别证据。下游还有统计口径约束：PROTOTYPE/MOCK/软件基线数据不得并入 LIVE 实机统计（plan §1.4 "目标与实测分开"、C04 §4）。整套机制防的就是"演示时关掉标识、把原型数据冒充工业识别结果"——恒显且无开关，是因为有动机关它的人恰恰是操作者自己。

② 一次手动检查失败后，为什么不能把上一轮成功结果当作这次结果记录

因为记录是证据，必须与真实发生的那一次事件一一对应；借用上一轮结果就是伪造证据链。

一次检查的身份是 (session_id, check_id) + 本轮新 capture + 当轮工单/config，D9 明确以键去重、"一次确认的检查只记一条"，D8 明确结果未到/过期/断联不记录（docs/vision-sync-protocol-decisions.md D8–D10）。上一轮成功结果属于另一个 check_id、另一张 capture、另一个时间点，把它记到本轮名下，W07 要求的每一项可追溯字段（哪个 session/round、用哪张 capture、按哪版工单、什么来源、判定依据）全部对不上。

这不是假想情形，是真实修过的 bug：2026-10-08 发现 last_round_manual 原先在"发动请求"时就标记，于是断联中按 c 触发失败后，显示窗内残留的旧报文会被当成这次手动检查写入批次档案；修复就是把标记移到"报文被采纳"之后（exe-anomalies 日志，D8 采纳点语义）。同类防线还有：D3 撤框（超龄/会话不符/配置不符即清框，杜绝静默旧框）、C04 §2.1 禁止复用上一轮帧（连服务端缓存回放都违规）。

后果链也很硬：失败轮记成成功，复检率/失败率统计失真；批次档案虚增成功记录，工业上就可能按错误记录放行本该 RECHECK 的批次（"不截断放行、不允许错误放行"被破坏）。正确做法是失败轮要么不落记录、要么进 anomalies.jsonl + anomaly_*.png 异常日志（D11），界面照实显示等待/撤框状态——这与 AGENTS.md 红线"不得把未实现说成已完成"是同一原则的记录侧版本。

③ INT8 卷积 bias+乘加超出 INT32，黄金参考应拒绝，不是回绕也不是饱和

结论：拒绝（fail loudly），并在 D2/R12 冻结时将"设计保证不溢出 + 越界拒绝"写死，附最坏界证明。理由分三层：

契约层。黄金参考是冻结整数契约的可执行形式——R5 要求"不得改变冻结黄金参考的整数结果"、R18 要求量化点与 argmax 位精确一致。而"溢出规则"目前是显式待冻结项：R12 要求测试包给出"舍入及溢出规则"，D2 行还写着"硬件乘数/移位、scale 编码未定"（docs/outsource/cop-cnn-requirements.md CNN-R4/R5/R12/R18、§8 D2）。黄金若自行选回绕或饱和，就是实现方替规格发明语义，而冻结顺序恰恰必须是"先拍板规格、后实现黄金"。

语义层。回绕把补码加法器的电路现象固化成算术语义：A 回绕后不再满足 R5 的实数解释 A*s_in*s_w，数字无意义却仍被"算出来"；如果 DUT 也回绕，两边一致地错，验证会静默通过一次真实溢出事故。饱和则是规格外的操作——契约里的饱和只存在于两处：ReLU 在 0 截断、Q() 在 [-127,127] clip；给 INT32 累加器发明一层饱和，DUT 若按典型加法器回绕就是假失配，还会掩盖"累加位宽不够"这个真实设计缺陷。拒绝是唯一不发明语义的选项，也与项目一贯的处理风格一致：bbox 退化/越界拒绝、未知字段拒绝、非有限参数拒绝（docs/module3-prototype-reference.md:65）。

工程层。冻结首网单输出最坏累加 |A| ≤ 127×127×K_max，K_max = 32×3×3 = 288 → 约 4.65×10⁶，相对 INT32 上限 2.147×10⁹ 有约 460 倍余量——溢出在这张网上是可证不可能的。所以正确路线是先把这个界写进契约与算术参考；J02/R17 要求的"溢出、饱和例"（MAC tb 必测"连续累加与 INT32 行为"）用途是钉死这个界和拒绝行为，而不是定义回绕。真正触发溢出的测试向量说明权重/scale/规格有缺陷，应修复上游，而不是给缺陷定义一个合法结果。（若将来 D2 确实书面冻结了某种溢出行为，黄金随之实现——但那是一次规格评审，不是黄金实现者能自选的动作。）

一句话收拢：三问是同一条原则的三个面——依据与数据来源必须跟着数据本身走，越出契约域必须失败而不是被解释（①标识跟数据走、②证据跟事件走、③黄金不发明语义）。①②在 FPGA 工程里已经是现行约定并有落码；③目前无冻结答案，属 D2 待拍板项，上述"拒绝"是按项目原则的推演，最终需委托方书面冻结。

## 判定与校正

三题核心理解通过：正确解释来源标记、有效轮次证据绑定及 INT32 累加溢出拒绝。
第三题的项目状态需校正：当前 C02/C03 已由 JL 于 2026-10-11 定稿，记录见 2026-10-10-coprocessor-g0-contracts.md §8；C02 §3.3 已明确导出器必须证明 bias_q+sum 不溢出，RTL 不得回绕或逐项饱和。用户引用的外包未决清单不能替代此冻结契约。MAC 乘积项上界约 4.65M，完整证明必须另包含 bias；不能只据 MAC 项推导任何合法 INT32 bias 都安全。该校正在合并 #69 前明确反馈给用户。

## 验证与边界

原始输出及精确被审 SHA 见 data/logs/2026-10-12-pr-review/。
本轮 C01 25 个视觉 RTL tb、11 组 Python、Verilog-2001、N03 离板假驱动/生命周期通过；PR70 10组、PR71 3组 Python 通过；合并预演保留双方名单后的13+3组通过。
完整 RTL all 的既有仓库证据 full-regression-exit.txt=0，当前视觉 .v 与 final-inputs 哈希一致，核相对该 PR 基线未改。本轮重复 all 的 nofwd CoreMark 通过后主动停止后续重复计算，不把取消运行说成完整 PASS。
源码/文档差异空白检查通过。PR69 原始日志的完整 diff --check 报 CRLF/尾随空格，保留原字节，未修剪历史证据。本轮日志定向 -text/-whitespace，Markdown 仍检查。

未实现/未接入：CNN RTL/首网硬件输出、C01 DDR帧槽所有权与真实颜色对拍、N03 长测、正式硬件 LIVE 和工业闭环；C04 待确认项保持候选状态。

GitHub protect-main 要求1个批准审查，但当前账号 never-die-cold（id 270969795）在规则集中配置 always bypass。按用户明确合并请求使用普通 merge API、校验预期 head SHA，不改规则、不直接 push main、不使用强推/reset。
