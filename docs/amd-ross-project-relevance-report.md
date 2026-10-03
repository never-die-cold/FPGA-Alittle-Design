# AMD ROSS 与赛事资源对本项目的关联研究报告

面向紧固件识别与工业检查系统的工具采用和材料建设

> 2026 年 10 月 3 日 | codex/vision-offboard  ·  a2c29d8

> 状态与结论以上述研究快照为准，不代表后续最新项目进度。

## 1. 研究结论与通知对应关系

这些通知与本项目关联最直接的是核与视觉链路验证、Skill 技能包和最终设计报告。Radeon 云算力可支持模块三的模型训练；本地智能体赛道的群和参考仓库属于另一种参赛交付，不能直接套用到我们的自主选题作品。

本项目为 AMD 自主选题赛道初级组作品，目标是自研 RISC-V 调度、HDMI 视觉预处理、CNN 协处理器和 Windows EXE 组成的紧固件识别与工业检查系统。本报告按这一工程目标评估资源，优先保留既有 RTL 架构和验收入口。项目依据见末尾仓库资料索引。

| 通知或资源 | 对应项目部分 | 具体用途 | 关联程度 |
| --- | --- | --- | --- |
| ROSS 与 Vivado MCP | 模块一与模块二验证 | 执行 Tcl、读取报告、辅助仿真和实现排障 [1](https://www.amd.com/en/products/software/ross-agentic-ai.html) [4](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/vivado-mcp.md) | 直接 |
| 官方 Skills | skill/ 与工程流程 | 借鉴执行步骤、判据、证据格式和失败处理 [2](https://github.com/Xilinx/ross-ai-assistant) | 直接 |
| 报告体现 MCP 提效 | M4 报告与 llm_log | 形成真实工具调用案例和可复现对照 | 直接 |
| AMD 文档知识库 | 三模块设计与调试 | 查证工具命令、IP 和约束说明 [10](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/local-kb/README.md) | 辅助 |
| Radeon GPU 云算力 | 模块三训练与量化 | 训练正式紧固件模型并生成黄金参考 [13](https://amd-aim.github.io/radeon-cloud-docs/introduction/) | 条件相关 |
| 本地智能体参考仓库 | 独立智能体赛道 | 借鉴自测与工具轨迹组织；不改变本项目交付 [15](https://gitee.com/Vickyiii/hlsagent2026) | 参考 |
| 培训 群与昵称通知 | 团队学习与赛事管理 | 准备培训问题；按报名赛道确认进群与昵称 | 管理 |

### 建议采用的范围

先做一个 ROSS 辅助验证案例，再把已解决的工程问题提炼成 Skill，并把证据纳入报告。云训练按数据和模型需求启动。暂不因这些通知改为 HLS 主线，也不把交付目标改为自动生成硬件代码的智能体。以上为本报告的工程建议，不是赛事新增的技术要求。

## 2. 官方能力与环境条件

### ROSS 的组成和执行方式

ROSS 将 AMD 工具 MCP、文档知识库、工程 Skills 和参考设计组合起来。MCP 是智能体连接工具的接口；Skill 是描述具体工程任务如何执行的说明。Vivado 路径为智能体经 MCP 调用 Tcl，再由 Vivado 返回执行结果。它主要减少工具操作和诊断信息传递的成本，功能正确性仍需测试台和实际硬件证据。[1](https://www.amd.com/en/products/software/ross-agentic-ai.html) [3](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/README.md) [4](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/vivado-mcp.md)

官方独立 MCP 可启动或连接 Vivado、执行命令、读取日志和查询历史。文档搜索在当前工具参考中被列为独立 amd-doc-search 服务。Windows 并不具备清单中所有工具：vivado_display、vivado_lsf 和 vivado_ssh 为 Linux 专用，实际暴露的工具以运行时清单为准。[5](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/reference/vivado-mcp-tools.md)

### 版本口径需要分层理解

| 来源 | 当前说明 | 本项目判断 |
| --- | --- | --- |
| 群公告 | Vivado 2025.2 及后续 2026.1；10 月 1 日发布 | 作为培训通知 |
| 产品页与仓库 FAQ | 产品页称 Vivado 全版本；仓库 FAQ 写 2020.2 起；HLS 产品页写 2025.2 起 [1](https://www.amd.com/en/products/software/ross-agentic-ai.html) [3](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/README.md) | 宣传与 FAQ 有差异 |
| 安装指南与单项 Skill | 2026.1 为测试基线；RTL 仿真验证过 2025.2/2026.1；时序与 ILA Skill 要求 2026.1+ [3](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/README.md) [6](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-simulate-rtl/SKILL.md) [7](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-timing-methodology-checks/SKILL.md) [8](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/hw-ila-debug/SKILL.md) | 沿用现有 2026.1 |

因此，“架构上兼容”不能替代具体功能的实测。我们已有 Vivado 2026.1 使用记录，无需为试用 ROSS 切换版本；还需核验 MCP 下载包、客户端加载、工具许可和实际任务是否可运行。Skills CHANGELOG 的初始同步版本为 2026.9.1，日期为 9 月 30 日；群公告的发布时间为 10 月 1 日，两者应分别记录。[16](https://github.com/Xilinx/ross-ai-assistant/blob/main/CHANGELOG.md)

### 安装路线与知识库选择

IDE 路线安装包含 MCP 的 VSIX；CLI 路线安装独立 MCP 二进制，两者择一。官方仓库的技能插件仍需单独的工具连接，且应避免同时用插件和复制方式重复加载 Skills。下载入口需 AMD 账号，支持 Windows 和 Linux。[2](https://github.com/Xilinx/ross-ai-assistant) [4](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/vivado-mcp.md) [17](https://www.amd.com/en/support/downloads/ross-agentic-ai.html)

本地知识库只保证检索层可离线；若回答模型仍在云端，整个流程并非断网运行。建议先使用满足现有环境的文档查询方式，只有明确需要离线复现时再建设本地数据库和本地回答模型。[10](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/local-kb/README.md)

## 3. 模块一与模块二的使用场景

### 模块一 核集成验证和时序分析

当前 v0 核已有验收证据，forwarding、hazard、id_ex_stage、mem_wb_stage 有独立验证记录；完整 v1 核尚未接入验收。ROSS 最合适的切入点是配合既有 tb 复验集成行为、归类 XSim 错误，以及读取实现报告，不能凭独立模块 PASS 宣称三级核已完成。

官方 vivado-simulate-rtl 强调按显式契约验证行为，编译成功和正常退出不等于功能正确。应用到我们的核，应保留 RV32IM、load-use、转发、冲刷和多拍乘除法判据；MCP 负责工具执行与诊断，回归结果仍以仓库脚本及自检 tb 为依据。[6](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-simulate-rtl/SKILL.md)

vivado-rtl-lint 可用来发现未驱动信号、锁存器和算术位宽问题；它只能报告真实 lint 输出。时序方法学 Skill 可对规则分类、追溯约束并在修复后复查。核性能对比仍必须使用相同器件、版本、程序和约束口径，不能用改变时钟目标来冒充 RTL 提速。[7](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-timing-methodology-checks/SKILL.md) [9](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-rtl-lint/SKILL.md)

### 模块二 多时钟和 HDMI 上板调试

视觉链路已有 22 个仓库内 tb 的离板验证记录、原子配置 CDC、彩色直通分流和实现证据。物理 HDMI bit/XSA 已产出，但相机锁定、采集卡闭环和实机延迟仍待验证。因此，ROSS 对模块二的价值集中在约束审查、硬件问题定位和证据整理。

可先对已有 checkpoint 运行方法学检查，核对像素域与 AXI 域的时钟、同步器及稳定总线约束。当前 config_bridge 采用请求/确认握手；任何建议都必须符合该契约，不能仅通过宽泛的异步时钟例外消除报告而掩盖配置一致性问题。[7](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-timing-methodology-checks/SKILL.md)

若上板出现锁定失败、黑屏或配置不生效，可考虑 hw-ila-debug：发现 ILA、设置触发、采集并导出 CSV/VCD。前提是位流包含所需 ILA、能连接硬件，且 Vivado 与 hw_server 版本匹配。PYNQ-Z2 应使用 Vivado MCP 路径；官方 chipscope-mcp 路径限 Versal。[8](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/hw-ila-debug/SKILL.md)

### 首个案例建议

先打开现有视觉 checkpoint，生成方法学报告并与现有 Tcl 流程的输出核对，记录实际发现及未解决项。这一案例范围较小，可验证工具连接和报告读取能力。新增 ILA 会影响资源和布线，宜在出现具体上板问题后单独评估，不把它作为试用 ROSS 的必做项。

## 4. 模型训练 前端与赛道边界

### 模块三 云算力用于训练侧

Radeon Cloud 提供 GPU 实例，通过 JupyterLab 或 SSH 使用，运行 ROCm 生态；它还提供模型 API。对我们最直接的用途是训练正式紧固件分类 CNN、开展量化实验并生成黄金参考。模型 API 主要服务大模型调用，不能代替这个训练任务。[13](https://amd-aim.github.io/radeon-cloud-docs/introduction/)

项目已有合成数据上的 CPU 训练与 INT8 导出演练，但正式相机数据、正式紧固件模型和 CNN 协处理器尚未完成。云训练应输出与硬件匹配的网络结构、INT8 权重、scale/zero-point、hex 排布和逐层激活参考。优先跑通小批量训练与导出，再扩大实验；ROCm、PyTorch 和量化库组合是否适用，需在实际实例验证。

群通知的免费体验申请入口属于活动渠道，实际资格和额度以申请结果为准。平台 GPU 实例消耗 credits，共享模型 API 的额度与其分开；需要保留训练文件时使用持久存储，并在完成后停止或销毁实例。云资源不会自动完成 MAC、缓存、调度和结果接口 RTL。[13](https://amd-aim.github.io/radeon-cloud-docs/introduction/) [14](https://amd-aim.github.io/radeon-cloud-docs/guides/credits/)

### HLS 和 Vitis AI 只作条件参考

hls-run-flow 覆盖 csim、csynth、cosim 和实现，主要经 v++ 或 vitis-run 执行，不能把使用 HLS Skill 等同于使用 MCP。我们当前采用自研 RTL 协处理器，HLS 流程只有在明确安排独立算子原型或对照实验时才有直接用途。[11](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/hls-run-flow/SKILL.md)

官方 Vitis AI 工作流面向 AMD NPU 的量化、编译配置和自定义算子。它的量化思路可作方法参考，但不能直接认定其产物适配 PYNQ-Z2 上的自研 INT8 协处理器；本项目仍须按自己的算子、数值和权重存储契约部署。[12](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/vitis-ai/index.md)

### PS 服务和 Windows EXE 的关联较弱

这些通知没有直接提供紧固件定位、工单检查、视频与结果同步或 EXE 界面实现。ROSS 可帮助查证 IP 和工具操作，产品层仍需实现板端定位、逐目标裁剪、检查规则和通信。现有 MOCK 服务及前端原型只能用于接口联调，不能算真实识别验收。

### 本地智能体赛道是另一种交付

HLS 参考仓库要求提交模型、推理栈、智能体、技能包和裸跑基线，并在断网环境以本地开源权重运行，具有单卡 32 GB 约束。这些要求适用于其智能体赛道，不是我们自主选题作品新增的交付要求。可借鉴其工具轨迹和失败分析组织，不将其器件、评分及提交结构移植成本项目约束。[15](https://gitee.com/Vickyiii/hlsagent2026)

## 5. 技能包建设和报告证据

### 从流程 Skill 补充到工程 Skill

仓库已收录 gufa-programming 和 understand-gate，主要控制开发节奏和理解门槛。官方工程 Skills 则把任务触发、前置条件、具体命令、报告解析、问题处理和复查组织在一起。我们的改进方向是保留现有规则，补充能直接解决 FPGA 工程问题的技能，而非复制官方全文。[2](https://github.com/Xilinx/ross-ai-assistant) [7](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-timing-methodology-checks/SKILL.md) [9](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-rtl-lint/SKILL.md)

| 候选工程技能 | 本项目已有原料 | 需要补充的可复用交付 |
| --- | --- | --- |
| 跨时钟配置一致性检查 | config_bridge 契约、异步 tb、CDC 约束 | 输入条件、握手检查、复位/忙态测试、失败解释 |
| 仿真失败门禁 | 退出码、PASS 判据与失败文本联合检查 | 明确成功条件、失败注入、自测入口、适用模拟器 |
| bit 和 XSA 导出排障 | impl_1 位流关联及 XSA 导出修复记录 | 工程状态检查、修复步骤、产物内容核验 |
| 按报告定位时序问题 | scaler 切拍与实现报告 | 同约束复测、最差路径归因、修改后的功能回归 |

建议每个技能写清适用场景、工具版本、输入输出、操作步骤、验收判据、失败分支、证据位置和失效条件；逐项链接真实失败记录。新技能的可复用效果必须由实际复验补充，尚未试用的部分应标为建议或待验证。复用官方代码时保留相应版权和许可证说明。

### 报告中怎样证明使用了官方 MCP

采用案例应包含问题、基线、官方 Skill/工具版本、真实调用记录、原始输出、采取的修改、复验和剩余问题。此前通过 shell 执行 Vivado 的记录证明脚本自动化，不自动证明使用过官方 MCP。当前没有 ROSS 实际接入证据，因此应先写试用方案，完成后再记录实测结果。

建议归档到 data/logs/ 的命令、工具响应和原始报告，以及 data/evidence/ 的波形或硬件观察；在 report/llm_log/ 解释智能体如何根据证据修正判断。所有记录关联 commit、器件、工具版本、参数、输入和脚本入口。自动修复仍遵守本仓库的小步交付和理解门槛。

### 效率比较采用相同任务

比较现有 Tcl/人工流程与 ROSS 流程时，保持任务、输入、版本和成功判据一致，同时记录总耗时、工具运行时间、人工操作次数和返工原因。若只有一次案例，就报告这一例的观察，不推算普遍提升比例。结果还应说明功能回归、时序和未解决项，不能仅以少敲命令证明设计质量提高。

## 6. 推进顺序和培训准备

建议按既有里程碑推进工具采用：M1 核验收 10 月 4 日、M2 预处理与推理 10 月 12 日、M3 工业闭环 10 月 20 日、M4 材料 10 月 26 日。这些日期来自本项目主计划；ROSS 试用以不挤占验收资源为原则，阶段按交付条件启动。

| 顺序 | 建议任务 | 完成标志 | 责任线 |
| --- | --- | --- | --- |
| 第一步 | 连接 MCP，复验已有视觉报告 | 真实工具可用；输出与现有流程核对 | 验证 |
| 第二步 | 用于明确的仿真或上板问题 | 定位有证据；修复后按原入口复验 | 验证 |
| 第三步 | 在模型需求明确后试用云 GPU | 小批训练、导出和 golden 对齐 | 训练 |
| 第四步 | 提炼工程 Skill 并写入材料 | 陌生输入复验；案例与证据可追溯 | 全员 |

### 10 月 10 日培训应带的问题

群通知安排 10 月 10 日 19:00 线上培训。建议重点确认 Windows 独立 MCP 的下载与连接方式、非工程模式 checkpoint 的支持情况，以及具体 Skills 的最低工具版本。这些问题与我们现有 2026.1 Tcl 构建流程直接相关。

第二组问题是：原始调用和报告怎样导出、长时间综合/实现怎样可靠获取结束状态，以及 PYNQ-Z2 上 ILA 调试有哪些限制。第三组问题是：云 GPU 体验是否对自主选题队伍开放、额度和持久存储条件是什么，以及报告是否存在必须展示 MCP 使用的正式要求。群通知的鼓励采用不能自行解释成新增评分项。

### 研究快照中的事实和待完成工作

已有验证记录：v0 核、v1 独立模块、视觉离板回归与实现、合成数据训练导出演练。已实现待实机验证：物理 HDMI bit/XSA、真实 MMIO 操作和 MOCK 前端接口。未实现或未接入验收：完整 v1 核、分支预测、正式紧固件模型、CNN 协处理器、部署的定位与逐目标裁剪、工业检查闭环。

ROSS 接入、官方 MCP 调用案例和云 GPU 训练在本次研究中均未实施。研究报告提出采用方案，不改变项目完成状态。上述状态来自研究快照的计划、契约和已有日志，本次未重新运行 RTL 回归。

### 赛事管理事项

群通知中的本地智能体 QQ 群 1035286654 对应该赛道；是否加入应按实际报名方向判断。队伍编号加化名的昵称格式属于登记管理。赛事总仓库是规则入口，正式约束和时间仍须以赛方最新公告为准；本文不把 HLS 参考仓库规则作为自主选题验收规则。

- [赛事总仓库 规则应按最新正式公告复核](https://gitee.com/Vickyiii/fpgachina26-amd)

- [RTL 本地智能体参考仓库 仅在相应赛道使用](https://gitee.com/Vickyiii/rtlagent2026)

- [群通知的 AMD 云算力体验申请入口](https://developer.amd.com.cn/login?source=91kadjjnI)

## 7. 来源索引一 官方工具和技能

网页核验日期为 2026 年 10 月 3 日。正文编号对应下列可点击链接；官方 GitHub 内容会持续更新，实际采用时应固定版本或 commit，并再次核验兼容性。正文中的采用顺序和项目适用性为工程判断。

- **[1] [AMD Ross Agentic AI 产品页](https://www.amd.com/en/products/software/ross-agentic-ai.html)**：产品组成、版本 FAQ、许可和 HLS 与 MCP 的关系。

- **[2] [AMD 官方 ROSS 仓库 README](https://github.com/Xilinx/ross-ai-assistant)**：安装选项、技能目录、插件与 MCP 的区分。

- **[3] [Getting Started 与仓库 FAQ](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/README.md)**：2026.1 测试基线和单项兼容性；FAQ 的较早版本说明见下方补充链接。

- [补充链接 仓库 FAQ](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/faq.md)

- **[4] [Vivado MCP 安装与连接指南](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/getting-started/vivado-mcp.md)**：IDE 与独立二进制路线、会话连接。

- **[5] [Vivado MCP 工具参考](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/reference/vivado-mcp-tools.md)**：执行、日志和历史能力，以及 Linux 专用工具限制。

- **[6] [vivado simulate rtl Skill](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-simulate-rtl/SKILL.md)**：按契约仿真、真实工具证据、2025.2/2026.1 验证范围。

- **[7] [vivado timing methodology checks Skill](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-timing-methodology-checks/SKILL.md)**：方法学检查、分类与修复后复查，要求 2026.1+。

- **[8] [hw ila debug Skill](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/hw-ila-debug/SKILL.md)**：ILA 触发采集、导出、硬件前提和服务器版本匹配。

- **[9] [vivado rtl lint Skill](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/vivado-rtl-lint/SKILL.md)**：synth_design -lint、规范解析和真实报告约束。

这些 Skills 在本报告中作为研究对象阅读，未执行其工具工作流；安装官方技能不等于本项目已经通过其验证。

## 8. 来源索引二 云资源与项目依据

- **[10] [AMD 本地知识库说明](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/local-kb/README.md)**：本地检索层与本地或云端回答模型的边界。

- **[11] [hls run flow Skill](https://github.com/Xilinx/ross-ai-assistant/blob/main/skills/hls-run-flow/SKILL.md)**：C 仿真、综合、协同仿真和实现流程。

- **[12] [Vitis AI 工作流说明](https://github.com/Xilinx/ross-ai-assistant/blob/main/docs/vitis-ai/index.md)**：AMD NPU 的量化、编译和算子工作流。

- **[13] [Radeon Cloud 平台介绍](https://amd-aim.github.io/radeon-cloud-docs/introduction/)**：GPU 实例、ROCm、访问方式、模型 API 和持久存储。

- **[14] [Radeon Cloud Credits](https://amd-aim.github.io/radeon-cloud-docs/guides/credits/)**：活动券兑换、实例消耗与模型 API 额度区分。

- **[15] [HLS 本地智能体赛道参考仓库](https://gitee.com/Vickyiii/hlsagent2026)**：仅用于说明 HLS 智能体交付边界，不作为本项目赛道规则。

- **[16] [ROSS Skills CHANGELOG](https://github.com/Xilinx/ross-ai-assistant/blob/main/CHANGELOG.md)**：2026.9.1 初始同步版本及 2026 年 9 月 30 日日期。

- **[17] [ROSS 官方下载入口](https://www.amd.com/en/support/downloads/ross-agentic-ai.html)**：实际安装包与平台选项以登录后的下载内容为准。

### 项目状态依据

仓库快照 a2c29d8，分支 codex/vision-offboard。README.md 用于确认自主选题初级组；plan.md 用于产品边界和里程碑；src/riscv/plan.md、design_v0.md、design_v1.md 用于核状态与验收；src/vision/design_v0.md 用于视觉链路和 CDC 契约；docs/module3-model-training.md 用于训练交付；src/pynq_host/README.md 用于 MOCK 软件边界；skill/README.md 用于已收录技能。

已有证据索引为 report/llm_log/2026-10-02-vision-offboard-closure.md 和 data/logs/2026-10-02-vision-offboard/README.md。研究不以尚未跟踪的上板脚本作为验收依据。
