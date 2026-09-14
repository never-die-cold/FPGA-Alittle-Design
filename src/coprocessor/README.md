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

## 设计参考

- 软/硬件双版本同界面对比范式：往届国一 hlstrack2025_40562（YOLO+UKF 的 soft/hardware 双 notebook），见 [docs/amd_track_awards.md](../docs/amd_track_awards.md)
- 算子化验证（CONV/POOL/GEMM 加速比表）与吞吐率指标（每拍采样数/SSR 思路）：[docs/proposal_upgrade.md](../docs/proposal_upgrade.md)

> 状态：🚧 待开发（M2 里程碑，L2 降级时可整体裁剪）
