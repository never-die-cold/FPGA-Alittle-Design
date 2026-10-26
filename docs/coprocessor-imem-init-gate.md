# cop_job IMEM/DMEM 初始化门禁

## 调用清单

仓库活跃源码没有 `$readmemb`。会进入综合的 `$readmemh` 只有两处：

| 文件 / 模块 | 调用 | 生产板调用路径 |
|:---|:---|:---|
| `src/riscv/imem.v` / `imem` | 无条件 `$readmemh(INIT_FILE, mem)` | `cop_system_wrapper → cop_system_i/pl/inst (pynq_cop_top) → soc_top/soc → u_imem` |
| `src/riscv/dmem.v` / `dmem` | `INIT_FILE!=""` 时 `$readmemh` | 同上至 `soc_top/soc → u_dmem` |

`pynq_cop_top` 把同一个 `cop_job.hex` 传给两者；`soc_top` 只是参数转接。`pynq_z2_top →
soc_top → u_imem/u_dmem` 是 ENABLE_COP=0 基线的另一条综合调用路径，不进入生产 cop bit。

只用于仿真的直接调用按目录如下；它们不会证明 bit 内含 INIT：

- RISC-V：`tb_arch_test.v`、`tb_core_coremark.v`、`tb_core_fwd.v`、`tb_core_muldiv.v`、
  `tb_core_smoke.v`、`tb_core_test.v`。
- cop：`tb_cnn_sequencer.v`、`tb_conv_engine.v`、`tb_cop_top.v`。
- vision：`tb_chain.v`、`tb_cop_buf.v`、`tb_fullchain.v`、`tb_gaussian3x3.v`、
  `tb_in_align.v`、`tb_osd.v`、`tb_patterns.v`、`tb_rgb2gray.v`、`tb_scaler.v`、
  `tb_scaler_ds.v`、`tb_sobel.v`、`tb_top.v`。

复核命令：`rg -n '\$readmem[hb]' src sim build tools --glob '!sim/build/**'`。

## 原故障与路径

旧参数值 `src/riscv_fw/cop_job.hex` 是相对路径。project-mode synth run 的工作目录不是仓库根，
而是：

```text
build/run/pynq_cop_40mhz/project/pynq_cop_40mhz.runs/synth_1
```

因此旧写法会尝试打开该目录下的 `src/riscv_fw/cop_job.hex`。历史流程没有归档 `runme.log`，当前
WSL 又没有 Vivado，所以原 warning 原文不可恢复，不能伪造为已复现。修复后 Windows clean build
必须保留 `build/reports/pynq_cop_40mhz/readmem_synth_diagnostics.txt` 中的原始匹配行；任何
readmem/cop_job warning/error 都令门禁失败。

## 新门禁

1. Tcl 从 `[info script]` 推导仓库根和 `cop_job.hex` 绝对路径，不提交机器路径；构建期派生完整
   8192-word IMEM/DMEM 文件（尾部分别填 NOP/零），三者都通过 `add_files -norecurse` 成为显式
   工程依赖，BD module-reference 参数使用两份派生文件的绝对路径。
2. 综合前 `tools/cop_imem_gate.py precheck` 要求文件存在、非空，首三字严格为
   `00008117/00010113/00000297`。首字既不能是非法指令 `00000000`，也不能是 NOP `00000013`。
3. 综合后扫描 `synth_1/runme.log`；相关 warning/error fail-closed，并保存原始行。
4. 打开 synth netlist 后读取 `soc/u_imem/rdata_reg_0..7` 的 RAMB36E1 `INIT_*`：要求非全零，
   再按 8 个 4-bit lane 重组地址 0，必须等于 hex 首字 `00008117`。
5. `gate_summary.txt` 只有在上述门禁通过后才写 `IMEM_FIRST_WORD=00008117`、
   `IMEM_INIT_NONZERO=1`、`READMEM_WARNINGS=0`。

当前 RTL 在调用 `$readmemh` 前把 IMEM 填成 NOP，所以“文件没载入”在 RTL 语义上趋向
`0x00000013`，不是全零；器件若出现全零，`0x00000000` 是非法指令。新门禁同时拒绝两种空载状态。

## Windows clean-build 命令与实测

```powershell
$env:COP_PYTHON="C:\Microsoft VS Code\anaconda\python.exe"
& "D:\vivado\2026.1\Vivado\bin\vivado.bat" -mode batch `
  -source build\build_pynq_cop_gate.tcl
```

JL 主机没有 Windows RISC-V 工具链，故不运行会重建固件的 `run_pynq_cop_gate.ps1`。必须显式设置
`COP_PYTHON`，否则 Tcl 可能选到 WindowsApps 的 `python3.EXE` 占位符。

预期关键行：

```text
IMEM PRECHECK PASSED: first_word=00008117
READMEM LOG GATE PASSED: relevant_lines=0 blocking=0
IMEM POST-SYNTH GATE PASSED: first_word=00008117 nonzero=1 cells=8
PYNQ COP WHOLE-SYSTEM GATE PASSED: ...
```

2026-10-26 JL 用 Vivado 2026.1 实测三项均通过：`IMEM_FIRST_WORD=00008117`、
`IMEM_INIT_NONZERO=1`、`READMEM_WARNINGS=0`。报告中的 `D:\boardtop\...` 是同一仓库内容的
Windows 暂存路径，不是硬编码提交路径。该结论只覆盖综合后 IMEM 初始化，不代表板级验收。
