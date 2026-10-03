# ID+EX 隐式端口修复验证

- 分支：`codex/fix-implicit-ports`
- 对象：`id_ex_stage.v` 的 `decode (.*)` 改为 Verilog-2001 显式端口连接；tb 同步显式连接。
- 环境：WSL Ubuntu；Icarus Verilog；目标器件口径 `xc7z020clg400-1`。

## 可复现命令与结果

```bash
bash sim/scripts/run_iverilog.sh all
```

完整输出：`run_iverilog_all.log`。退出码 0，共 16 条 PASS；包括 ID+EX 6 例、
RV32IM `tohost=142879`、CoreMark CPI 2.105 和 SoC 回归。

```bash
grep -rn "(\.\*)" src/
iverilog -g2001 -Wall -tnull -s id_ex_stage \
  src/riscv/id_ex_stage.v src/riscv/decode.v src/riscv/alu.v
iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v
```

原始输出：`verilog2001_compile.log`。扫描无命中；编译退出码 0，stdout/stderr 为空，
目标模块与全核 OOC RTL 集合均退出码 0、stdout/stderr 为空，即默认 Verilog-2001 本地代理检查为零 error/warning。

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
