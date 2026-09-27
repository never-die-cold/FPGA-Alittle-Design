# Part A SoC 上板验证证据（2026-09-26）

> 用途：独立验证 `dev/rtl` 待合并提交 `db9fe33`（Part A SoC 上板准备与 40 MHz 时序收敛）的**仿真 / 构建 / 真实上板**证据。
> 被测件决策与上板判据见 `report/llm_log/2026-09-23-partA-soc-onboard.md`。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `db9fe33`（`dev/rtl`，基于 `main@c3d2f6b`；验证时尚未并入 main） |
| 被测文件 | `src/riscv/soc_top.v`、`src/riscv/pynq_z2_top.v`、`sim/riscv/tb_soc_top.v`、`build/build_soc.tcl`、`build/constraints/pynq_z2_soc.xdc`、`board/scripts/program_soc.tcl` |
| 验证人 | 验证线（waltercooper） |
| 日期 | 2026-09-26 |

## 环境

| 工具 | 版本 |
|:---|:---|
| Vivado | 2026.1（BASIC，win64） |
| 仿真 | XSim（GUI 行为仿真）——与 RTL 线 iverilog 形成**双工具对拍** |
| 器件 | `xc7z020clg400-1`（PYNQ-Z2） |
| 下载 | 板载 Micro-USB JTAG，器件 `xc7z020_1` |

## 结果 1：SoC 仿真（XSim）PASS

命令（从 `sim/` 目录执行）：
```text
xvlog -sv <src/riscv/*.v> riscv/tb_soc_top.v
xelab tb_soc_top -s tb_soc_top_sim
xsim tb_soc_top_sim -R
```
输出：
```text
PASS: SoC tohost=13, tohost_exit=0, LED=1101, reset LED=0000
```
原始日志：`sim_xsim.log`

> GUI 行为仿真的注意点：`tb_soc_top.v` 里 `IMEM_INIT_FILE="../src/riscv_fw/hello_v0.hex"` 是相对 `sim/` 的路径；GUI 的仿真工作目录在 `<工程>.sim/sim_1/behav/xsim/`，需把 `hello_v0.hex` 拷到该目录下的 `../src/riscv_fw/`（即 `behav/src/riscv_fw/`），并把 `xsim.simulate.runtime` 设为 `all`，否则会 `$readmemh` 找不到文件且只跑 1000 ns。

## 结果 2：构建（Vivado）BUILD PASSED

命令：`vivado -mode batch -source build/build_soc.tcl`

门禁全部通过：

| 项 | 实测 |
|:---|:---|
| 时钟 | `sys_clk_125` 8 ns、`core_clk_40` 25 ns 均存在且周期正确 |
| 时序 | **WNS +0.142 ns、TNS 0.000、WHS +0.071 ns、THS 0.000**；`All user specified timing constraints are met`；未约束端点 0 |
| DRC | 0 Error / 0 Critical Warning（22 条普通 Warning：REQP-1839×20、CHECK-3×1、ZPS7-1×1） |
| 资源 | Slice LUT 6267（11.78%）、Slice Register 408（0.38%）、Block RAM Tile 8（5.71%）、DSP 0 |
| bitstream | `build/run/soc/pynq_z2_soc.bit` |

报告副本：`reports/`（`soc_timing_impl.rpt`、`soc_utilization_impl.rpt`、`soc_drc_impl.rpt` 等）

## 结果 3：真实上板（JTAG）PASS

方式：Vivado **Hardware Manager（GUI）**：Open Target → Auto Connect → 选器件 `xc7z020_1` → Program Device → 选 `build/run/soc/pynq_z2_soc.bit` → Program；配置成功。
结果：板上 LED = `1101`（见下"上板现象"）。
> 等价命令行脚本：`board/scripts/program_soc.tcl`（按 `PART=xc7z020*` 唯一选器件）。归档时板卡已断开，未重抓命令行日志；**上板判据以板上 LED 现象为准**。

本次验证下载的 bitstream：
| 项 | 值 |
|:---|:---|
| 路径 | `build/run/soc/pynq_z2_soc.bit`（不入库） |
| SHA256 | `8D28219BBE8CE1022E6A73DFCD624E279101712DCFA4E58A76BC8BC18F53E71C` |
| 大小 | 4,045,766 B |

> 注：位流哈希与 RTL 线记录的 `d81cb8cf...` 不同属正常（位流含构建元数据），本值对应**本次验证实际下载**的位流。

## 上板现象与结论

- 下载后 LED = **`1101`**（LED0/2/3 亮、LED1 灭），**静止不动** ✅（主判据）
- 按 BTN0：LED 先 `0000`，松开后 `0001`；可重复；断电重下后回到 `1101`
- **结论：Part A SoC 真实上板 PASS。**

## 验证发现（非阻塞）

按 BTN0 松开后 LED 变为 `0001`，原因可解释：
`main_v0.c` 用 `tohost` 当前值当种子（`sum = (seed+1)+(seed+2)+(seed+4)+(seed+6) = 4*seed + 13`），而**软复位不清 dmem**、`tohost` 又位于 `.bss` 之外（`start.S` 清 `.bss` 不会碰它）→ 第二次运行 `seed=13` → `sum=65` → 低 4 位 `0001`。

- 属**契约 / 测试覆盖缺口**，非 RTL 缺陷：
  - `sim/riscv/tb_soc_top.v` 只检查复位期间 LED=`0000`，**未检查"释放后重跑"**；
  - `src/riscv/design_v0.md` §5.8 未定义软复位后的 LED 期望。
- 建议（反馈 RTL 线）：在 tb 增加"重跑期望"，或在契约写明，或决定复位时一并清 `tohost`。

## 复现步骤

1. `git switch` 到 `db9fe33`（或该提交所在分支）
2. 仿真：见结果 1（或 `bash sim/scripts/run_iverilog.sh soc`）
3. 构建：`vivado -mode batch -source build/build_soc.tcl`
4. 下载：`vivado -mode batch -source board/scripts/program_soc.tcl`
5. 观察 LED = `1101`

## 边界

- bitstream 不入库（`.gitignore *.bit`）；Vivado 工程产物不入库
- 本目录仅归档本次独立验证证据；不修改 RTL 线在原提交内的报告与 RTL/tb
