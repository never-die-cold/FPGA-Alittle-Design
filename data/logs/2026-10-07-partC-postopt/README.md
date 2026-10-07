# Part C PC/flush 优化后复验与上板（2026-10-07）

> 用途：对已并入 main 的 PC/flush 降深度优化（`2daecc9`，PR #57/#58 → main `c2bb910`）做 **Vivado 时序复测 + SoC 构建 + PYNQ-Z2 上板**。这是 `../2026-10-06-partC-verify/README.md` 缺口清单的收尾项：优化后 Vivado 未验证（最低复测点 11.520 ns）。
> 契约权威：`src/riscv/design_v1.md` §16；验收：`src/riscv/plan.md` §4.2/§4.3。
> 本目录归验证线；原始日志与报告副本只追加不改。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| 被测提交 | `main@c2bb910`（含 `2daecc9` PC/flush 降深度 + `e97aee9` arch-test 四档） |
| 工作区附加改动 | 仅 `src/riscv/core_top.v` 声明顺序（采纳验证线 `../2026-10-06-partC-verify/core_top_fix.diff`：`bp_predict_taken`、`redirect_target` 前移；**纯声明位置，功能零改动**，否则 `build_fmax.tcl` 的 `read_verilog -sv` 报 used before declaration） |
| 与全量回归锚点的关系 | `git diff 2daecc9 -- src/riscv/ sim/riscv/` 仅上述 core_top.v 声明移动 + e97aee9 的 tb_arch_test.v BHT_MODE 参数（均为已验证内容） |
| 工具 | Vivado 2026.1（`D:\Vivado_downloads\2026.1`，注：`board/scripts/program_soc.bat` 内硬编码路径已失效，本次经其 tcl 直调）；iverilog 13.0（MSYS2 ucrt64）；器件 `xc7z020clg400-1` |
| 验证人 | never-die-cold（agent 驱动）｜日期 2026-10-07 |

## 结果 1：iverilog 全量回归（声明补丁后复跑）

命令：`bash sim/scripts/run_iverilog.sh all`（仓库根）。**总退出码 0**，66 项 PASS；
`FAIL: injected` 两行为 vision 门禁自检的预期注入（与 2026-10-06 口径一致），非真实失败。
- 功能 tb 20 项全 PASS（含 `tb_branch_predict`、`tb_core_pc_control` 768 组、`tb_id_ex_stage` 12304 例、`tb_core_bht_flow` mode=0/1/2）。
- CoreMark 四档（退出码 0、tohost=34713、retired=10106386）：

| 档 | cycles | BHT lookup/hit/miss | 与 2026-10-06 锚点 |
|:---|---:|:---|:---|
| v1_nofwd | 19057438 | — | 一致 |
| v1_fwd | 17114141 | — | 一致 |
| v1_fwd_bht1 | 16335562 | 1854101/1587055/267046 | 一致 |
| v1_fwd_bht2 | 16232079 | 1854101/1690538/163563（91.18%） | 一致 |

原始日志：`iverilog-all.log`（末行含总退出码）。

## 结果 2：核 OOC 门禁复测 —— bht2 @ 11.520 ns（86.8 MHz）PASS ✅

命令：`vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_11p52_postopt 11.520 -core_profile bht2 src/riscv`

| 项 | 优化前（2026-10-06） | **优化后（本次）** |
|:---|:---|:---|
| WNS @11.520 ns | **−0.334 ns（约束实测失败）** | **+0.538 ns，TNS=0，hold 全过（WHS/WPWS 见报告）** ✅ |
| 最差路径 | `instr_hold_reg[5] → pc_reg[27]`，Data Path 11.860 ns，**17 级** | `u_if_stage/stall_q_reg → u_pc/pc_reg[30]`，Data Path 10.920 ns，**12 级**（logic 22.3% / route 77.7%） |
| LUT / FF | 2314 / 637（@10ns 档） | 2443 / 637（本点） |
| 脚本外推 Fmax | 84.4 MHz | 91.1 MHz（外推估计，非实测通过频率） |

- **结论：Part C 最低时序目标达成——保持三级，BHT2 核 OOC 在 86.8 MHz 实点约束通过。** 原失败记录（10-06）保留不改写。
- 口径：**可称"实测"的只有约束点通过/失败**；外推 Fmax 仅供参考。核 OOC 与完整 SoC 频率分开表述。

## 结果 3：核 OOC 四档 @10 ns（记录档，同 `build_fmax.tcl` 法）

| 档 | 优化前 WNS | **优化后 WNS** | 优化后外推 Fmax | LUT | 判定 |
|:---|---:|---:|---:|---:|:---|
| v1_nofwd | +0.447 | **+0.051** | 100.5 MHz | 2014 | **@100 MHz 实点通过** |
| v1_fwd | −0.383 | −0.587 | 94.5 MHz | 2150 | 失败（记录） |
| v1_fwd_bht1 | −1.928 | **−0.419** | 96.0 MHz | 2357 | 失败（记录） |
| v1_fwd_bht2 | −1.955 | **−0.586** | 94.5 MHz | 2508 | 失败（记录） |

- BHT 两档改善 1.3–1.5 ns（降深度直接收益）；`nofwd` 达 100 MHz 实点；`fwd/bht1/bht2` @10 ns 仍失败但外推已越过 v0 基线 86.8 MHz。报告副本：`reports/fmax/<label>/`。

## 结果 4：SoC 主档构建 —— 40 MHz bht2 BUILD PASSED

命令：`vivado -mode batch -source build/build_soc.tcl -tclargs 40 bht2`

| 项 | 实测 |
|:---|:---|
| 时序 | **WNS +3.618 / TNS 0**；hold WHS +0.035 / THS 0；未约束端点 0（脚本门禁通过） |
| DRC | 0 Error |
| 资源 | Slice LUT 6768（12.72%）、Slice Register 859（0.81%） |
| 位流 | `build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit`，4,045,766 B，SHA256 `B06F08289D8F461DE051A89095E4E22ACB290455632D162CA14BA869F407EC93` |

报告副本：`reports/soc_40mhz_bht2/`；构建日志：`build_soc_40mhz_bht2.log`。

## 结果 5：真实上板（40 MHz bht2 位流，优化后 RTL）

命令：`vivado -mode batch -source board/scripts/program_soc.tcl -tclargs build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit`
输出：`FOUND: xc7z020_1` → `PROGRAM PASSED`，End of startup HIGH（日志 `program_soc_40mhz_bht2.log`）。

| 项 | 期望 | 实测 |
|:---|:---|:---:|
| 下载后 LED | `1101`（`hello_v0` 写 `tohost=13`），静止 | ✅ `1101`，静止 |
| BTN0 按下 | `0000` | ✅ `0000` |
| BTN0 松开 | 依赖旧 DMEM（契约 §4 允许） | ✅ `0001`（与 Part A / 前次 v1 一致） |

观察人：never-die-cold（2026-10-07，板前读数）。

## 结论（限定口径）

- **PC/flush 降深度优化（`2daecc9`，已入 main）复验闭环**：iverilog 全量退出码 0、四档 CoreMark 锚点逐位一致 → 核 OOC 门禁 bht2 @11.520 ns（86.8 MHz）**WNS +0.538 通过**（优化前 −0.334 失败，原记录保留）→ SoC 40 MHz bht2 构建 WNS +3.618 → **真实上板 LED 三步现象与 Part A/Part B/前次 v1 完全一致**。
- **Part C 最低时序目标达成**：保持三级，BHT2 核 OOC 86.8 MHz 实点约束通过，优化后最差路径 17 级 → 12 级。
- 核 OOC 频率与完整 SoC 频率分开表述；外推 Fmax（91.1 MHz 等）非实测通过频率。
- 未做：优化后 XSim 四档复跑（10-06 已在优化前 RTL 上做过双工具对拍，本次锚点逐位一致故未重跑）；SoC 125 MHz 维持 FAIL 记录。

## 复现

```bat
rem Vivado 2026.1 实际安装于 D:\Vivado_downloads\2026.1（见下"边界"）
bash sim/scripts/run_iverilog.sh all
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_11p52_postopt 11.520 -core_profile bht2 src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top v1_<tier>_10ns_postopt 10.000 -core_profile <tier> src/riscv
vivado -mode batch -source build/build_soc.tcl -tclargs 40 bht2
vivado -mode batch -source board/scripts/program_soc.tcl -tclargs build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit
```

## 边界与遗留

- `src/riscv/core_top.v` 声明顺序修正**未 commit**（等理解确认；与 `../2026-10-06-partC-verify/` 的请求一致，请 RTL 线采纳后入库）。
- `board/scripts/program_soc.bat` 硬编码 `D:\Vivado\2026.1` 已失效，本次未改该脚本（超出目录授权），经 tcl 直调绕过；建议 RTL/板务线更新路径。
- SoC 125 MHz 档维持 2026-10-05 FAIL 记录（WNS −8.044），非阻塞，本次未复测。
- "主频提升或持平 v0 86.8 MHz"条款：bht2 @86.8 MHz 实点通过 + 外推 91.1 MHz；正式条款结论待 RTL/复核确认后写入契约 §14。
