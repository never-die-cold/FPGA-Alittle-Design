# [2026-10-27] 协作记录：main@cfbded8 状态文档对齐与三态口径统一

> 标签：#coprocessor #docs #状态对齐 #三态 #main
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`89e5249` `8baa519`

## 1. 任务与初始提示词

在 `main@cfbded8`（PR #86–#89 已合并）上对齐协处理器状态文档：把“物理 bank/整机/位流未实现”
等旧表述改为与现 RTL、TB 和整机门禁证据一致；统一“仿真 PASS / 整机综合实现 PASS(40MHz) /
板上 UNVERIFIED”三态口径；保留历史时点，不把 dev/riscv 独有的 A 变体门禁与新包写进 main。

## 2. 模型第一版方案

更新 `src/coprocessor/README.md`、`docs/runbooks/coprocessor-j04-handoff.md`、
`docs/closeout-todo.md`、`docs/contracts/coprocessor-handoff-v0.md`、
`docs/coprocessor-board-clock-runbook.md`：J04b 改为“描述表/结果 DMA/深测/板验收尾”；
Open 台账同步；J07/J08 改三态；af53fe2 等条目加历史时点；板钟 runbook 改为已随
2026-10-26 整机门禁复跑（edge-fix bit `9341F7FA…`、WNS +3.062 ns），但 BOARD 仍 UNVERIFIED。

## 3. 失败现象

1. 旧入口仍写“物理 bank、SoC/综合/位流未实现”，与影子 bank、生产板顶和整机门禁事实冲突。
2. 旧 J04 交接仍写由核写 CLEAR 位清终态，违反 A2 的 PS 独占 CONSUME。
3. 交接索引同页混写“整机未验证”和“旧整机 PASS”，离开日期会误读。
4. 根计划/收尾表仍把已完成项列为下一交付物；板钟 runbook 仍称新源码待重跑。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | README 仍列物理 bank 未实现 | 旧状态未随 RTL 更新 | 改为描述表/结果 DMA/深测/板验 | 与 plan 一致 |
| 2 | 旧 CLEAR/W1C 流程 | 违反 A2 | 标注旧语义/改为 CONSUME | 文档对齐 |
| 3 | 同页混写三态 | 时点未分离 | 当前状态与历史小节分开 | 不再混淆 |
| 4 | 板钟 runbook 过期 | 未跟 2026-10-26 门禁 | 更新为 edge-fix 门禁事实 | BOARD 仍 UNVERIFIED |

## 5. 最终结论

5 个文档完成对齐，当前口径统一为：仿真 PASS；40 MHz 整机综合实现 PASS（含 IMEM 初始化门禁）；
板上 UNVERIFIED。J04b/J07/J08 的剩余缺口改为描述表/结果 DMA/深测/板验、B 视频未综合、
首包待 NC。明确未把 dev/riscv 独有的 A 变体新门禁、新包和 MMCM 状态写进 main。

## 6. 经验沉淀

- 触发条件：稳定的 main 快照与活跃开发线分离，文档仍引用旧实现状态。
- 排查步骤：先以当前权威计划与门禁证据为准；把“当前状态”和“历史时点”分节；
  三态（仿真/综合实现/板上）永远分开写。
- 适用范围：任何 main 快照回填；不要把开发线独有产物混入稳定线。
#skill候选
