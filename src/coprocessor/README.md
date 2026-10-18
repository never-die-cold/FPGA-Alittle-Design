# src/coprocessor —— CNN 整数算子与整网控制器

轻量 INT8 CNN 的计算链已进入离板验证。v0 已冻结为 MMIO/AXI4-Lite 控制面 + DMA 数据面，
RISC-V 以 load/store 访问且不启用自定义指令。

## 阶段 0 契约

- [C02 整数与硬件契约](design_v0.md)：首网、量化、逐位舍入/饱和、排布与资源预算；
- [C03 集成接口契约](../../docs/coprocessor-integration-v0.md)：MMIO、DMA、状态、结果、固件与 PS 分工。

两份文件均已由 JL 于 2026-10-11 冻结；它们不是 RTL、正式 INT8 模型或 M2 验收证据。
模块 J01–J10 状态与进入 J04 的门槛见 [`plan.md`](plan.md)。
WC/NC 交接只从[协处理器 v0 交接索引](../../docs/coprocessor-handoff-v0.md)进入，避免复制契约表。

## 规划内容

- `cop_top.v`：协处理器顶层
- `dma_ctrl.v`：权重/ROI/结果 DMA 描述符与流控制
- `cop_ctrl_regs.v`：PS AXI4-Lite + RISC-V 本地 MMIO 的逻辑寄存器契约
- `isa_extension.v`：后续可选研究项；v0 不例化、不占 opcode
- `buffer.v`：片上特征图/权重缓存

## 接口约定

- 与 RISC-V 核：`soc_top` 本地 MMIO 窗口，固件以 load/store 启动和轮询；现有核数据口没有等待握手，不能直接冒充 AXI master
- 与 PS：AXI4-Lite 配置/状态；数据通过 AXI DMA/DataMover 搬运
- 与存储系统：只搬权重、逐目标 64×64 ROI 与小结果；中间特征默认驻留 BRAM，不默认全分辨率逐帧 DDR 回写
- C03 已给出寄存器映射；实际接入时须同步核/SoC 契约与驱动，当前 MMIO/DMA 均未接入

## 已实现的离板计算链（2026-10-13）

现役计算通路使用 `mac_array_pipeline.v` 内部的 128 路乘法/加法树；`mac_lane.v` 与
`dot8.v` 仅是独立诊断模块，未被现役阵列实例化，二者 PASS 不能替代现役流水线对拍。

`int8_mac.v` 和 `mac_array.v` 提供组合乘加与 O16/I8 阵列；`mac_array_pipeline.v` 提供 128 路乘法和分拍加法树。`int8_requant.v` / `int8_requant_pipeline.v` 按 C02 实现 ReLU、远离零舍入与对称饱和；`int8_gap.v`、`int8_logits.v` 实现 GAP、稳定 argmax、margin/score 和低置信判定。INT32 溢出导致失败，不回绕或饱和后继续。

`conv_engine.v` 实现一拍同步 BRAM 读接口、分拍地址生成、padding/尾通道、bias 和卷积/FC 调度；`cnn_sequencer.v` 串联四层 Conv→GAP→FC。暂停保持数据和有效位，复位/取消/超时使结果无效。外部 ROI/ping/pong/权重/参数存储须共享复位，busy 期间禁止修改；该模块不包含实体 BRAM、C03 寄存器、DMA 或核接入。

仓库入口：`bash sim/scripts/run_iverilog.sh coprocessor all`，支持 `pipeline`、`conv`、`network`、`watchdog` 专项；默认 Verilog-2001 编译。总回归 `bash sim/scripts/run_iverilog.sh all` 已包含这些入口。首版原始结果和失败记录见[10/13 证据](../../data/logs/2026-10-13-cnn-arithmetic/README.md)。

10/15 优化：尺寸中间值收窄为无符号 8 位并保留非法几何检查；启动时锁存 watchdog 最后允许周期。
卷积读地址/同步读与 MAC 返回重叠，参数每个输出通道块只读一次；16 路 requant 改为两路分时处理，整数语义不变。
两组整网逐元素对拍各为 472,593 周期（含每 7 拍暂停 1 拍），首版为 1,123,109 周期；每网读取 10 组参数。
100 MHz OOC 为 DSP 136/220、LUT 4540、FF 4037，WNS 0.317 ns、WHS 0.123 ns；DSP 门限为 176，保留至少 20% 器件余量。
这些数据包含控制器与算术链，尚不包含实体 BRAM/SoC/视频；[命令与原始证据](../../data/logs/2026-10-15-improvements-fast/README.md)。

`int8_reference.py` 实现输入/bias 量化、舍入、scale 编码与 requant；`int8_tensor_reference.py`
实现张量/逐通道权重量化、bias 和 OIHW 卷积累加，溢出拒绝。Python 全量入口为
`bash sim/scripts/run_coprocessor_python.sh all`，支持 `COPROCESSOR_PYTHON` 或 `VISION_PYTHON` 指定解释器。
`int8_network_reference.py` 实现固定结构整数链、模型形状/类型/范围和通用累加界检查；固定种子诊断权重与两组输入提供逐层黄金，但**不是训练后的正式模型**。`manifests` 独立模式会重新生成算术、算子和整网诊断数据，核对必需文件、来源与落盘 SHA256，并执行篡改负例。

Linux 隔离环境从仓库根目录复现：
```bash
python3 -m venv sim/build/coprocessor-venv
sim/build/coprocessor-venv/bin/python -m pip install -r src/coprocessor/requirements.txt
COPROCESSOR_PYTHON=sim/build/coprocessor-venv/bin/python bash sim/scripts/run_coprocessor_python.sh all
```
venv 位于已忽略的 `sim/build`，不作为交付文件；PASS 证据仍来自仓库内测试与 runner。

综合入口：`powershell.exe -NoProfile -File sim/scripts/run_cnn_ooc.ps1`，自动存档源码/脚本，运行 100 MHz 控制器 OOC 综合与布局布线，保存时序/资源/DRC和退出码。外部存储、SoC与视频未计入，OOC报告不代替整机时序或板端实测。

## 设计参考

- 软/硬件双版本同界面对比范式：往届国一 hlstrack2025_40562（YOLO+UKF 的 soft/hardware 双 notebook），见 [docs/track_research.md](../../docs/track_research.md)
- 算子化验证（CONV/POOL/GEMM 加速比表）与吞吐率指标（每拍采样数/SSR 思路）：[docs/proposal_upgrade.md](../../docs/proposal_upgrade.md)
- 训练/量化侧前期准备与接口对齐点：[docs/module3-model-training.md](../../docs/module3-model-training.md)

> 未实现：正式 INT8 训练/权重发布、实体 BRAM 与完整协处理器顶层、C03 MMIO/DMA、核接入和工业固件；首网板端输出与整机时序/性能尚未验证。
