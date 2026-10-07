# src/riscv —— RISC-V 软核 RTL

自研三级流水 RISC-V 核（RV32IM）：流水线重构 + 数据转发（旁路）+ 轻量分支预测。

> 📋 收口证据与四档数据见 [模块一报告](../../report/module1-closure.md)，技术验收与学习路线见 [plan.md](plan.md)；Part A 历史证据见 [done/m1-first-phase-completed.md](done/m1-first-phase-completed.md)。
> 🔧 v0 接口冻结（模块划分 / 信号表 / 控制真值表）：[design_v0.md](design_v0.md)。

## v1 已实现内容

- `core_top.v`：核顶层，例化各级流水与互连（v1 改造）
- `id_ex_stage.v`：组合译码 + 执行级（decode/ALU、分支目标与条件）；不增加流水寄存器
- `mem_wb_stage.v`：执行到提交的边界寄存器；访存与写回组合逻辑在 core_top
- `forwarding.v`：数据转发（旁路）单元
- `hazard.v`：冒险检测与流水线暂停（Stall）控制
- `branch_predict.v`：1-bit/2-bit 分支历史表
- `decode.v`：译码（R1 已加 `uses_rs1/uses_rs2` 源使用标志）
- `regfile.v` / `alu.v` / `pc.v` / `muldiv.v`：v0 已有，v1 沿用

> v1 模块接口与拍序以 `design_v1.md` 冻结契约为准。

## SoC 外壳与集成（原 `src/soc/` 并入本目录）

- `soc_top.v`：PL 侧 SoC 顶层（核 + 指令 BRAM + 数据 RAM + 最小外设）
- `imem.v` / `dmem.v`：32KB 同步读指令 BRAM / 32KB 异步读分布式数据 RAM
- **未实现**：`bus_interconnect.v`、`ps_interface.v`、统一 `addr_map.md`；当前译码在 soc_top，PS/协处理器集成属于后续模块

## 命名与编码约定

- 文件与模块名：小写 + 下划线；时钟 `clk`、复位 `rst_n`（低有效）
- 每个模块头部注释：功能、接口说明、作者、日期
- 所有模块必须先通过 `sim/` 下对应 testbench 再上板

## 版本基线

- `v0`：两级流水基线（已收口，锚点 tag `partA-v0` = `962a4f5`，接口见 `design_v0.md`）
- `v1`：三级流水 + 转发 + Radix-4 乘法 + 可切换 BHT（实现与验收证据见 `design_v1.md` §14/§16）

默认配置为转发开、BHT 关；Part C 主验收配置为转发开、BHT2。保持相同存储器端口，核 OOC 与 40MHz SoC/上板频率分开记录。提交仍须用户通过理解门槛。
