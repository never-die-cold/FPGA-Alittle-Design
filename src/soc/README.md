# src/soc —— 顶层集成与总线互连

RISC-V 核 + CNN 协处理器 + 预处理流水线的 SoC 级集成，以及与 PS 侧的接口。

## 规划内容

- `soc_top.v`：PL 侧 SoC 顶层
- `bus_interconnect.v`：内部总线互连（指令/数据存储、外设地址映射）
- `imem.v` / `dmem.v`：指令/数据存储（BlockRAM）
- `ps_interface.v`：PS↔PL AXI-Lite 寄存器映射 + 中断
- `addr_map.md`：地址映射表（定稿后同步 `sw/` 两侧）

## 地址映射

待定稿后在此维护唯一权威版本，`sw/riscv_fw/` 与 `sw/pynq_host/` 均以本表为准。

> 状态：🚧 待开发（M1 起步，M3 完成集成）
