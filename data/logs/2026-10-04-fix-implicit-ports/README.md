# ID+EX 隐式端口修复验证

- 分支：`dev/rtl`
- 落地提交：`5499c2d fix(rtl): make ID+EX Verilog-2001 synthesizable`
- 对象：`id_ex_stage.v` 的 `decode (.*)` 改为 Verilog-2001 显式端口连接；tb 同步显式连接。
- 环境：WSL Ubuntu；Icarus Verilog；目标器件口径 `xc7z020clg400-1`。

## 可复现命令与结果

```bash
bash sim/scripts/run_iverilog.sh all
```

完整输出：`run_iverilog_all.log`。退出码 0，共 16 条 PASS；包括 ID+EX 6 例、
RV32IM `tohost=142879`、CoreMark CPI 2.105 和 SoC 回归。

同步到远端 `dev/rtl` 后，以仓库提供的解释器开关重跑：

```bash
VISION_PYTHON=python3 bash sim/scripts/run_iverilog.sh all
```

完整输出：`dev-rtl-run_iverilog_all.log`。退出码 0，共 48 条 PASS；覆盖上述
RISC-V 回归、视觉门禁自检、视觉 RTL 回归和三项 Python 检查。门禁自检会故意
注入 `FAIL/FATAL/ERROR` 样例并确认它们被拒绝，最终判据为
`PASS: vision gate 8 cases (PASS/FAIL/fatal/exit/missing tb)`。

```bash
grep -rn "(\.\*)" src/
iverilog -g2001 -Wall -tnull -s id_ex_stage \
  src/riscv/id_ex_stage.v src/riscv/decode.v src/riscv/alu.v
iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v
```

原始输出：`verilog2001_compile.log`。扫描无命中；编译退出码 0，stdout/stderr 为空，
目标模块与全核 OOC RTL 集合均退出码 0、stdout/stderr 为空，即默认 Verilog-2001 本地代理检查为零 error/warning。

同步后复核结果分别归档为 `dev-rtl-implicit-port-scan.log`、
`dev-rtl-verilog2001-compile.log` 和 `dev-rtl-diff-check.log`；三份文件均为零字节，
表示相应命令退出符合预期且没有错误、警告或空白字符问题输出。

## Vivado 状态

`vivado_probe.log` 记录了探测原始输出。WSL 找到的启动器属于 Windows 安装，但缺少
`Vivado/bin/unwrapped/lnx64.o/prodversion`，不能执行 Linux Vivado，因此本环境没有
Vivado OOC PASS 结论。可在 Windows 仓库根目录运行：

```powershell
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch `
  -source sim/scripts/synth_id_ex_ooc.tcl
```

成功判据是终端出现 `OOC SYNTH PASS: id_ex_stage ...`；脚本产物写入
`data/logs/id_ex_ooc/`。在真实输出产生前，状态保持“Vivado 综合未验证”。
