# src/coprocessor —— CNN 推理协处理器 RTL

以自定义指令 + AXI 接口挂载到 RISC-V 核的轻量 CNN 加速器，INT8 量化。

## 规划内容

- `cop_top.v`：协处理器顶层
- `mac_array.v`：INT8 MAC 阵列
- `dma_ctrl.v`：权重/特征图 DMA 搬运控制
- `isa_extension.v`：自定义指令译码（`conv.start` / `conv.wait` 等）
- `buffer.v`：片上特征图/权重缓存

## 接口约定

- 与 RISC-V 核：自定义指令通道（操作码 + 操作数 + 完成信号）
- 与存储系统：AXI / 自定义握手访存 DDR 帧缓冲
- 寄存器映射表定稿后同步更新到 `docs/` 与 `sw/riscv_fw/`

> 状态：🚧 待开发（M2 里程碑，L2 降级时可整体裁剪）
