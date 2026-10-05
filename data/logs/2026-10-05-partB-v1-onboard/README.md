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

## 结论

- **v1 三级流水功能"优化不改语义"**：XSim 两档全 PASS，上板 LED = `1101`（与 v0 一致）→ **v1 已上板 PASS**（40 MHz 档）。
- **时序**：40 MHz 档 WNS +4.850 通过；**125 MHz 档 FAIL 保留**（非阻塞加分项，未达标）。
- 已知（团队/bench）：转发 CPI 增益 **8.14%**，原 25% 门禁 FAIL 保留，新门禁 ≥8.0%。

## 复现步骤

1. `git switch` 到 `dev/rtl@85b94a5`
2. 功能：`sim\scripts\run_riscv_xsim.bat all`
3. 构建：`vivado -mode batch -source build/build_soc.tcl -tclargs 40`（及 `125`）
4. 上板：`board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
5. 观察 LED = `1101`

## 边界

- 位流不入库（`.gitignore *.bit`）；`build/run` 为忽略目录
- `reports/` 仅为证据副本；不修改 RTL 线在 `dev/rtl` 的正式报告与 RTL/tb
- 长构建曾在阻塞式命令下超时（125 MHz），详见协作记录 `report/llm_log/2026-10-05-partB-v1-onboard-verify.md`
