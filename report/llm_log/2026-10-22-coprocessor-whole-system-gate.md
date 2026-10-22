# [2026-10-22] 协作记录：Windows Vivado 40 MHz OOC 修复与整机门禁

> 标签：#coprocessor #Vivado #时序 #资源 #门禁
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`10fa44a` `437e973` `edd6ac8` `07327ba` `d6ff9f0`

## 1. 任务与初始提示词

从 `2026-10-21-board-gate-checkpoint.md` 的 f) 命令继续，在 Windows 侧真跑 40 MHz
`compute` / `storage` OOC；修掉阻止门禁的 XDC 与 BRAM 推断问题；新增整机（非 OOC）
40 MHz 门禁，保留 `ENABLE_COP=0` 基线；只有整机通过才允许 bitstream/.hwh。

## 2. 模型第一版方案

保持 `build/build_coprocessor_gate.tcl` 的 40/100 MHz 分档；删除 XDC 中不支持的 `if`；
为 ROI/ping/pong 增加无复位同步 1R1W RAM 模板，让 Vivado 推断实体 BRAM；
新增 `build_pynq_cop_gate.tcl` + `create_pynq_cop_bd.tcl` + PS1 脚本做整机门禁，
判定 WNS≥0、DSP≤220、BRAM36≤140、DRC/CDC 无未豁免。

## 3. 失败现象

1. checkpoint 里的 Vivado 路径不存在；注册表实际为 `D:\vivado\2026.1\Vivado`。
2. compute 首次退出 0、WNS +7.460，但 XDC 的两条 `if` 被 Vivado 报为不支持（4 条 Critical Warning）。
3. storage 首次退出 1：ROI 被拆成 32,768 个寄存器、ping/pong 变 distributed RAM，
   `UTLZ-1` LUT 57,380 > 53,200，placer 未运行。
4. 整机首跑综合/布线完成（WNS +2.663、WHS +0.020、LUT 48.8%、DSP 136/220、BRAM36 69/140、DRC 0），
   但 `check_timing no_clock=360`、`unconstrained_internal_endpoints=120`，门禁 **FAIL**（不是时序问题）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | Vivado 路径不存在 | 存档路径漂移 | 用注册表实际安装路径 | 进入综合 |
| 2 | XDC `if` Critical Warning | XDC 不支持条件语句 | `10fa44a` 删条件，周期由 Tcl 注入 | 约束可解析 |
| 3 | storage LUT 57,380 超限 | ROI/ping/pong 未推断 BRAM | `437e973` 同步 1R1W RAM 模板 | 28×RAMB36+1×RAMB18 |
| 4 | 整机 no_clock/120 未约束 | CDC 载荷被常量折叠 | 见 CDC/latch 记录修复 | 整机门禁最终 PASS |

## 5. 最终结论

40 MHz OOC 真实结果：

| 目标 | 退出码 | LUT | FF | DSP | BRAM | WNS / WHS |
|:---|---:|---:|---:|---:|---:|:---|
| compute | 0 | 6,299 | 7,261 | 136 | 0 | +7.460 / +0.097 ns |
| storage | 0 | 38,562 | 12,389 | 0 | 28.5 | +18.108 / +0.225 ns |

整机最终 PASS：WNS **+2.498 ns**、DSP **136/220**、BRAM36 **69/140**、LATCHES=0、
DRC_BLOCKING=0；CDC-15=73、CDC-3=12、CDC-6=7 全部命中 allowlist。基线 `ENABLE_COP=0`
PASS、WNS +6.840 ns。OOC 与整机资源不能相加冒充整机结论；板级仍未验证。

## 6. 经验沉淀

- 触发条件：门禁脚本存在但从未在目标 EDA 工具里真跑。
- 排查步骤：先修工具路径与约束语法，再看 BRAM 推断/资源，最后才看整机时序；
  “综合完成”不等于门禁 PASS，必须看 check_timing/DRC/CDC。
- 适用范围：所有 OOC→整机推进；换器件/时钟档要重新出报告。
#skill候选
