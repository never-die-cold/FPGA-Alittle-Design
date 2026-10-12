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
| [`pynq-z2-bringup/SKILL.md`](pynq-z2-bringup/SKILL.md) | **通用 PYNQ 板级踩坑清单**（不绑题目，换题换板可用）：XDC 只认官方 SHA256 溯源；JTAG 按 PART 选器件；125MHz 经 MMCM 分频 + locked 门控复位；视频硬限制先查官方文档（720p/无 HDCP/无 USB 主机）；下载工具默认档=安全档、激进档显式 opt-in；Vivado GUI 仿真三坑；共用板报备与阻塞解除同步 | `2026-09-20-pynq-z2-smoke.md`、`2026-09-20-pynq-jtag-bringup.md`、`2026-09-23-partA-soc-onboard.md`、`2026-09-20-demo-hardware-chain.md`、`2026-10-05-rtl-pynq-z2-dual-clock.md`、`2026-09-26-partA-soc-onboard-verify.md`、`2026-10-09-soc-download-collaboration.md` |
| [`timing-closure-workflow/SKILL.md`](timing-closure-workflow/SKILL.md) | 时序收敛与 Fmax 口径工作流：实测 WNS+worst path 驱动的 P0–P5 流程、六种降深度手法、Fmax 约束递减收敛法、通过点/失败点/外推三档口径（外推不得当基线）、跨人复测交接模板（被测代码必须先入 git） | `2026-10-06-partC-pc-depth.md`、`2026-10-06-rtl-*`（6 篇降深度）、`2026-10-05-partB-v1-onboard-verify.md`、`2026-10-06-partB-t2-fmax-verify.md`、`2026-10-07-partC-postopt-board.md`、`2026-10-07-module1-closure.md` |
| [`sim-board-consistency/SKILL.md`](sim-board-consistency/SKILL.md) | 仿真-上板一致性踩坑清单：唯一退休点口径与闭合校验、终止窗口竞态、官方基准隐含规则写成显式禁令（CoreMark 10s/max_cycles）、CRC 对≠参数档对（配置回读联合判据）、跨工具宽容度假象（iverilog vs xvlog -sv）、BRAM 推断只在顶层真实参数暴露、中断回归不拼接、历史 FAIL 不倒填 | `2026-10-05-partB-v1-cpi.md`、`2026-10-06-partC-verify.md`、`2026-09-23-coremark-*.md`（3 篇）、`2026-09-21-partA-decode-and-muldiv-tb.md`、`2026-10-01-vision-m2-sprint.md`、`2026-10-07-module1-closure.md`、`2026-10-09-module1-2-closeout.md` |
| [`dataset-leak-audit/SKILL.md`](dataset-leak-audit/SKILL.md) | 数据集防泄漏审计（校验脚本型，配仓库内可改编脚本）：会话+实物双维划分、文件字节/解码像素双哈希四层泄漏检查、哈希清单与 Git 换行陷阱、"结构 PASS ≠ 数据齐全 ≠ 来源可信"分层声明 | `2026-10-10-dataset-audit.md`、`2026-10-10-fastener-handoff.md`、`2026-10-03-data-collection-protocol.md` |
| [`contract-freeze-workflow/SKILL.md`](contract-freeze-workflow/SKILL.md) | 契约冻结工作流：冻结前枚举全部用例核对编码空间（muldiv 3 位装不下 RV32M 实例）；差集式双层白名单校验器；负例对旧代码 FAIL 留证→正负例矩阵；缺口只登记不放宽；契约变更三处同步（固件/仿真/RTL） | `2026-09-15-muldiv-interface-gap.md`、`2026-09-22-memory-contract.md`、`2026-10-10-q01-result-fields.md`、`2026-10-08-exe-batch-records.md`、`2026-10-10-offline-inspection.md` |

## 规划方向

1. 通用 PYNQ Overlay 加载、校验与寄存器映射使用范式（素材未齐）
2. 黄金参考比对与性能/资源数据自动采集脚本（素材齐，待成稿；部分已入 `big-rewrite-playbook`、`sim-board-consistency`）
3. 离板替身开发闭环（替身分层/幂等回放/原子落盘/来源互斥/黄金参考容差方法；素材见 `2026-10-10-offline-inspection.md`、`2026-10-10-model-reference.md`，待成稿）
4. 多会话/多分支协作与收口（WIP 指纹转移、exit 143 不拼 PASS、默认档规则的实施案例；素材见 `2026-10-09-*-collaboration.md` 系列，部分已入 `pynq-z2-bringup`/`sim-board-consistency`）
5. 回填现有 skill 小增量：`gufa-programming`（讲解过深换生活类比、双工具补讲、记录错误方向）、`bug-fix-playbook`（DUT 错 vs 测试期望错、证伪也留痕、幂等验收条款的结构性保证）

## 原料来源

每周从 `report/llm_log/` 中 `#skill候选` 标签的条目提炼，期末成稿。2026-10-11 全量 113 条记录三段精读过一轮，按官方 3.3.5.2 四类形态成稿 5 项（本轮新增）；剩余方向见上。

> 状态：🚧 持续积累中
