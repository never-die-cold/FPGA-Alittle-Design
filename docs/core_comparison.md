# 核性能对比计划：自研核 vs PicoRV32 vs E203

> 状态（2026-10-09）：自研核四档 CoreMark 与模块一收口见[收口报告](../report/module1-closure.md)；PicoRV32 已有 OOC 原始报告，频率数字为 Slack 外推，未重跑其 CoreMark。
> §1 排期与 §4 风险预案保留为 9/21 历史；其中 v0 CPI≈1／DMEM 同步改造不是当前设计结论或新任务。
> 决策记录：[`report/llm_log/2026-09-21-narrative-architecture-fix.md`](../report/llm_log/2026-09-21-narrative-architecture-fix.md)
> 本文回答答辩必问题："PicoRV32/E203 现成且更成熟，你们自研的差异化优势是什么？"——用数据回答，不用情怀。

---

## 1. 已确认的执行决策（2026-09-21）

| # | 决策 | 内容 | 负责 | 时间 |
|:---:|:---|:---|:---|:---|
| 1 | 基准只用 CoreMark | 不做 Dhrystone；EEMBC 官方 coremark 裸机移植（`core_portme.c/h`） | 基准线 `dev/bench` | 9/25–10/1（与 Part B/C 并行；2026-09-21 排期压缩前移） |
| 2 | 仿真跑分用 iverilog | 短迭代（32 次）实测 → 外推 CoreMark/MHz，报告注明"仿真外推口径" | 基准线 | 同上 |
| 3 | dmem/imem 扩容 + SoC 计数器归 Part A 收口 | dmem 4KB→32KB（CoreMark 数据段）；imem 16KB→32KB（代码段）；`soc_top` 加 32-bit 存储器映射自由运行计数器（计时用） | RTL 线 `dev/rtl` | 9/24 前（Part A 收口一并做；9/27 合并日复核） |
| 4 | PicoRV32 对比由验证线做，排 M1 收口后 | regular + large 两配置，同器件同工具 OOC post-route | 验证线 `dev/verify` | 10/21–10/24（M4 窗口前段；原 10/5–10/8 因排期压缩让位 M2/M3） |
| 5 | PicoRV32 性能数据引用官方公开口径 | 不重跑其 CoreMark；引用 0.309 DMIPS/MHz + CPI 4–5，注明来源 | 验证线 | 同上（10/21–10/24） |

## 2. 参照数据（公开口径，正式引用前须逐条核对原文）

| 核 | LUT | Fmax | CPI | DMIPS/MHz | 来源与口径 |
|:---|---:|---:|---:|---:|:---|
| 本项目 v0（两级） | 1606 | 83.8 MHz（Slack外推，WNS −1.935@10ns；10/03复现同值） | CoreMark 2.105（短仿真；非设计推导≈1） | 未测 | `data/metrics.csv`、[对比实测](../data/logs/2026-10-03-picorv32-compare/README.md) |
| PicoRV32 (regular) **本仓 OOC** | 905 | **194.6 MHz（Slack 外推）**；WNS −0.139@5ns，该约束实点失败 | 4–5（引用作者自述，未重跑） | 未测 | [2026-10-03 对比实测](../data/logs/2026-10-03-picorv32-compare/README.md)，OOC 同法 |
| PicoRV32 (large，含 M) **本仓 OOC** | 2006 | **134.3 MHz（Slack 外推）**；WNS −0.445@7ns，该约束实点失败 | — | — | 同上 |
| PicoRV32 (regular) | ~904 | ~196–200 MHz（Artix-7 -1 级 post-route，作者精调约束） | 4–5（作者自述） | 0.309 | 官方 README + JIPS 论文 |
| PicoRV32 (large，含 M) | ~2019 | 同上量级 | — | — | 官方 README |
| 蜂鸟 E203 | 4153 | 41.7 MHz（**综合口径，非实现**） | ≈1 | 1.61（社区移植 50MHz 实测） | JIPS 论文 / 社区移植 |
| SiFive E31 | 3614 | 100 | — | — | JIPS 论文（综合） |
| SCR1 | 4337 | 40 | — | — | JIPS 论文（综合） |

> JIPS 论文：*Selecting a Synthesizable RISC-V Processor Core for Low-Cost Devices*（JIPS 2025，Vivado 综合 XC7Z020-clg400，与本项目同器件同速度级）。⚠️ 该表为**综合级**数据、未做实现优化，E203 Fmax 可能有水分；引用必须注明口径。

## 3. 对比指标定义

- **CoreMark/MHz**：当前四档为 v1_nofwd / v1_fwd / v1_fwd_bht1 / v1_fwd_bht2；v0 是外部历史锚点。短仿真外推不是官方长时间认证分数。
- **CoreMark/LUT**：面积能效。只在负载、计时和资源口径一致时比较；不能用 PicoRV32 公开 CPI 与自研 CoreMark CPI 直接推出加速倍数。
- **Fmax（约束递减收敛法）**：PicoRV32 对比时不能只跑 10ns 约束（大正 slack 会低估其 Fmax），做 10ns→5ns→收敛 2–3 轮，两边同法。
- 口径纪律：同器件（xc7z020clg400-1）、同工具（Vivado 2026.1）、同为 post-route（E203 引用数据除外，须标注"综合口径"）。

## 4. 风险预案

1. **CoreMark/MHz < 0.5**：说明两级结构的每拍取指瓶颈比 design_v0.md §2.2 推导严重——撤回性能对比话术，README 论证降级为单轴"面积效率 + 协处理器耦合"。
2. **dmem 同步读改造破坏 v0 CPI≈1 锚点**：改造后重跑 v0 冒烟 + arch-test 回归；CPI 口径变化记入 llm_log（诚实数据要求）。
3. **CoreMark 数据段超 32KB**：先裁迭代数据规模（官方配置项），不考虑 DDR（触碰零 DDR 卖点）。
4. **PicoRV32 Fmax 远超本核**：预期内（其为作者精调的 size/fmax 优化设计）；对策是聚焦 CoreMark/LUT 与协处理器耦合论证，不押主频。

## 5. 产出物

2026-10-07 自研核v0外部锚点及v1四档CoreMark/MHz、每MHz面积归一值、原始日志与方法限制见 [模块一收口报告](../report/module1-closure.md)；不能把外推值标成实际通过频率，也不拿PicoRV32公开CPI作同负载加速比。

- [x] 自研核四档 CoreMark/MHz 与每 MHz 面积归一值已入[收口报告](../report/module1-closure.md)和[指标表](../data/metrics.csv)；不是实板 CoreMark/LUT。
- [x] 自研核跑分与 PicoRV32 OOC 日志已在[模块一证据](../data/logs/2026-10-07-module1-closure/README.md)及[PicoRV32 证据](../data/logs/2026-10-03-picorv32-compare/README.md)归档。
- [x] 本文档 §2 表更新为实测数字 + PicoRV32 实测行（2026-10-03，Fmax/资源列；CPI/DMIPS 引用公开口径）
- [x] [README「为什么自研核」](../README.md)已刷新为当前四档 CPI、BHT2 核实点资源与比较限制；未宣称 PicoRV32 同负载优势。
