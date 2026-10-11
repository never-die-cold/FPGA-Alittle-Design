# [2026-10-10] 协作记录：协处理器 C03 模块——PS / RISC-V / 协处理器集成契约（coprocessor-integration-v0.md）

> 标签：#coprocessor #架构决策 #接口契约
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本文件（`docs/coprocessor-integration-v0.md`）随本轮 G0 契约同批提交

## 1. 任务与初始提示词

冻结协处理器与核/PS 的接口：**控制权、寄存器语义、DMA 数据对象、任务/结果关联、busy/done/error/timeout、复位、低置信与工单结果衔接**；v0 **不启用自定义指令、不改 RV32IM 译码/三级流水/转发/BHT**。

## 2. 模型第一版方案

- **控制面**：MMIO + AXI4-Lite；**数据面**：DMA（只搬小 ROI、权重、结果）。
- **分工**：PS 软件/LIVE 服务做定位与 INT8 输入导出、在 DDR 准备权重包/ROI/目标描述符；`config/model/job` 经 AXI4-Lite 提交，数据经 AXI DMA/DataMover。
- **现状**：核数据口只有 `addr/wdata/be/we/rdata`（**无 `ready/valid`**，DMEM 同拍异步读、上升沿写）→ **不得冒充 AXI master**。v0 在 `soc_top` 增**单周期本地 MMIO 窗口**，经请求/应答 CDC 与协处理器控制域交换；PS 侧用真正 AXI4-Lite slave 访问同一逻辑寄存器映射。
- 逻辑寄存器表、`config/result` 原子提交、结果布局、超时/错误/复位、`seq` 原子提交、软复位保权重、ROI DMA 排布；本地 MMIO 基址 `0x8001_0000`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **“核直接访问 AXI4-Lite”缺少等待语义**：现有核无握手 → 推荐本地单周期 MMIO + CDC（真 AXI 留给 PS 侧）。
2. **10 与 16 混用**：检查 V0 最多 10 与协议最多 16 被混为一谈 → 冻结为“硬件/协议能力 16、检查 V0 业务策略 10；11–16 直接 RECHECK”。
3. **开始实现前须回写**：新增 MMIO 地址与 SoC 行为要回写 `src/riscv/design_v1.md`（其“地址空间/端口不变、无总线等待”条款不能静默绕过）。
4. **未决**：接口/RTL 未实现，板端验收未做。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 把核数据口当 AXI master | 核口无 `ready/valid`，无法完成握手 | 本地单周期 MMIO + 请求/应答 CDC | ✅ 写入契约 |
| 2 | 10 与 16 当同一上限 | 能力与业务策略应分层 | 能力 16 / 策略 10，超 10 RECHECK | ✅ 冻结口径 |

## 5. 最终结论

C03 契约冻结为 **v0 基线**：`MMIO + AXI4-Lite`（控制）+ `DMA`（数据）；自定义指令降为后续研究项。**接口未实现**，且新增 MMIO 地址需在实现前回写核契约。

## 6. 经验沉淀

- **协议名替代不了时序契约**：没有 `ready/valid` 的核端口不能静默接入可等待 AXI；
- “系统上限”与“业务策略上限”必须**分层**，否则破坏协议兼容；
- 任何新增地址/总线行为都要**回写核契约**，不得绕过冻结条款。 #skill候选
