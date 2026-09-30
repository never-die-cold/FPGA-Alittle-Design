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
- 与存储系统：权重、逐目标小图与特征图缓冲的 AXI / 自定义握手；PS/PL 搬运及 BRAM/DDR 使用由缓存契约冻结，不默认全分辨率逐帧 DDR 回写
- 寄存器映射表定稿后同步更新到 `docs/` 与 `src/riscv_fw/`

## 设计参考

- 软/硬件双版本同界面对比范式：往届国一 hlstrack2025_40562（YOLO+UKF 的 soft/hardware 双 notebook），见 [docs/track_research.md](../../docs/track_research.md)
- 算子化验证（CONV/POOL/GEMM 加速比表）与吞吐率指标（每拍采样数/SSR 思路）：[docs/proposal_upgrade.md](../../docs/proposal_upgrade.md)
- 训练/量化侧前期准备与接口对齐点：[docs/module3-model-training.md](../../docs/module3-model-training.md)

> 状态：训练导出演练已完成，正式紧固件模型与协处理器 RTL 尚未实现。首版为自由分散且互不遮挡的物体，由传统视觉定位、逐目标裁剪后送入 CNN 分类。模块一验收后主力转入，M2 首网验证、M3 工业闭环的收口时间以根目录 [项目主计划](../../plan.md) 为准；L2 降级时可整体裁剪。当前接口仍为规划，须与视频/分析分流及快照缓存对齐后冻结。
