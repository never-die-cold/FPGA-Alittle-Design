# Part B T2 SoC 构建与上板验证（2026-10-06）

> 用途：验证线对 `dev/rtl@b93afaa`（T2：`id_ex` 分支比较解耦 ALU + `core_top` 转发接线简化）做 Windows 侧复验：XSim 功能回归 → 40 MHz SoC 构建 → JTAG 上板。
> 核 OOC Fmax（T2）另见 [`../2026-10-06-partB-t2-fmax/`](../2026-10-06-partB-t2-fmax/README.md)（11.52 ns 通过 / 10 ns 差 9 ps）。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `dev/rtl@b93afaa`（T2；未并入 main） |
| 工具 | Vivado 2026.1；器件 `xc7z020clg400-1` |
| 验证人 | 验证线 ｜ 日期 2026-10-06 |

## 结果 1：功能回归（XSim）PASS

命令：`sim\scripts\run_riscv_xsim.bat all`
输出：`PASS: RISC-V XSim mode all`（`tb_muldiv`、`tb_core_fwd`(fwd/nofwd)、`tb_core_v1_muldiv_flow`(fwd/nofwd) 全 PASS）
原始日志：`xsim/`
> T2 改了 RTL/tb，本次为独立功能复跑，结论：**T2 未破坏功能语义**。

## 结果 2：40 MHz SoC 构建 BUILD PASSED

命令：`vivado -mode batch -source build/build_soc.tcl -tclargs 40`

| 项 | 实测 |
|:---|:---|
| 时钟 | `sys_clk_125` 8 ns、`core_clk_40` 25 ns 均存在且周期正确 |
| 时序 | **WNS +7.388 ns**；`All user specified timing constraints are met`；未约束端点 0 |
| DRC | 0 Error / 0 Critical Warning |
| 资源 | Slice LUT 6325（11.89%）、Slice Register 749（0.70%） |
| 位流 | `build/run/soc_40mhz/pynq_z2_soc_40mhz.bit`，4,045,766 B，SHA256 `E7BB4041FD13D3C4FE28FCEC797A29E2F8180525F28AB63842FA87314F7761E5` |

报告副本：`reports/soc_40mhz/`；构建日志：`build_soc_40mhz.log`
> 对比 T2 前（`85b94a5`，40 MHz WNS +4.850）：**+7.388 ns，明显改善**，与 T2"降深度"一致。

## 结果 3：真实上板（40 MHz 位流）PASS

命令：`board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit`
输出：`FOUND: xc7z020_1` → `PROGRAM PASSED`（日志 `program_soc_40mhz.log`）

板上现象（与 Part A / 前次 v1 完全一致）：
| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（契约 §4 允许） | ✅ 与之前一致 |

## 结论（限定口径）

- **T2 代码：XSim 功能回归 PASS；40 MHz SoC 构建通过（WNS +7.388）；40 MHz 位流真实上板观察到 LED=`1101`（静止）→ 40 MHz 构建与上板验证通过。**
- 本次**只做 40 MHz 档**；SoC 125 MHz 档未做（核 OOC Fmax 见 `../2026-10-06-partB-t2-fmax/`）。
- 核 OOC 频率与完整 SoC 频率**分开表述**；外推 Fmax 仅作参考。

## 复现

```bat
sim\scripts\run_riscv_xsim.bat all
vivado -mode batch -source build\build_soc.tcl -tclargs 40
board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit
```

## 边界

- 只读复验，不改 RTL / tb；`b93afaa` 未并入 main
- 位流不入库（`.gitignore *.bit`）；`build/run` 为忽略目录；关键报告已复制入本目录
