# v0 核回归基线（2026-09-14）

> 用途：「优化不改语义」的对照证据——Part B/C 改动后必须跑同一套回归，结论与本基线一致才算通过。
> 来源任务：`docs/tasks/verify_never-die-cold.md` 第 1 周（验证线）。

## 被测版本

| 项 | 值 |
|:---|:---|
| 代码版本 | `61b99a5`（origin/main，v0 两级流水 RV32I） |
| RTL | `src/riscv/*.v`（pc / regfile / alu / decode / if_stage / core_top） |
| 测试程序 | `src/riscv_fw/hello_v0.hex`（SHA256 `F8D097B2C9400C6864C77A629CBBC602041268F1847868C04B5A8EE691F7ADE3`）<br>`src/riscv_fw/hello_test.hex`（SHA256 `5D02B5EFA9132EAA8BAA8E0276C62E8B7562D03AFF525FE8FA9DA61A61699108`） |

## 环境

| 工具 | 版本 |
|:---|:---|
| Icarus Verilog | 13.0（stable，MSYS2 ucrt64） |
| Vivado XSim | v2026.1（BASIC 授权） |
| RISC-V GCC | 14.2.0（`riscv32-unknown-elf`） |

## 结果（双工具对拍，结论一致）

| tb | 检查点 | iverilog | XSim |
|:---|:---|:---:|:---:|
| `tb_core_smoke` | `tohost==13 && tohost_exit==0` | ✅ PASS | ✅ PASS |
| `tb_core_test` | `tohost_exit==0`（RV32I 38 用例） | ✅ PASS | ✅ PASS |

- 原始输出：`run_iverilog_2026-09-14.log`、`xsim_2026-09-14.log`
- 编译期 warning（timescale inherited、`$readmemh` 不足 4096 字）为既有已知现象，不影响 PASS 判定

## 复跑方法

```bash
# iverilog（MSYS2 UCRT64 shell）
bash sim/scripts/run_iverilog.sh

# XSim（Vivado 2026.1，从 sim/ 目录运行以保证 $readmemh 相对路径正确）
xvlog ../src/riscv/*.v riscv/tb_core_smoke.v riscv/tb_core_test.v
xelab tb_core_smoke -s smoke && xsim smoke -R
xelab tb_core_test -s test  && xsim test -R
```

## 关联

- 综合基线（同版本，OOC post-route）：**Fmax 86.8 MHz / WNS -1.530 ns**——证据 `build/reports/`、指标 `data/metrics.csv`
- 环境验收记录：`report/llm_log/2026-09-14-vivado-2026-1-acceptance.md`
