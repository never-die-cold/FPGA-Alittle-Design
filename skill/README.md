# skill —— 技能包

从大模型协作过程中沉淀的可复用经验，按 AMD 赛道 3.3.5.2 要求组织。

## 评价标准

**可复用性**：一支陌生队伍拿到本目录，能直接用在自己的题目上。每条 Skill 须写明：

- 适用场景
- 使用方法
- 已验证的效果
- 失效条件
- 从哪几条 `report/llm_log/` 记录（哪些失败）中总结得出

## 已收录

| Skill | 用途 | 关联失败记录 |
|:---|:---|:---|
| [`understand-gate/SKILL.md`](understand-gate/SKILL.md) | 入库理解门槛：AI 生成的代码 commit 前必须通过"逐段讲解 + 3 道理解测试题"，看不懂的代码不许入库 | `2026-09-14-understanding-gate.md`（已删，见 `docs/workflow.md` §2）、`2026-09-20-fwd-tb-understanding-gate.md`（理解门槛首轮不过的实例） |
| [`gufa-programming/SKILL.md`](gufa-programming/SKILL.md) | 古法编程（小步交付）：AI 单步 ≤100 行，每步自检 + 讲解 + 出 2–3 题，用户审核通过才走下一步 | 新提炼：`report/llm_log/2026-09-20-fwd-tb-understanding-gate.md`（理解债集中爆发）、`2026-09-15-muldiv-interface-gap.md`（缺口发现太晚）；效果待试点回填 |
| [`bug-fix-playbook/SKILL.md`](bug-fix-playbook/SKILL.md) | 代码修正手册：先分清功能坏/反馈坏；弱测试巡检（内容断言）；负例先行（FAIL→修→PASS）；时间戳三问（本地观测时基）；资格标记放采纳点；恢复路径自检；自愈条件显式化 | `2026-10-08-exe-rounds-states.md`、`2026-10-08-exe-result-age-flap.md`、`2026-10-08-exe-manual-round-adopt-point.md`、`2026-10-08-exe-rec-counter.md`、`2026-10-08-exe-anomaly-events.md`、`2026-10-10-q01-result-fields.md` |
| [`big-rewrite-playbook/SKILL.md`](big-rewrite-playbook/SKILL.md) | 大规模重做手册：性价比子集决策（含不做清单）；可复现出图脚本评审；冻结设计后重写；兼容式演进（并行 profile 不破旧验证）；基准先行（估算会翻车）；测试连带扫雷；资源子集化；DPI/平台适配 | `2026-10-08-exe-ui-redesign.md`、`2026-10-09-exe-hud-implementation.md`、`2026-10-09-exe-hud-v4-implementation.md`、`2026-10-09-exe-export-cjk.md`、`2026-10-06-vision-sync-protocol-decision.md` |

## 规划方向

1. 通用 PYNQ Overlay 加载、校验与寄存器映射使用范式（素材未齐）
2. RISC-V 核仿真—上板一致性验证踩坑清单（素材齐，待成稿；部分已入 `bug-fix-playbook`）
3. 黄金参考比对与性能/资源数据自动采集脚本（素材齐，待成稿；部分已入 `big-rewrite-playbook`）
4. "根据综合报告定位时序瓶颈"的提示词工作流（素材全在 `2026-10-06-rtl-*` 系列 + `2026-10-07-partC-*`，待成稿）

## 原料来源

每周从 `report/llm_log/` 中 `#skill候选` 标签的条目提炼，期末成稿。

> 状态：🚧 持续积累中
