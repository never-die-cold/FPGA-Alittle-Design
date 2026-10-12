# src/coprocessor —— CNN 推理协处理器 RTL

规划中的轻量 INT8 CNN 加速器。v0 已冻结为 MMIO/AXI4-Lite 控制面 + DMA 数据面，
RISC-V 以 load/store 访问且不启用自定义指令。

## 阶段 0 契约

- [C02 整数与硬件契约](design_v0.md)：首网、量化、逐位舍入/饱和、排布与资源预算；
- [C03 集成接口契约](../../docs/coprocessor-integration-v0.md)：MMIO、DMA、状态、结果、固件与 PS 分工。

两份文件均已由 JL 于 2026-10-11 冻结；它们不是 RTL、正式 INT8 模型或 M2 验收证据。

## 规划内容

- `cop_top.v`：协处理器顶层
- `mac_array.v`：INT8 MAC 阵列
- `dma_ctrl.v`：权重/ROI/结果 DMA 描述符与流控制
- `cop_ctrl_regs.v`：PS AXI4-Lite + RISC-V 本地 MMIO 的逻辑寄存器契约
- `isa_extension.v`：后续可选研究项；v0 不例化、不占 opcode
- `buffer.v`：片上特征图/权重缓存

## 接口约定

- 与 RISC-V 核：`soc_top` 本地 MMIO 窗口，固件以 load/store 启动和轮询；现有核数据口没有等待握手，不能直接冒充 AXI master
- 与 PS：AXI4-Lite 配置/状态；数据通过 AXI DMA/DataMover 搬运
- 与存储系统：只搬权重、逐目标 64×64 ROI 与小结果；中间特征默认驻留 BRAM，不默认全分辨率逐帧 DDR 回写
- 寄存器映射表定稿后同步更新到 `docs/` 与 `src/riscv_fw/`

## 设计参考

- 软/硬件双版本同界面对比范式：往届国一 hlstrack2025_40562（YOLO+UKF 的 soft/hardware 双 notebook），见 [docs/track_research.md](../../docs/track_research.md)
- 算子化验证（CONV/POOL/GEMM 加速比表）与吞吐率指标（每拍采样数/SSR 思路）：[docs/proposal_upgrade.md](../../docs/proposal_upgrade.md)
- 训练/量化侧前期准备与接口对齐点：[docs/module3-model-training.md](../../docs/module3-model-training.md)

> 状态：C02/C03 已冻结；FP32 逐层参考和训练导出演练已有仓库证据。正式 INT8 模型、整数黄金、协处理器 RTL、MMIO/DMA 接入与工业固件均未实现。
