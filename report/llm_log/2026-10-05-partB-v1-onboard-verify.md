# [2026-10-05] 协作记录：Part B v1 三级流水 Windows 复验与上板（XSim 对拍 + 双频构建 + JTAG 实测）

> 标签：#riscv #验证 #hardware #build #工具链
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：被测 `dev/rtl@85b94a5`（Part B 收官 `3a6ad00`）；证据随本条记录入库
> 用途：验证线按 `docs/partB-rtl-handoff.md` 完成 v1 的 Windows 复验与真实上板；记录 125 MHz 未收敛与长构建超时处置

## 1. 任务与初始提示词

> "我们的项目又更新了许多 rtl 部分的文件，三级流水线完成，但是优化程度不如预期，我现在要进行这部分对应的上板验证工作，请你带领着我完成工作"

被测件 = `dev/rtl` 的 v1 三级流水核（`design_v1.md` 冻结契约，`ENABLE_FORWARDING` 两档）。团队交接单明确：**Windows 复验（XSim / Vivado 双频 / PYNQ-Z2 实机）待验证，不得写"v1 已上板"**。

## 2. 模型第一版方案

1. 在 `dev/rtl@85b94a5` 上建临时验证分支；
2. 功能对拍：`sim\scripts\run_riscv_xsim.bat all`（本机无 iverilog，用团队 Windows XSim 脚本）；
3. Vivado 双频构建：`build_soc.tcl -tclargs 40` 与 `-tclargs 125`，核对两时钟/未约束端点/WNS/DRC；
4. 上板：下 40 MHz 位流，观察 `LED=1101`；
5. 归档证据 + 写记录 + 提交 `dev/verify`。

## 3. 失败现象（真实偏差）

1. **125 MHz 档时序远未收敛**：布线后正式 `WNS = −8.044 ns / TNS = −14009.521`，失败端点 5740（phys_opt 期间估计约 −7.3）；`check_timing` 时钟检查全 0，纯数据路径太慢。布线报 `21749 pins with tight setup and hold constraints`，极慢。
2. **长构建阻塞式命令超时**：125 MHz 构建跑过约 10 分钟被平台中断；**但 Vivado 子进程仍在后台运行**（PID 27396 持续占用 CPU），表现为"命令结束了、进程还在、产物半截"。
3. 本机无 iverilog/MSYS2 → 不能用 `run_iverilog.sh`；改用团队提供的 `run_riscv_xsim.bat`（顺带形成 XSim/iverilog 双工具对拍）。
4. 板卡在归档时段一度断开（此前命令行抓下载日志失败），后重连完成上板。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 无 iverilog | 本机只有 Vivado，用团队 Windows XSim 脚本 | 改用 `run_riscv_xsim.bat all` | ✅ `PASS: RISC-V XSim mode all`（5 个 tb 全 PASS） |
| 2 | 125 MHz 构建反复"卡住/超时" | 时序太紧导致布线极慢；且中断未杀子进程，残留在后台 | `Stop-Process` 结束残留 vivado；确认 125 失败 | ✅ 清理完成，125 记 FAIL |
| 3 | 125 明显不达标 | 布线后 WNS = −8.044、5740 失败端点，注定门禁 FAIL | 按交接单**保留 FAIL、不生成/不使用该档位流** | ✅ 保留完整 impl/timing/DRC 报告与日志，无 `.bit` |
| 4 | 上板 LED 现象 | 需与 v0 语义对照 | 下 40 MHz 位流，观察 LED | ✅ `1101` 静止；BTN0 `0000→0001`（契约允许） |

## 5. 最终结论

- **功能（XSim）**：`PASS: RISC-V XSim mode all`；转发档气泡 0/4/5/0（127 周期）、无转发档 14/10/15/3（175 周期）→ 转发有效、语义不变。
- **时序（Vivado）**：40 MHz 档 `BUILD PASSED`，**WNS +4.850 ns**，0 Error/0 Critical DRC，LUT 6442 / FF 791 / RAMB36 8；**125 MHz 档 FAIL（布线后 WNS = −8.044 / TNS −14009 / 5740 失败端点），按规矩不产出位流**。
- **Fmax（OOC，约束递减收敛）**：v1 `core_top` ≈ **81 MHz**（12.5 ns WNS +0.312 与 12.15 ns WNS −0.152 之间过零，约 12.3 ns），对比 v0 基线 **86.8 MHz** 略降；原始日志 `fmax/v1_*.log`。
- **上板（40 MHz）**：`PROGRAM PASSED`，**LED=`1101` 静止**，BTN0 `0000→0001`（与 v0 一致，契约 §4 允许）→ **v1 已上板 PASS**。
- 证据归档：`data/logs/2026-10-05-partB-v1-onboard/`（`xsim/`、双频 `reports/`、构建与下载日志）；上板记录 `board/logs/2026-10-05-partB-v1-onboard/README.md`。
- 已知（团队/bench）：转发 CPI 增益 8.14%（原 25% 门禁 FAIL 保留，新门禁 ≥8.0%）。

## 6. 经验沉淀

- 触发条件：在本地复验/构建一个已知时序紧张的大设计，或用阻塞式命令跑长任务 #skill候选
- 排查步骤：
  1. **长构建不要阻塞等待**：优先在你自己的终端后台跑，或后台启动 + 轮询日志；命令被中断≠任务停止，要检查并 `Stop-Process` 清理残留 Vivado（`Get-Process vivado`）。
  2. **失败门禁要"如实保留"**：125 MHz 未收敛就记 FAIL、不生成也不冒用该档位流（`partB-rtl-handoff.md` 门禁铁律）。
  3. **缺工具先找团队脚本**：本机无 iverilog 时用团队 `run_riscv_xsim.bat`，还顺带得到跨工具对拍。
  4. **"优化不改语义"的板级判据**：同一固件、不同微架构，板上现象应与基线一致（本例 LED=`1101`）；软复位后依赖旧 DMEM 的行为属契约允许，不算回归。
  5. **Fmax 用"约束递减收敛"测**：单点约束下工具优化强度不同，报告值会漂（本例 73.2→82.0→83.8）；必须逐轮收紧周期直到 WNS 由正转负，取过零点为 Fmax（v1≈81 MHz）。
- 适用范围（换题目/换板卡是否成立）：成立；任何"功能仿真 + 时序构建 + 真实上板 + Fmax 收敛测量"的验证、以及长 EDA 任务的执行方式均适用。
