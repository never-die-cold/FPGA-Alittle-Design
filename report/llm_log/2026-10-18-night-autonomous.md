# 2026-10-18 夜间自主执行日志

> 分支：`codex/night-2026-10-18`  
> 起点：`cb352f8be3883a0048e89d38d756fbf87529d5b7`  
> 原则：只做仓库内可复现的离板工作；不 push，不代替 JL 冻结新契约。

## 1. 第零阶段：需求、契约与现状复述

已完整阅读：`AGENTS.md`、`docs/workflow.md`、根 `plan.md`、
`src/riscv/plan.md`、`src/riscv/design_v0.md`、`src/riscv/design_v1.md`、
`src/coprocessor/design_v0.md`、`docs/coprocessor-integration-v0.md`、
`src/coprocessor/README.md`、模块 3 的训练与原型参考、检查 V0 与视觉同步协议、
两份 runner、`data/metrics.csv`，以及 `src/coprocessor/`、`sim/coprocessor/`
现存的全部 RTL/TB。另读了三人收口清单和现行 DDR 离线交接索引。

指定的 `src/coprocessor/plan.md` 与 `docs/coprocessor-handoff-v0.md` 在起点 HEAD
不存在；前者列为本夜 J03 收口待建文件，后者以现行
`docs/cnn-ddr-offline-handoff-2026-10-13.md` 辅助核对，但不冒充缺失文件。

### ✅ 已实现并有仓库内验证入口

- J02 诊断整数参考、量化/打包/解析和逐层黄金生成；它是诊断包，不是正式模型包。
- J03 的 INT8 MAC、128 lane 流水阵列、卷积、ReLU/requant、GAP、FC 与整网 sequencer。
- `mac_array_pipeline` → `conv_engine` → `cnn_sequencer` 现役计算链及对应 TB。
- `mac_lane`、`dot8` 独立诊断 TB；起点提交已把两者接入独立模式和 `all`。
- RISC-V 核既有回归、视觉链既有回归均有仓库 runner；本夜将重新执行而不沿用历史 PASS。

### 🟡 已实现但未完成系统级验证

- 协处理器模块级仿真与 OOC 历史报告已有证据；完整 SoC 综合、实现、100 MHz
  时序和板端行为均未验证。
- C02/C03 已冻结，但 C03 的本地 MMIO/CDC 行为尚未回写核契约并经 JL 确认。
- 诊断参数包能推进 J03/J04 管路验证，但没有真实 PTQ/QAT 权重、阈值和正式黄金身份。

### ⬜ 未实现 / 未接入核

- 物理 BRAM/cache wrapper、`cop_top`、MMIO 寄存器块、CDC mailbox、DMA/payload 装载。
- RISC-V/SoC 接入、工业固件、目标级结果表联动与系统超时闭环。
- 真实数据训练/PTQ（必要时 QAT）、J06 正式模型包、整机位流、上板验证。

### 本夜可安全推进的范围

- J03-R1：只复核起点提交的 runner 接入，跑两个独立模式、协处理器 `all`、全仓 `all`。
- J03 收口：建立模块计划/验收记录，明确诊断模块与现役链，不改 RTL。
- J04 前置：只形成 C03 MMIO 地址和 SoC 行为的核契约草案，标成“待 JL 确认”。
- 余量仅用于独立、低风险的 TB/文档/golden 校验；不展开未经评审的新架构。

禁止碰：冻结 C02/C03 的语义、RISC-V 核既有访存语义、vision/SoC 已验收行为、
J04 RTL、综合/实现/位流和上板。需要新决策时只记问题并跳过。

### 现役数据通路与诊断模块

- 现役：`mac_array_pipeline.v` 内含自己的 128 路乘法/加法树，被
  `conv_engine.v` 实例化，再由 `cnn_sequencer.v` 调度。
- 诊断：`mac_lane.v` 与 `dot8.v` 是独立自测模块，未被现役
  `mac_array_pipeline.v` 实例化；其 PASS 不能替代现役流水线对拍。

### 执行约束

- 冻结契约不得静默修改；核接口仍是无 ready/valid 的同拍异步读、上升沿写本地口，
  不能称作 AXI4-Lite master，也不得暗加等待语义。
- 进入综合的 RTL 必须通过 Verilog-2001，禁止 `.*`、`logic`、`always_ff` 等 SV-only 语法。
- 每个实现小步先设计、改动不超过 100 行，使用仓库内 TB 与 runner，保留原始退出码。
- 仿真 PASS 不等于综合、时序或上板 PASS；历史失败数据不改写。
- 夜间模式替代白天理解门槛：每步闭环后写日志并本地 commit，绝不 push。

## 2. 完成记录

待续。

## 3. 失败、跳过与待确认问题

待续。

## 4. 续工点

第零阶段复述已落盘；下一步从 J03-R1 起点提交的独立与全量回归复核开始。
