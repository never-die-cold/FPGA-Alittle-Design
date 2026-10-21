# [2026-10-21] 协作记录：K4 交付 Vivado 40/100 MHz 门禁脚本与 Windows 检查清单

> 标签：#coprocessor #build #Vivado #时序 #门禁
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`c9c3c97` `b821aa1`

## 1. 任务与初始提示词

K4：在现有 build 脚本风格下新增 Vivado Tcl，做综合、实现、报告导出；派生时钟 XDC 必须与
RTL 分频参数同档（默认 40 MHz 安全档），报告目录按档位分开；产出 Windows 侧检查清单，
写清命令、LUT/FF/DSP/BRAM 占用、WNS、未约束路径、判定标准与失败回滚。
**严禁声称任何综合/时序结果**，一律 UNVERIFIED；只提交脚本/约束/模板，不提交 `.xpr` 与 report。

## 2. 模型第一版方案

`build/build_coprocessor_gate.tcl` 接 `-tclargs <40|100> <compute|storage>`：
读入 `src/coprocessor/*.v`，OOC 综合/实现，按档位写
`build/reports/coprocessor/<freq>mhz/<target>/`；自动判定 WNS≥0、`check_timing` 四项为 0、
DRC 无 Error/Critical Warning。`coprocessor_board_clock.xdc` 按 125 MHz×8÷25=40 MHz 派生；
`.gitignore` 排除 `.xpr`、run/report 与 bitstream。

## 3. 失败现象

1. WSL 无 Vivado，本轮无法执行任何综合/实现/时序命令。
2. 若把 `.xpr`、`.dcp`、report 一起提交，会把本机生成物和未验证结论带进仓库。
3. 100 MHz 若失败，不能覆盖或污染 40 MHz 的安全档结论。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | WSL 无 Vivado | 不能产出时序结论 | 只交脚本/约束/清单，全部标 UNVERIFIED | 未越权宣称 |
| 2 | 生成物可能入库 | 仓库卫生风险 | `.gitignore` 排除 `.xpr`/run/report/bit | 只提交 5 个文本文件 |
| 3 | 100 MHz 失败会污染 40 MHz | 档位未隔离 | 报告与 checkpoint 按 `40mhz/100mhz` 分目录 | 失败可独立回滚 |
| 4 | 只打印报告不算门禁 | 缺少自动判定 | Tcl 内检查 WNS/check_timing/DRC 并 error 退出 | 脚本可失败得可见 |

## 5. 最终结论

K4 交付：`build/build_coprocessor_gate.tcl`、三份 XDC、`docs/coprocessor-vivado-checklist.md`。
当前真实状态：**UNVERIFIED，需 Windows 侧 Vivado 执行**。`compute`/`storage` 是两个独立 OOC，
只能分别证明计算控制逻辑与 K3 存储可实现；资源相加不能冒充整机布局布线。默认 40 MHz；
100 MHz 仅作可选档，失败不回写 40 MHz 结论。

## 6. 经验沉淀

- 触发条件：在没有目标工具（Vivado）的环境里仍要推进交付。
- 排查步骤：只交可复现脚本与约束，把判定条件写进 Tcl（WNS/未约束/DRC/CDC），
  报告按档位隔离；明确“OOC ≠ 整机”，不把脚本存在当成综合通过。
- 适用范围：任何跨 Windows/Linux 的 EDA 门禁；换器件需改 part 与 XDC，不沿用结论。
#skill候选
