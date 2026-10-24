# Board-Gate Windows Vivado 实测续档

日期：2026-10-22；分支：`dev/riscv`；工具：Vivado 2026.1；未 push。

## 1. 执行范围

- 从 `2026-10-21-board-gate-checkpoint.md` 的 f) 命令继续，没有重做 K1–K5。
- 只验证 40 MHz `compute` / `storage` OOC；没有执行上板。
- 输出报告位于 gitignore 下的 `build/reports/coprocessor/40mhz/`，未提交生成物。

## 2. 初次真实结果

- checkpoint 中的 Vivado 路径不存在；注册表确认实际安装在
  `D:\vivado\2026.1\Vivado\bin\vivado.bat`。
- compute 初次退出 0、WNS +7.460 ns，但 XDC 中的 `if` 被 Vivado 报为不支持；不能据此收口。
- storage 初次退出 1：ROI 被拆成寄存器、ping/pong 被拆成 distributed RAM，最终
  `UTLZ-1` 为 LUT logic 57,380 > 53,200，placer 未运行。

## 3. 修复提交

- `10fa44a`：删除两个 XDC 中不支持的条件语句；周期变量仍由 Tcl 按档位注入。
- `437e973`：增加无复位同步 1R1W RAM 模板；ROI/ping/pong 改为实体 BRAM 推断，外部接口和
  一拍读延迟不变。
- `edd6ac8`：把实测指标及 OOC/整机边界写入 Vivado 检查清单。

## 4. 仓库内回归

- `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh bram_network`
  → 退出 0；`PASS: K3-LATENCY nominal one-cycle BRAM read matches; early/late samples mismatch visibly`；
  pattern/zero 各 `9225 packed words/73795 elements match integer network`。
- `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all`
  → 退出 0；最后一条为 zero `9225 packed words/73795 elements match integer network`。
- 回归在本机重新生成的 `src/riscv_fw/cop_job.dis` 是工具链噪声，已恢复到开工 HEAD，未提交。

## 5. 最终 Vivado 证据

两个命令均使用 `build/build_coprocessor_gate.tcl -tclargs 40 <target>`：

| 目标 | 退出码 | LUT | FF | DSP | BRAM Tile | WNS / WHS |
|:---|---:|---:|---:|---:|---:|:---|
| compute | 0 | 6,299 | 7,261 | 136 | 0 | +7.460 / +0.097 ns |
| storage | 0 | 38,562 | 12,389 | 0 | 28.5 | +18.108 / +0.225 ns |

- 两目标的 `no_clock`、`constant_clock`、`unconstrained_internal_endpoints`、
  `generated_clocks` 均为 0；DRC Error/Critical Warning 均为 0。
- storage 为 28×RAMB36E1 + 1×RAMB18E1；16 路权重、ROI、ping、pong 是 Block RAM。
- GAP scratch 是小型 distributed RAM；16 路参数并读仍为寄存器/LUT。两目标只是分别 OOC，
  资源相加不能作为整机实现结论。

## 6. bitstream / `.hwh` 前置审计

- `build_soc.tcl` 只读取 `src/riscv/*.v`；`pynq_z2_top` 未传 `ENABLE_COP`，所以保持默认 0。
- 仓库没有包含 `cop_top`、`cop_bram_storage`、Zynq PS、AXI-Lite 与 DataMover 的生产顶层/BD；
  纯 RTL `build_soc.tcl` 也没有 `.hwh` 导出路径。
- 仓库只有 J02 诊断 golden，没有 J05/J06 发布模型 payload/manifest。不得把诊断权重冒充生产模型。
- 因此 P2（发布 manifest 地址适配 + 生产板顶）实际是 P0 bitstream/.hwh 的前置；P1 NC/WC
  又依赖该产物。当前未生成 bitstream/.hwh，综合实现与板验状态保持 UNVERIFIED。

## 7. OPEN 与下一门槛

- OPEN-K2-1（部分收口）：16×64 权重 bank 与三个大缓冲已完成 OOC BRAM 推断；整机布线未验证。
- OPEN-STORAGE-1：参数并读仍用寄存器/LUT，ROI 双缓冲与双 64-bit 写口尚未进入生产板顶。
- OPEN-MODEL-1：J05/J06 发布 payload/manifest 缺失，无法实现唯一权威的 offset/length 适配。
- OPEN-BOARD-1：生产 Zynq PS/AXI/物理 bank 顶层与 `.hwh` 导出流程缺失。
- 下一门槛：先交付发布模型 payload/manifest，再按其 offset/length 实现并验证 P2；通过整机门禁后
  才能产 bitstream/.hwh，随后依次交 NC 下载、WC 真接口联调。
