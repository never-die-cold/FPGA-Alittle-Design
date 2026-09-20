# PYNQ-Z2 LED smoke test 上板实测记录（2026-09-20）

> 用途：`board/smoke_test/` LED 流水灯在**真实板卡**上的下载与验收记录；补齐 `dev/rtl → main` 的「真实上板验证」遗留项。
> 约定：按 `board/README.md`，实测记录只追加不改；本文件为首次上板记录。
> 上游自检证据（仿真 + Vivado 构建）见 [`data/logs/2026-09-20-pynq-z2-smoke-vivado/`](../../../data/logs/2026-09-20-pynq-z2-smoke-vivado/README.md)。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测件 | `board/smoke_test/`（PR #15，merge `93eeb97`） |
| 被测源码 commit | `main@2bf0e45` |
| 记录人 | waltercooper |
| 日期 | 2026-09-20 |

## 硬件、连接与「两种下载」的区别（先看这里）

项目里有两个容易混淆的「下载」，本记录对应的 PL 配置用的是 **JTAG**：

| 名称 | 作用 | 本次情况 |
|:---|:---|:---|
| **SD 卡烧录** | 把 PYNQ Linux 镜像写入 SD 卡，让板子能启动（PS 侧） | 队友已完成，板子从 SD 卡启动 PYNQ v3.x / Ubuntu 22.04 |
| **JTAG 下载** | 通过板载 USB-JTAG 把 `.bit` 配置进 **PL（可编程逻辑）** | **本次上板验证使用的方式**（Vivado hw_manager） |
| （备选）PYNQ 加载 | 板内 Linux 用 `Bitstream.download()` 配置 PL | 本次未用，列出仅作对照 |

> 两者不冲突：SD 卡负责「板子能不能开机」，JTAG 负责「PL 里烧的是哪个设计」。本记录验证的是后者。

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C），全队共用 1 块
- 连接：板载 Micro-USB（JTAG/UART）直连本机 Windows；PYNQ Linux 串口在 **COM4（ttyPS0，115200）**
- 供电 / 启动：正常 SD 卡启动（PYNQ v3.x，Ubuntu 22.04）
- 本机：Vivado 2026.1（`D:\vivado\2026.1\Vivado\bin\vivado.bat`）

## 1. 构建 bitstream

```powershell
New-Item -ItemType Directory -Force C:\fpga_build\pynq_z2_smoke | Out-Null
& D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch `
  -source "D:/Desktop/contests/2026fpga/FPGA-Alittle-Design/board/smoke_test/scripts/build.tcl"
```

结果：`BUILD PASSED`；产物：

| 项 | 值 |
|:---|:---|
| 路径 | `C:/fpga_build/pynq_z2_smoke/run_20260920_211712_22288/pynq_z2_smoke.bit`（不入库，`.gitignore *.bit`） |
| SHA256 | `AA65F0B1D1D0DF42277B80686584D810F8228847ED4537C266B6187F4951C4B1` |
| 大小 | 4,045,772 B |

## 2. JTAG 下载 bitstream 到 PL（本次方式）

用 `program_pl.tcl`（临时脚本，放构建目录，不入库）：

```tcl
open_hw_manager
connect_hw_server
open_hw_target

set dev ""
foreach d [get_hw_devices] {
    puts "FOUND: $d  PART=[get_property -quiet PART $d]"
    if {[string match "xc7z020*" [get_property -quiet PART $d]]} { set dev $d }
}
if {$dev eq ""} { puts "*** NO xc7z020 FOUND ***"; close_hw_manager; exit 1 }
puts "PROGRAMMING: $dev"
current_hw_device $dev
refresh_hw_device -update_hw_probes false $dev
set_property PROGRAM.FILE {C:/fpga_build/pynq_z2_smoke/run_20260920_211712_22288/pynq_z2_smoke.bit} $dev
program_hw_devices $dev
puts "*** PL PROGRAMMED ***"
close_hw_manager
```

```powershell
& D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source C:\fpga_build\program_pl.tcl
```

关键输出（节选）：

```text
FOUND: arm_dap_0   PART=arm_dap
FOUND: xc7z020_1   PART=xc7z020
PROGRAMMING: xc7z020_1
INFO: [Labtools 27-3164] End of startup status: HIGH
*** PL PROGRAMMED ***
```

> **踩坑记录**：Zynq 的 JTAG 链上同时存在 `arm_dap_0`（ARM 调试口）与 `xc7z020_1`（PL）。用 `[lindex [get_hw_devices] 0]` 会取到 `arm_dap_0`，报 `ERROR: [Labtoolstcl 44-10] Device arm_dap_0 is not programmable`。必须按 `PART` 过滤出 `xc7z020_1` 再 `program_hw_devices`。

## 3. 上板验收（肉眼观察，非仿真）

| 项 | 期望（`board/smoke_test/README.md` 第 5、6 步） | 实测 |
|:---|:---|:---:|
| LED 顺序 | 同时仅一个亮，`LED0→LED1→LED2→LED3→LED0`，每步约 0.5 s，连续 ≥3 圈 | ✅ |
| BTN0 复位 | 按住 BTN0 时 LED0 保持亮；松开后从 LED0 重新计时并继续循环（重复 2 次） | ✅ |

**结论：上板 PASS。** 仿真 PASS 不能代替上板，本记录以真实板卡观察为准。

## 4. 结论

LED smoke test 通过「仿真（iverilog）→ 构建（Vivado BUILD PASSED）→ 真实上板（JTAG 下载 + 肉眼验收）」全链路；`dev/rtl → main` 的**真实上板验证遗留项已闭环**。

## 5. 复现步骤

1. 板卡 Micro-USB 接本机 → 装 Digilent 线缆驱动（如 Vivado 未识别目标）
2. 跑第 1 节构建命令，确认 `BUILD PASSED`
3. 跑第 2 节下载脚本（`DEV` 选 `xc7z020_1`）
4. 肉眼验证第 3 节两行现象

## 边界

- `board/smoke_test/`（RTL/XDC/脚本）归 **RTL 线**维护；本记录归 `board/`（验证线归档边界 + 上板执行人）
- bitstream 与 Vivado 工程不入库（`.gitignore *.bit`）；原始报告由构建脚本写在 `C:\fpga_build` 之外，需要时另存
- 本记录用 JTAG 配置 PL；板子系统启动依赖队友完成的 SD 卡烧录（PYNQ 镜像），两者互不替代
- 本次只配置 PL，不烧 Flash，断电后需重新下载
- 上板时钟方案（板载 125 MHz vs v0 Fmax 86.8 MHz）与本测试无关，仍待拍板（`src/riscv/design_v0.md` §10）

## 关联

- `board/smoke_test/README.md`（被测件步骤与验收清单）
- `data/logs/2026-09-20-pynq-z2-smoke-vivado/README.md`（仿真 + 构建门禁证据）
- `report/llm_log/2026-09-20-pynq-z2-smoke-verification.md`（PR #15 独立复核）
