# [2026-10-06] 协作记录：if_stage 模块——flush 只清 valid（把 flush 移出指令数据路径）

> 标签：#riscv #流水线 #时序优化 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本模块（`src/riscv/if_stage.v` + `sim/riscv/tb_if_stage.v`）随本轮 PC/flush 降深度同批提交；概览见 `2026-10-06-partC-pc-depth.md`

## 1. 任务与初始提示词

验证线实测 BHT2 核 OOC @11.520 ns **WNS = −0.334 ns**，最差路径 `u_if_stage/instr_hold_reg[5] → u_pc/pc_reg[27]`（17 级、route 66.6%）。要求**保持三级**、不改“误预测冲 1 槽 / 正确预测零气泡 / 四档统计语义”，把这条路径降深度。本模块：**让 `flush` 只影响 `valid`，不再参与 32 位指令数据选择**。

## 2. 模型第一版方案

```verilog
// 旧：instr = stall_q ? instr_hold : (flush_q ? NOP : imem_rdata);
assign instr       = stall_q ? instr_hold : imem_rdata;   // flush_q 移出数据路径
assign instr_valid = stall_q ? valid_hold : ~flush_q;     // flush 只改有效位
// 停顿首拍：instr_hold <= imem_rdata;  valid_hold <= ~flush_q;
```

无效槽允许含 `mul/store/JAL` 编码（数据为 don't-care）；所有副作用由 `valid` 门控。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；**未决**：优化后 WNS/Fmax/资源未验证，交验证线实跑 11.520 ns 与四档 10 ns。
2. 本机无 Vivado；不保证综合后逻辑级数（布线占比/新增扇出可能影响）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `flush_q` 选择 NOP 串在 32 位数据路径里 | 控制（valid）应与数据（instr）分离 | `instr` 去掉 flush 选择，`instr_valid` 保留 flush | ✅ `tb_if_stage` 12 例 PASS |
| 2 | 无效槽仍可能含 mul/store 编码 | 靠 valid 门控副作用，不必注入 NOP | 保持 valid 门控 | ✅ 768 例真值表等价、无副作用 |

## 5. 最终结论

`if_stage` 现在 `flush` **只清 `instr_valid`**，指令数据路径只受 `stall_q` 的快照/直通选择，`flush_q` 不再串进 `imem_rdata → decode/target` 的 32 位路径。功能等价由 `tb_if_stage`（12 例）、`pc_control`（768 例等价）与四档 cycles 不变证明；**时序收益待 Vivado 复测**。

## 6. 经验沉淀

- **控制与数据分离**：`valid` 负责副作用门控，**不要把它串进 32 位数据路径**（这里 flush 注入 NOP 曾占着关键路径）。
- NOP 注入只做波形可读，**不能代替 valid 门控**；无效槽按 don't-care 处理。
- #skill候选
