# 转发专项 v0 对照基线（2026-09-20）

> 用途：Part B（三级流水 + 数据转发，9/28 开工）的对照锚点——同一测试程序在 v0 上的实测行为；
> v1 接入后用 `+exp_*` 覆盖期望值，同一套程序与 tb 即可给出"转发/停顿是否按契约工作"的判据。
> 相关决策：`report/llm_log/2026-09-20-v0-no-stall-cpi-reframe.md`（v0 无数据停顿、CPI 口径重定义）

## 被测版本

| 项 | 值 |
|:---|:---|
| RTL | v0 两级流水（`src/riscv/*.v`，与 main@`6c324fb` 一致，本轮未改 RTL） |
| 测试程序 | `sim/riscv/fwd/fwd_test.hex`（SHA256 `50687DAF…12DF5`；反汇编 `fwd_test.dis` SHA256 `426C381C…840D`） |
| testbench | `sim/riscv/tb_core_fwd.v`（随本基线提交） |
| 工具 | Icarus Verilog 13.0（MSYS2 ucrt64）；`-g2012 -Wall` |

## 结果（v0 契约：数据冒险零停顿、taken 分支 1 拍）

| 阶段 | 内容 | 周期 | 气泡 | v0 期望 | 判定 |
|:---|:---|---:|---:|---:|:---:|
| A | R 型连读（10 条 RAW 依赖链） | 28 | 0 | 0 | ✅ |
| B | lw→运算连读（4 处 load-use） | 22 | 0 | 0 | ✅ |
| C | taken 分支/跳转（bne×3 + jal + jalr） | 26 | 5 | 5 | ✅ |
| D | not-taken 分支（6 种分支全不跳） | 12 | 0 | 0 | ✅ |
| — | 总周期 122 / 总气泡 8（含启动 1、收尾 2） | | | | ✅ |

结果比对：阶段 A 10 个结果字、阶段 B 5 个结果字、循环计数 4、误跳标记 0 全部与期望一致（逐条推导见 `fwd_test.S` 注释）。
原始输出：`run_iverilog_2026-09-20.log`（SHA256 `F3937B7A…1E23`）。

## v1 使用方式（Part B）

```bash
bash sim/scripts/run_iverilog.sh fwd
# 覆盖期望（示例：v1 三级 + 转发，4 处 load-use 各 1 拍停顿）
vvp sim/build/tb_core_fwd.vvp +exp_a=0 +exp_b=4 +exp_c=5 +exp_d=0
```

机制自证：`plusarg_override_demo.log` 记录了一次故意用 `+exp_b=4` 跑 v0 的结果——按预期 FAIL（`阶段B 气泡 期望 4 实际 0`，退出码 1），证明覆盖参数确实参与判定。

## 复跑方法

```bash
bash sim/scripts/build_fwd.sh          # 汇编 fwd_test.S -> hex/dis（需要 riscv32-unknown-elf-gcc 与 Python）
bash sim/scripts/run_iverilog.sh fwd   # 跑转发专项
bash sim/scripts/run_iverilog.sh       # 全量回归（v0 冒烟 + 逐指令 + 转发专项）
```

## 边界

- 本 tb 只统计**气泡与结果**，CPI 正式测量由基准线 harness 负责（避免重复建设）
- 阶段 C 的 5 拍 = v0 契约值；v1 无预测档同为 5 拍（同为取指冲刷），Part C 上 BHT 后应按命中率变化
