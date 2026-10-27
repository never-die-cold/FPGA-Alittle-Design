# CNN 协处理器项目简介

自研核已接入 CNN 协处理器<br>
仿真与 40MHz 整机门禁通过<br>
板验、正式模型和视频仍待完成

这是面向板卡紧固件检查的自研计算子系统：RISC-V 核负责调度，CNN 协处理器负责整数推理，PS 负责装载数据、提交任务和保存结果。READY 只作提示，软件以 ACCEPTED、终态和消费清除完成可靠交接。

当前口径为：仿真 PASS / 整机综合实现 PASS(40MHz) / 板上 UNVERIFIED。A 变体已形成仅含核与协处理器的首包；B 视频变体只有离板接入，尚未完成综合实现或板验。

证据包括：BRAM 模式下 pattern 与 zero 各 73,795 个元素逐项一致；当前唯一有效包的哈希前十二位为 e2eb5bd340f0。初始化门禁也确认固件镜像不是空内容。

仍缺三项关键闭环：板级未验证、正式模型未发布、视频整机未验证。当前模型是 PROVISIONAL 诊断网络，不是发布模型；score_q15 是整数分数，不是概率。

JL 负责归档门禁原始证据并补齐交付缺口。NC 负责在板上核验时钟、固件、装载和结果。WC 负责按现行握手与消费顺序接入软件，并保留独立超时。

## 来源文件

- plan.md
- coprocessor-nc-handoff.md
- coprocessor-build-variants.md
- coprocessor-integration-v0.md
- coprocessor-manifest-v1.md
- coprocessor-imem-init-gate.md
- 2026-10-27-closeout-audit.md
