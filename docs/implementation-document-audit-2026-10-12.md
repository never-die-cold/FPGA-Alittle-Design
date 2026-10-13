# 当前实现与文档核对

2026-10-12；核对已合并基线 `3e2e1c9`，并单独标明本工作区尚未提交的 NC 离板改动。
本文供续工与交接使用：状态依据源码、冻结契约和原始证据，不以目标或日期替代实现。
主计划见[plan.md](../plan.md)，执行分工见[三人清单](project-closeout-three-person-checklist.md)。

## 已修正的不一致

| 项目 | 旧文档问题 | 核实后的事实与依据 |
| --- | --- | --- |
| 视觉回归 | 当前仍写23个RTL tb | [Icarus入口](../sim/scripts/run_vision_iverilog.sh)与[XSim入口](../sim/scripts/run_vision_xsim.sh)均含25个，包括2个捕获tb；[整合结果](../data/logs/2026-10-12-pr-review/README.md)通过。旧23项日志不改写 |
| Python回归 | 混用8/10/13组为当前数量 | 合并时13组视觉+3组协处理器；工作区新增构建输入审计后[视觉入口](../sim/scripts/run_vision_python.sh)14组，[离板结果](../data/logs/2026-10-12-nc-offline/README.md)通过。14组尚未提交，不冒充已合入 |
| C02/C03 | 算子/接口未冻结、自定义指令首版 | JL已冻结[C02](../src/coprocessor/design_v0.md)/[C03](coprocessor-integration-v0.md)：64×64灰度FastenerCNN，MMIO/AXI4-Lite控制+DMA，v0不启用自定义指令；实际接口仍未接入 |
| CNN目录/黄金 | 只有README、整数黄金全未实现 | [标量参考](../src/coprocessor/int8_reference.py)、[张量/卷积参考](../src/coprocessor/int8_tensor_reference.py)已有且3组回归通过；整网算子链/正式模型包/RTL未实现 |
| ROI路径 | 整帧224×224灰度快照直接喂首网 | 已有cop_buf快照是分析/诊断接口。C03要求PS从原图定位/裁剪并量化逐目标ROI，再DMA送CNN；安全原图获取未验收 |
| 服务/来源 | 只有MOCK、PROTOTYPE未实现 | [FILE/LIVE服务](../src/pynq_host/vision_live_service.py)及合成LIVE替身已有；FILE每轮复制文件、prototype恒true，EXE徽标已实现。真实HDMI/DDR/MMIO/CNN后端缺失 |
| EXE/记录 | 没有工单/批次/导出；所有截图不能作硬件证据 | LIVE类别/分数/工单横幅、手动有效轮记录、schema v2与CSV已有。MOCK/PROTOTYPE不算硬件证据；真实LIVE仍须原帧/版本/实测证明，不由无前缀文件名代签 |
| Q01/D3 | 白名单修复未提交；年龄使用created_at | Q01已随PR #67合并；v1.2继续严格白名单。EXE按本地接收后年龄撤框，created_at仅诊断与留档，见[rounds.py](../src/vision_client/rounds.py) |
| C01状态 | 源码未提交、最新诊断仍失败 | 源码随PR #69合并；23:15[显示/状态诊断PASS](../data/logs/2026-10-11-c01-probe-evidence/README.md)已解释halted期间dummy-ready/stream_seq增长。DDR完整BGR/槽所有权仍未验收 |
| 位流溯源 | 原vision与C01的缺口混用 | 原vision的bit/hwh与XSA配对但缺构建源码锚定；C01已有98项输入清单与构建日志，[恢复包](../data/evidence/2026-10-12-c01-exact-build-inputs/README.md)严格复核98/98。输入完整性不独立证明bit来自当前源码 |
| 分工 | 仍分配NC训练、WC上板 | 当前NC全部上板/采集/实测，JL训练/量化/RTL/固件，WC数据/PS软件/EXE/材料。D7的NC实机服务责任与W04/W05的WC软件实现职责分别说明 |

## 不能由现有实现推导的能力

`vision_live_service.State.check()`每次HTTP调用递增check_id，trigger_ref只回显，尚无请求重试幂等。FILE_REPLAY按request_id复用产物是另一条路径，不能替它代签。

`BatchRecords.keys`是进程内集合，启动时未从旧records.jsonl恢复。当前同进程session/check去重已有；跨进程复用同一记录目录的持久去重不应视为已实现。服务重启新session降低碰撞机会，但不补齐这项能力。

FILE服务`/v1/config`只推进软件config_id；工单由启动参数提供，HTTP尚未接工单编辑与真实R12确认。C04中的配置链和检查快照查看是设计要求，不能全写成已落码。

冻结的16目标硬件/协议能力与10件业务策略不等同。当前FILE服务默认max-targets=16、文件规则也允许参数化上限；实际C04映射/业务限额仍待一致评审，冻结契约不自动改变软件默认值。

UVC正常、stream_seq增长、软件锁和单独的VDMA halted都不能授权复制DDR槽。必须证明完整帧写完、写事务排干、复制窗口不被重用并同步缓存；[所有权文档](c01-ddr-frame-ownership-v0.md)仍是候选。

## 保留的历史与待办

历史llm_log、旧resume/三日计划、外包原文、原始日志与7幅历史配图保持原样。C01过程中早期失败/恢复未确认与后续PASS均保留，正文入口明确最新状态，避免反复执行旧恢复步骤。

M2仍缺首网硬件输出。未实现/未验收：正式数据/INT8模型/整网黄金、CNN RTL、核应用MMIO/工业固件、custom DDR安全取帧、硬件LIVE、完整N02/N03/N04/N05和工业/发布验收。C04未决项不因本次文档修改自动冻结。

核对复现与原始结果见[本轮检查记录](../data/logs/2026-10-12-document-audit/README.md)。本轮仅修正文档与保留核对证据，未修改生产源码、接口字段或位流。
