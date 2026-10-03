# [2026-10-03] 协作记录：Part C 复验准备清单（partC-verify-plan）制定与理解门槛

> 标签：#riscv #验证
> 平台：ZCode ｜ 模型：GLM-5.3-Flash（zai-start-plan）
> 相关 commit：与 `docs/partC-verify-plan.md` 同批提交
> 用途：Part C RTL 交付前的 verify/bench 备货计划；记录契约现状核查结论与理解门槛问答全量存证

## 1. 任务与初始提示词

用户指令要点：产出 `docs/partC-verify-plan.md`，风格完全对照 `docs/partB-verify-plan.md`（角色/交付前置/验收门禁/tb 备货/CPI 口径/XSim 对拍/上板简报/执行清单）；唯一权威 `src/riscv/design_v1.md` Part C 章节 + `src/riscv/plan.md` §4.3；四档 = v0 / v1_nofwd / v1_fwd / v1_fwd+BHT；CPI 降幅基线 = v1 无转发 ≥25%（v0 仅锚点）；BHT 命中率要可统计；125 MHz 非阻塞加分；预写 tb 等 RTL 交付再接入（Part B 教训写进注意事项）；只写文档，不改 RTL 和脚本。

## 2. 产出方案

九节结构对照 partB 版，关键设计：

- 门禁表把 ≥25% 拆成 `gain_fwd`（Part B D14）与 `gain_total`（Part C §4.3）两级公式，BHT 净贡献单独成列（负值即回归，必须定位）；
- 命中率门禁写"计数 vs 波形双源核对"，统计来源（片上 or tb）随契约冻结；
- 第 2 节把"Part B 前置闭合"（v1 两档入 `all` 且复验在案）列为 Part C 开工硬前置——当前看板口径为完整三级核未验收。

## 3. 偏差发现（重要，动手前核查所得）

任务卡称"唯一权威：design_v1.md Part C 章节"。动手前 `git show dev/rtl:src/riscv/design_v1.md` + diff 核查发现：**design_v1.md 全分支（含 dev/rtl，diff 为空）都没有 Part C 专章**——契约只冻结到 Part B（D1–D15，`fe80857`）。

纠偏：文档头部如实标注契约现状；权威组合落地为"plan.md §4.3 目标口径 + design_v1.md 沿用条款（§1.3/§9.4/§14/D10/D15）"；第 4 节 `tb_branch_predict.v` 断言点标"计划稿，契约冻结后回填"，防止预写 tb 变相预支验证结论。

## 4. 理解门槛（3 题问答，全部通过）

| 题 | 用户答案要点 | 判定 |
|:---|:---|:---|
| 1. 为何降幅基线是 v1_nofwd 而非 v0 | 同一三级核对照才能把降幅归因于转发/预测；v0 混入流水级数与架构差异，只作锚点；且 2.105→约 1.6 降幅仅约 24%，不达 25%，更不是规定的基线比较，不能据此验收 | ✅ |
| 2. `tb_branch_predict.v` 现在能否接入 `all` | 不能：DUT 未落地，提前接入会编译失败破坏全量回归；当前断言只是计划稿；正确时机 = `branch_predict.v` 落地的同一交付补齐契约 + 单独模式 + `all` 接入并留 PASS 证据；交付前仅允许对参考模型 stub 自洽检查，不算 RTL 验证 | ✅ |
| 3. L3 降级时 ≥25% 门禁是否还成立 | 成立：BHT 关闭后比较退化为 v1_fwd vs v1_nofwd，仍须按此基线计算；达标也只能如实报告降级配置结果，不得宣称含 BHT 的目标版通过；报告必须写明降级范围与原因、四档缩三档、BHT 关闭/未实现；门槛未达不得写成通过 | ✅ |

## 5. 最终结论

`docs/partC-verify-plan.md`（97 行）入库；Part C 备货与验收口径以文档第 3/5 节为准。验证方式：9 个被引路径存在性核对全 OK；锚点数值与 `data/metrics.csv` 一致（v0 CPI 2.105 / bench v0.1 2.860）；`git diff --check` clean。

## 6. 经验沉淀

- 触发条件：任务卡引用"某文档某章节"作为唯一权威时。
- 排查步骤：动手前先 `git grep`/`git show <branch>:<file>` 核对该章节是否真实存在（含其他分支）；不存在则如实标注，降级为"目标口径 + 相邻权威条款"组合，不得凭记忆补写。
- 适用范围：通用，跨分支协作尤其必要；答辩场景直接相关——引用不存在的契约章节会被当场戳穿。
