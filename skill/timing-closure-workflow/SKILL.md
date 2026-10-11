---
name: timing-closure-workflow
description: Use when post-route WNS is negative, when asked to "提频/降深度/收敛时序", when reporting Fmax, when handing a timing re-verification to another person, or when quoting any frequency number in docs or reports. 时序收敛与 Fmax 口径工作流：实测 WNS+worst path 输入 → 旧行为黄金参考 → 降深度改写 → 等价回归 → 复测交接；频率宣称只用"约束通过点"，外推值必须带"外推"字样。Trigger on WNS / Fmax / 时序 / 降深度 / 提频 / setup 违例. Not for functional bugs (see bug-fix-playbook) or board bring-up (see pynq-z2-bringup).
---

# 时序收敛与 Fmax 口径工作流（timing-closure-workflow）

一句话规则：**每个频率数字都要能回答"什么口径"——约束通过点、失败点、外推三选一；改时序前先把旧行为锁进等价黄金参考，改完只宣称"待复测"，复测由真实 STA 说话。**

## 工作流（P0–P5，每步输入输出明确）

| 步 | 输入 | 输出 |
|:---|:---|:---|
| P0 | 实测 WNS + worst path（source/destination/逻辑级数/route%） | 契约回写：地址/行为真值表、复测目标、验收判据 |
| P1 | 旧 RTL 现行为 | **用旧公式建等价黄金 tb**（如 768 例 PC/flush 判据逐一断言）——改之前锁行为 |
| P2–P4 | 黄金 tb + 降深度手法（下表） | 每改一块跑等价 tb + 模块 tb + 全量回归；功能等价与性能收益**分别取证** |
| P5 | 全部改动 | source_manifest（起点 HEAD + 逐文件 SHA256；未提交的运行版本不能只写 HEAD） |

**交接提示词模板**（实测驱动，不用形容词）：「实测 <配置> @<周期> WNS=<值>，最差路径 <src>→<dst>（<N> 级、route <x>%）。要求保持 <约束清单>，把这条路径降深度。」——验证线↔RTL 线交接时附复测命令与判据（WNS≥0 的周期即通过点）。

## 六种降深度手法（改数据/选择拓扑，不是改命名）

1. 优先级选择链 → 互斥条件掩码相或（`{32{cond}} & value` 或集），控制与数据分离；
2. 分支比较与 ALU 解耦（独立 eq/lt/ltu 比较器直出 taken）；
3. B 型分支专用立即数旁路；"下一个 PC"用独立加法，别在已选目标上再 +4；
4. flush 只进 valid 位，移出指令数据路径（副作用全靠 valid 门控）；
5. 转发源按物理结构裁剪（唯一在途生产者场景置空旁路源）；
6. 观测/统计逻辑（命中率计数等）外置到 tb 层次化事件线，不占片上资源不污染 Fmax。

## Fmax 实测：约束递减收敛法

单点约束下报告值会漂（实测案例 73.2→82.0→83.8 MHz）。逐轮收紧周期直到 WNS 由正转负，**取过零点**；结论按三档表述：
- **约束通过点**：WNS≥0 的那个约束倒数——唯一可宣称的"工作点"；
- **失败点**：WNS<0 的最近约束（如实记录，附 worst path）；
- **外推**：`1/(周期+|WNS|)`——只能带"外推"字样作参考，**不得写成基线/实测**（本项目曾因 86.8 外推值被 5+ 篇记录当基线引用而全库加审注）。

三个频率域分开表述，互相不可替代：**核 OOC ≠ 完整 SoC 档位 ≠ 板上 PLL 实跑**。

## 踩坑与铁律

- **被测代码必须在 git**：跨人复测前 `git ls-remote` 核对远端 HEAD——照命令直接跑会拿旧代码还冠以新档名。
- 改信号命名/控制结构**不减少逻辑深度**；必须改真实数据路径或选择拓扑。
- RTL 侧改动只写"待 Vivado 复测"，不自行宣称 WNS/Fmax；沙箱/平台中断时**实际退出码优先于文档状态**。
- 优化提交必须重跑功能回归，别默认"只影响时序"；仿真周期数据 ≠ 真机时序。
- 归档失败不丢人：某档位 FAIL 就记 FAIL，不生成不冒用该档产物。

## 已验证效果

- WNS −0.334（17 级路径）→ 降深度后 **+0.538**（12 级），等价 tb 768 例零回归、四档周期逐位一致；
- 交接近年实测复测三档口径（11.52 ns 通过 / 10 ns 失败差 9 ps / 外推仅参考）全程无口径事故；
- Radix-4 乘法器预测 cycles 17,114,141 与实测**完全一致**（先分类记账、后投影、再实测对账）。
- 来源（`report/llm_log/`）：`2026-10-06-partC-pc-depth.md`、`2026-10-06-rtl-core-top-pc-flush-depth.md`、`2026-10-06-rtl-id-ex-stage-branch-compare.md`、`2026-10-06-rtl-id-ex-stage-branch-target.md`、`2026-10-06-rtl-if-stage-valid-only-flush.md`、`2026-10-06-rtl-core-top-forwarding-wiring.md`、`2026-10-06-rtl-branch-predict.md`、`2026-10-05-partB-v1-onboard-verify.md`、`2026-10-06-partB-t2-fmax-verify.md`、`2026-10-07-partC-postopt-board.md`、`2026-10-07-module1-closure.md`、`2026-10-05-partB-fast-multiply-options.md`

## 失效条件

- 目标是资源/面积而非时序——手法表不适用（降深度常增资源）。
- 无 STA 工具可用的场合（纯仿真环境）只能停在"待复测"，不得用仿真周期外推频率。
- 综合策略/器件换代后历史 WNS 数值全部作废，只有口径纪律与流程保留。
