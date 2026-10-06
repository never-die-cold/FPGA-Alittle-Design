# Part C 验证证据（2026-10-06）

> 用途：验证线对 `dev/rtl@3c6b794`（Part C：可切换 BHT + 板级/构建四档参数化）的 Windows 复验：XSim 功能/四档对拍 → 核 OOC 四档 → SoC 主档构建与上板。
> 契约权威：`src/riscv/design_v1.md` §16（BHT）+ D17；交接：`docs/partC-rtl-handoff.md`、`docs/partC-verify-plan.md`。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `dev/rtl@3c6b794`（未并入 main） |
| **附加修正** | `src/riscv/core_top.v` 两处声明顺序（`bp_predict_taken`、`redirect_target` 前移）——用户授权、**功能等价**（纯声明位置），见 `core_top_fix.diff`；**请 RTL 线采纳**（否则 `xvlog -sv`/`build_fmax -sv` 报 `used before its declaration`） |
| 工具 | Vivado 2026.1；器件 `xc7z020clg400-1`；XSim |

## 结果 1：XSim 功能（单元 + 整核）PASS

| tb | 结果 |
|:---|:---|
| `tb_branch_predict`（三档单元） | ✅ `PASS: tb_branch_predict (21 checks)` |
| `tb_core_bht_flow` mode=0/1/2（错路副作用抑制） | ✅ 全 PASS |

## 结果 2：四档 CoreMark XSim 对拍 PASS（与 Icarus 逐位一致）

命令：`xsim cm_<tier> -R -testplusarg ...`（plusargs 同 `run_iverilog.sh`：`+hex` `+max_cycles=50000000` `+exp_*`）

| 档 | cycles | retired | CPI | lookup | hit | miss |
|:---|--:|--:|--:|--:|--:|--:|
| `v1_nofwd` | 19057438 | 10106386 | 1.886 | 0 | 0 | 0 |
| `v1_fwd` | 17114141 | 10106386 | 1.693 | 0 | 0 | 0 |
| `v1_fwd_bht1` | 16335562 | 10106386 | 1.616 | 1854101 | 1587055 | 267046 |
| `v1_fwd_bht2` | 16232079 | 10106386 | 1.606 | 1854101 | 1690538 | 163563 |

- **cycles 与 RTL 线 Icarus 锚点完全相同**；CRC 期望（`e9f5/e714/1fd7/8e3a/8799`）全过 → PASS。
- bht2 命中率 = 1690538/1854101 = **91.18%**；bht1 = 85.6%。
- 原始日志：`cm_*.log`（`cm_<tier>.log`）。

## 结果 3：核 OOC 四档（@10 ns = 100 MHz 参考点）

命令：`build_fmax.tcl core_top v1_<tier>_10ns 10.000 -core_profile <tier> src/riscv`

| 档 | WNS (ns) | 外推 Fmax (MHz) | LUT | FF | BRAM |
|:---|--:|--:|--:|--:|--:|
| `v1_nofwd` | **+0.447** | **104.7** | 1853 | 508 | 0 |
| `v1_fwd` | −0.383 | 96.3 | 2046 | 508 | 0 |
| `v1_fwd_bht1` | −1.928 | 83.8 | 2248 | 573 | 0 |
| `v1_fwd_bht2` | **−1.955** | **83.6** | 2314 | 637 | 0 |

- **可称为"实测"的只有约束点通过/失败**：`nofwd` @10 ns 通过、其余三档 @10 ns 失败；Fmax 为 Slack 外推估计。
- **发现**：`nofwd` 达 100 MHz（104.7）；**转发 −8MHz、BHT 再 −13MHz，主档 bht2 仅 ~83.6 MHz**——低于 100 MHz 目标、也低于 v0 基线 86.8。bht2 关键路径 `u_if_stage/flush_q_reg → u_pc/pc_reg[30]`（17 级），BHT 信号进入 flush/PC 逻辑拉长了该路径；**BHT 查找/表本身不是主凶**。
- 报告副本：`reports/fmax/<tier>/`。

## 结果 4：SoC 主档（bht2）构建与上板 PASS

命令：`build_soc.tcl -tclargs 40 bht2` → `BUILD PASSED, profile=bht2, WNS=+5.599`，位流 `build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit`，SHA256 `0D670A2315DBBC2D48FBEBCDDE8F99B791686B04D0E65EB7CC6C7A921C829BB9`。
上板：`PROGRAM PASSED`；**LED=`1101` 静止**，BTN0 `0000→0001`（与 v0/Part B 一致）。
报告副本：`reports/soc_40mhz_bht2/`。

## 未完成 / 缺口

- **arch-test 四档：未做**。原因：① 本机无 riscv 工具链、无 iverilog；② `run_arch_test*.sh` 仅支持 `fwd|nofwd`、**不含 BHT 档**。属工具链/脚本缺口，需 RTL 线补 BHT 档 arch-test 入口或在有工具链的机器上跑。
- **BHT 档 Vivado 完备性**：本次只做了 @10 ns 单点（四档）+ 主档 40 MHz SoC；四档 Fmax 收敛、SoC 四档未做。

## 复现

```bat
rem 编译（RTL 需先采纳 core_top_fix.diff）
xvlog -sv <src/riscv/*.v> <sim/riscv/tb_*.v>
rem 单元/整核
xelab tb_branch_predict -s bp; xsim bp -R
xelab work.tb_core_bht_flow -generic_top "BHT_MODE=2" -s bht; xsim bht -R
rem 四档 CoreMark（plusargs 见 run_iverilog.sh）
xelab work.tb_core_coremark -generic_top "ENABLE_FORWARDING=1" -generic_top "BHT_MODE=2" -s cm_bht2
xsim cm_bht2 -R -testplusarg "hex=../src/riscv_fw/coremark.hex" -testplusarg "max_cycles=50000000" -testplusarg "exp_tohost=34713" ...
rem OOC / SoC
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_10ns 10.000 -core_profile bht2 src/riscv
vivado -mode batch -source build/build_soc.tcl -tclargs 40 bht2
board\scripts\program_soc.bat build\run\soc_40mhz_bht2\pynq_z2_soc_40mhz_bht2.bit
```

## 边界

- 只读复验 + 用户授权的一处 `core_top.v` 声明顺序修正；`3c6b794` 未并入 main
- 位流不入库；关键报告已复制入本目录
