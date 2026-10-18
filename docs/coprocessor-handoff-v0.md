# CNN 协处理器 v0 交接索引

> 给 JL、WC、NC 查找离板计算链的唯一入口；交接或复现前阅读。  
> 本页只指向权威契约和证据，不复制寄存器表、payload offset 或历史日志正文。

## 当前状态

- J03 离板计算链已收口：诊断整数参考、算子、Conv→GAP→FC 控制器和逐元素 TB 可复现。
- J04 未实现：实体存储、`cop_top`、MMIO/CDC、DMA、核接入和工业固件均不存在。
- J05/J06 未完成：没有真实审计 ROI 上的正式 INT8 模型、阈值和发布黄金。
- J07/J08 未完成：没有整机实现、位流或可交 NC 上板的三批正式交付包。

## 权威来源

| 内容 | 唯一来源 |
| --- | --- |
| 网络、整数算术、张量排布、payload | [C02](../src/coprocessor/design_v0.md) |
| MMIO、状态、DMA、结果与 PS/核分工 | [C03](coprocessor-integration-v0.md) |
| 核现役语义与待确认 SoC 回写 | [design_v1 §17](../src/riscv/design_v1.md) |
| J01–J10 状态和进入 J04 的门槛 | [模块计划](../src/coprocessor/plan.md) |
| J03 本轮离板复验 | [验收索引](../data/logs/2026-10-18-j03-closeout/README.md) |
| 10/13 CNN/DDR 历史接口与失败边界 | [历史交接](cnn-ddr-offline-handoff-2026-10-13.md) |
| 三人职责与最终签收 | [收口清单](project-closeout-three-person-checklist.md) |

若计划、README 或本页与 C02/C03 冲突，以 C02/C03 为准，并修正文档；不得反向改契约。

## JL 当前可交付给开发的内容

- 现役数据通路：`mac_array_pipeline` → `conv_engine` → `cnn_sequencer`；
- 诊断模块：`mac_lane`、`dot8`，未被现役阵列实例化；
- 两组诊断整网逐元素黄金，每组 73,795 个有效元素、472,593 个控制周期；
- 独立 runner、协处理器 `all` 与全仓 `all`；最终夜间复验均退出 0；
- 控制器 OOC 历史证据，但不包含实体 BRAM、DMA、SoC 或视频链。

这批内容可用于 J04 开发起步，不是正式模型包、整机包或板端验收包。

## WC 对接边界

- 驱动字段、权限、状态、目标结果和工单语义只按 C03；协议仍按 v1.2 决策单；
- 硬件能力 16 目标，检查 V0 策略最多 10 件；11–16 必须 RECHECK，不截断；
- 等 J04 寄存器/CDC 仿真通过后再签收驱动实现；当前只能 review 契约，不能联调硬件。

## NC 对接边界

- 片上存储需求与 10/13 历史 word 级接口可供规划，但正式 payload 字节数以模型 manifest 为准；
- OOC 正时序不代表完整 SoC 100 MHz；综合、实现、位流和上板状态均为未验证；
- J08 顺序保持“算子诊断包 → 首网包 → 整机包”，当前三包均未正式发布。

## 复现入口

```text
bash sim/scripts/run_coprocessor_python.sh manifests
bash sim/scripts/run_coprocessor_python.sh all
bash sim/scripts/run_iverilog.sh cop_mac_lane
bash sim/scripts/run_iverilog.sh cop_dot8
bash sim/scripts/run_coprocessor_iverilog.sh all
bash sim/scripts/run_iverilog.sh all
```

Linux 全仓 Python 回归需通过 `VISION_PYTHON`/`COPROCESSOR_PYTHON` 指向包含冻结依赖的解释器。
原始夜间执行、环境失败和最终退出码见[夜间日志](../report/llm_log/2026-10-18-night-autonomous.md)。

## 下一门槛

JL 先确认 `design_v1.md` §17 的子字写、连续写邮箱和非法访问细节；确认前不写 J04 RTL。

