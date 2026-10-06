# Part C 四档 iverilog 回归（2026-10-06）

> 用途：用项目官方仿真工具 **Icarus Verilog** 复跑 Part C 四档 CoreMark（此前的四档仅用 Vivado XSim 验证；本目录补 iverilog 官方结果，形成双工具对拍）。
> 被测：`dev/rtl@3c6b794`（Part C）；契约 `design_v1.md` §16。

## 环境

| 项 | 值 |
|:---|:---|
| iverilog | **Icarus Verilog 12.0**（`Icarus.Verilog` winget 包，bleyer.org build；`C:\iverilog\bin`） |
| 运行方式 | Git Bash：`export PATH=/c/iverilog/bin:$PATH`（本机原无 iverilog，本次按需安装） |
| 命令 | `bash sim/scripts/run_iverilog.sh v1_nofwd|v1_fwd|v1_fwd_bht1|v1_fwd_bht2` |

## 结果：四档全 PASS（与 XSim 及 RTL 锚点逐位一致）

| 档 | cycles | retired | CPI | lookup | hit | miss |
|:---|--:|--:|--:|--:|--:|--:|
| `v1_nofwd` | 19057438 | 10106386 | 1.886 | 0 | 0 | 0 |
| `v1_fwd` | 17114141 | 10106386 | 1.693 | 0 | 0 | 0 |
| `v1_fwd_bht1` | 16335562 | 10106386 | 1.616 | 1854101 | 1587055 | 267046 |
| `v1_fwd_bht2` | 16232079 | 10106386 | 1.606 | 1854101 | 1690538 | 163563 |

- 四档均 `PASS: coremark ...`，CRC 期望（`e9f5/e714/1fd7/8e3a/8799`）全过。
- **与 XSim（`data/logs/2026-10-06-partC-verify/`）cycles 完全相同** → 双工具对拍一致。
- 原始日志：`iv_v1_nofwd.log`、`iv_v1_fwd.log`、`iv_v1_fwd_bht1.log`、`iv_v1_fwd_bht2.log`。

## 备注

- `core_top.v` 的前向引用（`bp_predict_taken`/`redirect_target` 先用后声明）**iverilog 容忍**，故本 iverilog 回归无需修正即可跑；但 Vivado `-sv`（XSim/`build_fmax`）不容忍，需修正（见 `../2026-10-06-partC-verify/core_top_fix.diff`）。
- 本目录只补 iverilog 四档；arch-test 四档仍缺（还需 riscv 工具链，且 `run_arch_test*.sh` 不含 BHT 档）。
