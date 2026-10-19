# [2026-10-19] 协作记录：cop_top / cop_config_regs 模块——PS 控制权限与配置读回

> 标签：#coprocessor #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL，夜间）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：发布分支 `a88a042`（J04-25）；总记录见 `2026-10-18-j04-closeout.md`（J04-25 段）

## 1. 任务与初始提示词

J04-25：明确 **PS 与核的控制权限边界**，并让配置可经 AXI4-Lite 读回——PS **只能** 发 `ABORT/SOFT_RESET`，**不能**发 `START`；核命令优先，冲突时 PS 写零副作用拒绝；`RESULT_INDEX` 可由 PS 选择；配置 shadow/applied、工单统计/决策可读回。

## 2. 模型第一版方案

- `cop_top`：`ps_ctrl_access = (offset==0x00C || 0x06C)`；`ps_ctrl_allowed`——`CTRL` 仅允许 `[2:1]`（ABORT/SOFT_RESET）、禁 `[0]` START 与 `[7:3]` 保留位，`RESULT_INDEX` 要求 `[7:4]==0`；`ps_ctrl_valid = ps_write_valid && ps_ctrl_access && ps_ctrl_allowed && !command_valid`（**核命令优先**，冲突时 PS 写零副作用）。
- `cop_config_regs`：新增 `read_offset_i` / `read_data_o`，读回 `CFG_APPLIED(0x020)` 与 `shadow(0x018..0x064)`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败。
2. **未决**：AW/W 相位与背压矩阵、跨域返回路径完整扫描、综合与上板均未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | PS 能发 START | 控制权应分层 | `ps_ctrl_allowed` 只放 ABORT/SOFT_RESET | ✅ `cop_top` PASS |
| 2 | 核与 PS 同拍冲突 | 必须定优先级 | `!command_valid` 门控 PS 写 | ✅ |
| 3 | 配置不可读 | 加读回通道 | `cop_config_regs` read_offset/data | ✅ `config_regs` PASS |

## 5. 最终结论

PS 权限与配置读回落地：PS 仅 ABORT/SOFT_RESET、核命令优先且冲突时零副作用、配置 shadow/applied 可读；`config_regs`/`cop_top`/`all` PASS，J02 zero 最终 `9225 packed words / 73795 elements` 匹配。硬件验证未做。

## 6. 经验沉淀

- **控制权分层**：PS 只保留 abort/reset，启动权在核；
- 核/PS 同拍冲突时**核优先**，PS 写要零副作用拒绝；
- 配置读回同时暴露 **shadow 与 applied**，便于驱动校验原子提交。 #skill候选
