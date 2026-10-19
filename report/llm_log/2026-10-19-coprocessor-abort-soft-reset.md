# [2026-10-19] 协作记录：cop_core_mmio_gate / cop_ctrl_regs / cop_task_ctrl 模块——ABORT / SOFT_RESET 命令链

> 标签：#coprocessor #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL，夜间）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`9fdd035` 前的 J04-23/24 提交；总记录见 `2026-10-18-j04-closeout.md`（J04-23/24 段）

## 1. 任务与初始提示词

J04-23/24：为协处理器补 **ABORT / SOFT_RESET** 命令入口与执行链——核侧 MMIO 门禁接受 C03 的 `CTRL[5:0]` 命令、拒绝保留位；命令产生**单拍脉冲**；ABORT 只允许在 busy 时生效；SOFT_RESET 清运行状态/结果但**保留 MODEL_VALID**。

## 2. 模型第一版方案

- `cop_core_mmio_gate`：`ctrl_bits_valid=(wdata & 0xFFFF_FFC0)==0`、`ctrl_has_command=|wdata[5:0]`；`abort_allowed=!(wdata[1] && !busy_i)`（ABORT 仅 busy 合法），并纳入 `ctrl_write_valid`。
- `cop_ctrl_regs`：新增 `abort_pulse_o` / `soft_reset_pulse_o`；`CTRL[1]`→ABORT（同时置 `error`）；`CTRL[2]`→SOFT_RESET（清 `done/error/timeout/result_valid`）；`CTRL[0]`→START。
- `cop_task_ctrl`：`soft_reset_i`→回 IDLE 清运行状态；`abort_i && busy_o`→回 IDLE 并产生 `error_pulse`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 首次 `all` 退出 1：**旧 TB 仍预期 ABORT 被拒**；同步契约预期后重跑通过。
2. 顶层首跑两次在 ABORT 错误检查失败：先补 NBA 取样延时，再把错误锁存从后级脉冲改为**命令接收当拍**。
3. **未决**：综合/时序/上板未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | ABORT 任意时刻都接受 | 只应在 busy 时有效 | `abort_allowed` 门禁 | ✅ `mmio_gate` PASS |
| 2 | 命令常驻电平会重复触发 | 需单拍脉冲 | `ctrl_regs` pulse 寄存器 | ✅ `ctrl_regs` PASS |
| 3 | ABORT 错误检查失败 | NBA 取样/锁存时点问题 | 延时 + 命令当拍锁存 | ✅ `task_ctrl`/`cop_top` PASS |
| 4 | 软复位会误清权重 | 应只清运行状态/结果 | 保留 MODEL_VALID | ✅ 顶层 PASS |

## 5. 最终结论

ABORT/SOFT_RESET 命令链落地：门禁保留位校验、单拍脉冲、busy-only ABORT、软复位保留模型有效；独立 `mmio_gate`/`ctrl_regs`/`task_ctrl`/`cop_top` 与 `all` 均 PASS。硬件验证未做。

## 6. 经验沉淀

- 命令寄存器必须做**保留位校验** + **单拍脉冲**，不能靠常驻电平；
- **ABORT 仅在 busy 时合法**；软复位要区分“运行状态/结果”与“权重/模型有效”；
- 错误锁存要在**命令接收当拍**，别依赖后级脉冲的取样时序。 #skill候选
