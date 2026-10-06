# Part B v1（三级流水 + 转发）Windows 复验与上板证据（2026-10-05）

> 用途：验证线按团队交接单 [`docs/partB-rtl-handoff.md`](../../../docs/partB-rtl-handoff.md) 对 `dev/rtl` 的 v1 核做 **Windows 侧复验**：XSim 功能对拍 → Vivado 双频构建 → PYNQ-Z2 上板。
> 契约唯一权威：[`src/riscv/design_v1.md`](../../../src/riscv/design_v1.md)；验收对照：[`docs/partB-verify-plan.md`](../../../docs/partB-verify-plan.md)。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `dev/rtl@85b94a5`（Part B 收官提交 `3a6ad00`：radix-4 + 双时钟 handoff） |
| 契约 | `design_v1.md`（三级 IF/ID+EX/MEM+WB，`ENABLE_FORWARDING` 开关） |
| 验证人 | 验证线 ｜ 日期 2026-10-05 |
| 工具 | Vivado 2026.1；XSim；器件 `xc7z020clg400-1` |

## 结果 1：功能对拍（XSim）PASS

命令（仓库根，无需 iverilog）：
```bat
sim\scripts\run_riscv_xsim.bat all
```
输出：
```text
PASS: radix-4 multiply, division, boundaries and handshake
PASS: fwd_test 结果全对；气泡 A/B/C/D = 0/4/5/0，总周期 127，总气泡 13      (ENABLE_FORWARDING=1)
PASS: fwd_test 结果全对；气泡 A/B/C/D = 14/10/15/3，总周期 175，总气泡 61   (ENABLE_FORWARDING=0)
PASS: v1 muldiv mode=1 ... stalls=0/0/0
PASS: v1 muldiv mode=0 ... stalls=2/1/1
PASS: RISC-V XSim mode all
```
原始日志：`xsim/`（5 个 tb 的 `*-elab.log` 与 `*.log`）
> 与 RTL 线 iverilog 结论一致（双工具对拍）：转发档气泡显著少于无转发档。

## 结果 2：40 MHz 安全档构建 BUILD PASSED

命令：`vivado -mode batch -source build/build_soc.tcl -tclargs 40`

| 项 | 实测 |
|:---|:---|
| 时钟 | `sys_clk_125` 8 ns、`core_clk_40` 25 ns 均存在且周期正确 |
| 时序 | **WNS +4.850 ns**；`All user specified timing constraints are met`；未约束端点 0 |
| DRC | 0 Error / 0 Critical Warning |
| 资源 | Slice LUT 6442（12.11%）、Slice Register 791（0.74%）、Block RAM Tile 8（5.71%） |
| 位流 | `build/run/soc_40mhz/pynq_z2_soc_40mhz.bit`，4,045,766 B，SHA256 `5AA58E39451CA7F31EB46545988FDFA9CE556AE17C539932EDA8CAE38CDFB4F4` |

报告副本：`reports/soc_40mhz/`

## 结果 3：125 MHz 目标档构建 FAIL（时序门禁不过）

命令：`vivado -mode batch -source build/build_soc.tcl -tclargs 125`

- 布线极为吃力（日志 `There are 21749 pins with tight setup and hold constraints`）；
- 布线后正式时序：**WNS = −8.044 ns / TNS = −14009.521，失败端点 5740**（phys_opt 期间估计约 −7.3）；
- `check_timing`：`no_clock / constant_clock / unconstrained_internal_endpoints / generated_clocks` **均为 0**（时钟没问题，纯数据路径太慢）；
- 按交接单：**保留原始 FAIL，不生成、不使用 125 MHz 位流**（无 `.bit`）；
- **最差路径**（`reports/soc_125mhz/soc_timing_worst_paths.rpt`）：`u_soc/u_core/u_mem_wb/mem_addr_reg[3]` → DMEM 读 → 核内逻辑 → `u_soc/u_core/u_pc/pc_reg[21]`，Data Path **15.924 ns**（logic 4.802 / route 11.122 = **69.84%**），Logic Levels 21；**路径中不含乘法器**——失败主因是"访存 → PC"的组合路径与高布线占比，**不应归因于 Radix-4 乘法器**；
- 报告：`reports/soc_125mhz/`（synth + impl + timing/DRC）+ `build_soc_125mhz.log`。

## 结果 4：真实上板（40 MHz 位流）PASS

命令：`board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
输出：`FOUND: xc7z020_1` → `PROGRAM PASSED`（日志 `program_soc_40mhz.log`）

板上现象：
| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（契约 §4 允许） | `0001`（与 Part A 一致） |

## 结果 5：v1 核 OOC Fmax（约束递减收敛）——区分"约束通过频率"与"Slack 外推估计"

方法：`build/build_fmax.tcl`（OOC post-route、默认 directive、同器件/Vivado）。脚本输出的 `Fmax = 1/(period − WNS)` 是**单点 Slack 外推估计**，**不等于"在该频率下真的通过"**。

| 约束 period (ns) | 约束频率 (MHz) | WNS (ns) | 该约束是否通过 | 脚本外推 Fmax (MHz) |
|:---:|:---:|:---:|:---:|:---:|
| 15.000 | 66.67 | +1.342 | 通过 | 73.2 |
| 13.700 | 72.99 | +0.464 | 通过 | 75.6 |
| 13.200 | 75.76 | +0.301 | 通过 | 77.5 |
| **12.500** | **80.00** | **+0.312** | **通过（最低通过约束点）** | 82.0 |
| **12.150** | **82.30** | **−0.152** | **失败** | 81.3 |
| 10.000 | 100.00 | −1.935 | 失败 | 83.8 |

- **可称为"实测"的只有约束通过/失败点**：**80 MHz（12.5 ns）约束实际通过**；**82.30 MHz（12.15 ns）约束实际失败**。证据：`reports/fmax/v1_12p5ns/`、`reports/fmax/v1_12p15ns/`（`timing_impl.rpt` / `timing_worst_paths.rpt` / `utilization_impl.rpt` / `design_analysis_impl.rpt`；**OOC 脚本不生成 check_timing，check_timing 只在 SoC 构建里**）。
- **"约 81 MHz" 只是过零点的收敛估计**（来自单点 Slack 外推与线性插值），**不得称为"实测通过频率"，更不是"已验证的上板频率"**；不同约束会重新布局布线，插值不等于在该频率下做过一次验证。
- 这是**核 `core_top` 的 OOC 频率**，与**完整 SoC**（含 MMCM / IO / 存储；40 / 125 MHz 两档）**分开表述**，两者不可混用。
- 对比 v0 报告基线 **86.8 MHz**（tag `partA-v0`，同法 OOC）：**v1 估计低于 v0**，对应 plan / `design_v1.md` 的"**主频提升或持平**"条款**尚未满足**，属**未决验收项**，交 RTL / 负责人处理（**不能用 40 MHz SoC WNS≥0 代替这个比较门禁**）。

## 结论（按复核意见限定）

- **上板**：**40 MHz 构建与上板验证通过**（LED=`1101` 静止，BTN0 `0000→0001`）；**125 MHz 未通过**（WNS −8.044），按交接单未生成 / 未使用该档位流。
- **核 OOC 频率**：**80 MHz 约束点通过**、**82.30 MHz 约束点失败**；**"最高频率约 81 MHz" 为 Slack 外推估计**，非实测通过频率。核 OOC 与完整 SoC 频率分开表述。
- **主频比较门禁**：v1 估计低于 v0 报告基线 **86.8 MHz**，与"主频提升或持平"条款存在**未满足项**，交 RTL / 负责人处理（不得用 40 MHz WNS≥0 代替）。
- **功能**：XSim 两档全 PASS（"优化不改语义"）。
- **CPI（分类记账，不得混记）**：旧 **Radix-2** 工作点转发增益 **8.14%**（原 25% 门禁 FAIL，历史保留）；当前 **Radix-4** 工作点转发增益 **10.20%**（门禁 ≥8.0%）；固定转发的**乘法器**收益 **21.95%**；相对原始 nofwd 的**组合**收益 **28.30%**。来源：`data/logs/2026-10-05-partB-radix4-cycle-breakdown/summary.txt`、`data/logs/2026-10-05-partB-v1-coremark-cpi/summary.txt`。**本次验证未做完整 CoreMark XSim 复测**（仅做了核/SoC 功能与 40 MHz 上板）。
- **125 MHz 失败归因**：最差路径在"`u_mem_wb/mem_addr_reg[3]` → DMEM 读 → 核内 → `u_pc/pc_reg[21]`"，布线占比 **69.84%**，**与 Radix-4 乘法器无关**；后续诊断应针对"访存 → PC"路径。
- **验收状态**：完整**性能与主频比较验收尚有未决项**。

## 复现步骤

1. `git switch` 到 `dev/rtl@85b94a5`
2. 功能：`sim\scripts\run_riscv_xsim.bat all`
3. 构建：`vivado -mode batch -source build/build_soc.tcl -tclargs 40`（及 `125`）
4. Fmax：`vivado -mode batch -source build/build_fmax.tcl -tclargs core_top <label> <period_ns> src\riscv`（逐轮收紧周期至过零）
5. 上板：`board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
6. 观察 LED = `1101`

## 边界

- 位流不入库（`.gitignore *.bit`）；`build/run` 为忽略目录
- `reports/` 仅为证据副本；不修改 RTL 线在 `dev/rtl` 的正式报告与 RTL/tb
- 长构建曾在阻塞式命令下超时（125 MHz），详见协作记录 `report/llm_log/2026-10-05-partB-v1-onboard-verify.md`
