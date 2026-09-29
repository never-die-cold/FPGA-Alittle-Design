# src/riscv —— RISC-V 软核 RTL

自研三级流水 RISC-V 核（RV32IM）：流水线重构 + 数据转发（旁路）+ 轻量分支预测。

> 📋 剩余计划（三级+转发 / 预测+验证）与技术栈学习路线见 [plan.md](plan.md)；已完成部分（阶段 0 / 第一阶段 / Part A）原文与证据归档见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)。
> 🔧 v0 接口冻结（模块划分 / 信号表 / 控制真值表）：[design_v0.md](design_v0.md)。

## v1 规划内容（待实现）

- `core_top.v`：核顶层，例化各级流水与互连（v1 改造）
- `id_ex_stage.v`：译码 + 执行级（译码、ALU、乘除单元、转发裁决）
- `mem_wb_stage.v`：访存 + 写回级
- `forwarding.v`：数据转发（旁路）单元
- `hazard.v`：冒险检测与流水线暂停（Stall）控制
- `branch_predict.v`：1-bit/2-bit 分支历史表
- `decode.v`：译码（R1 已加 `uses_rs1/uses_rs2` 源使用标志）
- `regfile.v` / `alu.v` / `pc.v` / `muldiv.v`：v0 已有，v1 沿用

> v1 模块接口与拍序以 `design_v1.md` 冻结契约为准。

## SoC 外壳与集成（原 `src/soc/` 并入本目录）

- `soc_top.v`：PL 侧 SoC 顶层（核 + 指令 BRAM + 数据 RAM + 最小外设）
- `bus_interconnect.v`：内部总线互连（指令/数据存储、外设地址映射）
- `imem.v` / `dmem.v`：指令/数据存储（BlockRAM）
- `ps_interface.v`：PS↔PL AXI-Lite 寄存器映射 + 中断（M3）
- `addr_map.md`：地址映射表（定稿后 `src/riscv_fw/` 与 `src/pynq_host/` 均以此为准）

## 命名与编码约定

- 文件与模块名：小写 + 下划线；时钟 `clk`、复位 `rst_n`（低有效）
- 每个模块头部注释：功能、接口说明、作者、日期
- 所有模块必须先通过 `sim/` 下对应 testbench 再上板

## 版本基线

- `v0`：两级流水基线（已收口，锚点 tag `partA-v0` = `962a4f5`，接口见 `design_v0.md`）
- `v1`：三级流水 + 转发 + 分支预测（契约已冻结，见 `design_v1.md`；转发/冒险/三级重构 RTL 待实现）

> 状态（2026-09-29）：v0 与 Part A 收口完成；v1 契约定稿、R1 译码源使用标志已落地并通过回归；剩余 RTL 按 10/2 交付、10/4 验收推进。
