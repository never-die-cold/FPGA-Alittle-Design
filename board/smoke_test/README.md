# PYNQ-Z2 最小流水灯上板测试

本例为用户明确批准的目录规范例外：源码、约束、验证和构建脚本均独立放在
`board/smoke_test/`。只读取本例文件，不修改项目正式 RTL、原有构建脚本、
约束或根 README，也不依赖 RISC-V 核、PS 软件或 PYNQ overlay。

目标器件固定为 `xc7z020clg400-1`。使用板载 125 MHz PL 时钟，默认
`DIV_CYCLES=62500000`，每 0.5 秒移动一次，2 秒一圈：
`0001 -> 0010 -> 0100 -> 1000 -> 0001`（按 `led[3:0]` 表示）。
实现为计数器时钟使能，所有寄存器仍使用原始 125 MHz 时钟。

## 文件作用

| 文件 | 作用 |
|---|---|
| `rtl/pynq_z2_smoke_top.v` | 可综合 Verilog 顶层、参数化计数器、one-hot LED、BTN0 复位同步 |
| `constraints/pynq_z2_smoke.xdc` | 官方引脚、电压标准、8 ns 时钟及本设计的外部异步路径例外 |
| `sim/pynq_z2_smoke_tb.v` | 自动时钟/复位、逐周期检查启动、保持时间、循环顺序和中途复位 |
| `sim/run_iverilog.sh` | 运行分频值 1、2、5、8 的自检，任一失败返回非零 |
| `scripts/build.tcl` | 创建工程、综合、实现、约束/时序/DRC 检查、生成 bitstream |
| `.gitignore` | 忽略本例 `.sim_build/` 内的仿真产物 |
| `README.md` | 来源、复现及人工上板验收说明 |

没有创建 `program.tcl`；下载仅按下文在 Hardware Manager 中手动执行。

## 约束来源（2026-09-20 核验）

- 官方索引：[PYNQ Board Settings — XDC constraints file](https://pynq.readthedocs.io/en/v3.1/overlay_design_methodology/board_settings.html)。
- 索引中的 [PYNQ-Z2 Master XDC ZIP](https://dpoauwgwqsy2x.cloudfront.net/Download/pynq-z2_v1.0.xdc.zip)。
- 实际解包读取的成员名：`PYNQ-Z2 v1.0.xdc`。
- 原始成员字节的 SHA256：`07441e999bac956c77e78091c782cade278efc5a78affc51e5b12b4800b1fe73`。
- 按钮/LED 极性：[TUL PYNQ-Z2 Reference Manual v1.0](https://www.e-elements.com.tw/wp-content/uploads/2021/08/pynqz2_user_manual_v1_0.pdf)，第 14 节，表 9、11（PDF 第 20、21 页；供应商托管的 TUL 手册）。

| 顶层端口 | 官方信号 | PACKAGE_PIN | IOSTANDARD | 含义 |
|---|---|---|---|---|
| `clk` | `sysclk` | H16 | LVCMOS33 | 125 MHz，周期 8 ns，波形 `{0 4}` |
| `led[0]` | `led[0]` | R14 | LVCMOS33 | 用户 LED0，高电平亮 |
| `led[1]` | `led[1]` | P14 | LVCMOS33 | 用户 LED1，高电平亮 |
| `led[2]` | `led[2]` | N16 | LVCMOS33 | 用户 LED2，高电平亮 |
| `led[3]` | `led[3]` | M14 | LVCMOS33 | 用户 LED3，高电平亮 |
| `btn0` | `btn[0]` | D19 | LVCMOS33 | BTN0，按下为高电平 |

XDC 仅启用官方 Clock、LEDs、Buttons 中对应条目，重命名 `sysclk` 和
`btn[0]` 为顶层端口；引脚、IOSTANDARD、时钟周期没有自行推测。
新增的 `set_false_path` 属于本设计约束：BTN0 只接复位同步链的异步置位端；
LED 为无外部采样时钟的人眼指示输出，不捏造外部 input/output delay。
内部寄存器间路径仍检查 125 MHz 下的 setup/hold。

复位同步链异步置位、两拍释放，主逻辑同步复位；初始化值使用 Xilinx FPGA
可综合的寄存器 INIT，使下载后不按按钮也能启动。BTN0 保持按下时 LED0 亮，
松开经过两拍释放后重新计时。这里未做按键消抖，抖动可能重复复位，但最终
松开后正常运行。使用用户按钮 **BTN0**，不要用会清除 PL 配置的 PROG 按钮代替。
参数取正整数；`DIV_CYCLES=1` 也有合法的一位计数器。

## Icarus Verilog 自动仿真

前置：PATH 内存在 `iverilog`、`vvp`，以及 Bash、`mktemp`。
从仓库根目录执行：

```bash
bash board/smoke_test/sim/run_iverilog.sh
```

从任意工作目录执行时提供脚本的绝对路径，例如：

```bash
bash /home/jianglibo/FPGA-Alittle-Design/board/smoke_test/sim/run_iverilog.sh
```

脚本自行定位源文件，使用 `-P` 覆盖 testbench 参数并传给 DUT，覆盖 1、2、5、8
四个分频值。每组检查上电启动、24 次 LED 移动、每个间隔的保持、中途复位和恢复，
包含超时保护。通过打印 `TEST PASSED`；失败打印 `TEST FAILED` 并返回非零。
RTL 是 Verilog；仿真启用 `-g2005-sv` 仅用于 testbench 的 `$fatal(1)` 非零退出。
输出保存在本目录 `.gitignore` 忽略的 `.sim_build/run.XXXXXX/`，不覆盖旧运行，
脚本不删除文件。

## Windows Vivado 构建

本阶段没有实际运行 Vivado，尚未验证综合、实现或 bitstream。
需要 Windows Vivado 和 Zynq-7000 / XC7Z020 器件支持；无需安装 board files，
因为工程直接指定 part 并读取已核实 XDC。

打开已配置 Vivado PATH 的 Windows 命令提示符，将下面源代码路径替换为
Windows 上的真实仓库位置。先切换到输出目录，使 Vivado 自身的日志、journal
及 `.Xil` 也留在仓库之外：

```bat
if not exist C:\fpga_build\pynq_z2_smoke mkdir C:\fpga_build\pynq_z2_smoke
cd /d C:\fpga_build\pynq_z2_smoke
vivado -mode batch -source "C:/path/to/FPGA-Alittle-Design/board/smoke_test/scripts/build.tcl"
```

每次创建 `C:/fpga_build/pynq_z2_smoke/run_<日期时间>_<进程号>/`，保存工程、
运行产物及 `timing.rpt`、`utilization.rpt`、`drc.rpt`。不覆盖已有构建目录。
流程先综合、再实现至 route_design；检查运行状态、六个端口的官方映射和电压标准、
8 ns 时钟及寄存器时钟覆盖、setup/hold/pulse-width 时序总结和严重 DRC。
任一步失败均打印 `BUILD FAILED`、以非零状态退出，不生成新的 bitstream。
检查成功后才执行 `write_bitstream`，确认文件非空并打印：

```text
BUILD PASSED
BITSTREAM: C:/fpga_build/pynq_z2_smoke/run_.../pynq_z2_smoke.bit
```

版本导致报告格式无法识别也会停止，需查看报告和错误后适配，不能绕过时序门槛。
该脚本不打开 Hardware Manager，也不会自动连接或配置任何开发板。

## 手动下载与验收

1. 在实际 PYNQ-Z2 上核对板型；按 TUL 手册设置供电和启动模式，连接板载 USB-JTAG。
2. 完成上述构建并确认 `BUILD PASSED`，记下本次 `BITSTREAM` 的完整路径。
3. 在 Vivado GUI 手动打开 Hardware Manager，Open Target，连接目标板。
4. 核对检测到的是目标板的 `xc7z020` 器件；选择 Program Device，选择本次 `.bit`。
   此设计没有 ILA，不需 probes 文件；人工确认后点击 Program。
5. 观察四个单色用户 LED：同时仅一个亮，LED0、LED1、LED2、LED3 顺序移动，
   每步约 0.5 秒，连续观察至少三圈。
6. 按住 BTN0 时 LED0 保持亮；松开后从 LED0 重新计时并继续循环，重复验证两次。
7. 记录日期、板卡、供电/连接、源码版本、本次 bitstream 路径和现象。

满足第 5、6 步才算上板通过；仿真成功不能代替上板结果。下载只配置本次 PL，
不进行 Flash 烧写；断电后需要重新下载。这个例子不会修改项目正式 RTL。
