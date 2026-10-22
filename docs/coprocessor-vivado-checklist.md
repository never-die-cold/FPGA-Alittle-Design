# 协处理器 Vivado 检查清单

> 状态（2026-10-22）：**40 MHz compute/storage OOC VERIFIED**；整机综合实现、bitstream、
> `.hwh` 与板验仍为 **UNVERIFIED**。默认安全档为 40 MHz。

board-top 已增加 `pynq_cop_top`、100/40 MHz AXI/AXIS CDC、PS7+AXI DMA block-design Tcl
与严格整机门禁，但当前 WSL 找不到 Vivado，以下整机条目仍为 **UNVERIFIED**。
当前板顶只支持 `target_id == roi_index` 恒等映射；任意 `TARGET_DESC_ADDR` 描述表接入
是发布前 OPEN，即使 Tcl 门禁通过也不代表该功能已验收。

## JL 执行命令

从仓库根目录打开 `cmd.exe`，将 Vivado 路径替换为实际安装位置：

```bat
set VIVADO=D:\vivado\2026.1\Vivado\bin\vivado.bat
call "%VIVADO%" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 compute
call "%VIVADO%" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 storage
powershell -ExecutionPolicy Bypass -File build\run_pynq_cop_gate.ps1 -Vivado "%VIVADO%"
```

只有两个 40 MHz 命令均通过后，才可选择性尝试 `-tclargs 100 compute` 与
`-tclargs 100 storage`；100 MHz 失败不覆盖 40 MHz 目录。报告分别写入
`build/reports/coprocessor/<档位>/<compute|storage>/`，临时 checkpoint 写入
`build/run/coprocessor/`。这些目录和 `.xpr` 已忽略，不提交生成物。

整机 PowerShell 入口先以所选 riscv32/riscv64 工具链强制重建 `cop_job.hex`，再跑
`build_soc.tcl 40 fwd` 的 `ENABLE_COP=0` 基线，最后跑 PS7+DMA+`pynq_cop_top` 非 OOC 门禁。
它依赖已有流程生成的固定 `sim/build/hdmi-source/ps7_config.tcl`；缺失时显式 FAIL。

## 2026-10-22 实测证据（Vivado 2026.1）

| OOC 目标 | 退出码 | LUT / FF / DSP / BRAM Tile | WNS / WHS | check_timing |
|:---|---:|:---|:---|:---|
| compute | 0 | 6,299 / 7,261 / 136 / 0 | +7.460 / +0.097 ns | 四项均 0 |
| storage | 0 | 38,562 / 12,389 / 0 / 28.5 | +18.108 / +0.225 ns | 四项均 0 |

storage 最终映射为 28×RAMB36E1 + 1×RAMB18E1；16 路权重、ROI、ping、pong 均为
Block RAM。8×64-bit GAP scratch 为小型 distributed RAM；参数的 16 路并读仍落寄存器/LUT。
两目标 DRC 均无 Error/Critical Warning。报告是本地生成物，不入库。

`coprocessor_board_clock.xdc` 是旧 PL 板钟集成约束模板。board-top 的 PS7 直接提供
100 MHz 与 40 MHz FCLK；`pynq_cop_board.xdc` 校验 10/25 ns 并将两域声明为异步。
当前没有实际整机报告，因此整机实现、bitstream 和 `.hwh` 仍为 **UNVERIFIED**；
PROVISIONAL payload 也不是发布模型。

## 每个档位必看指标与判定

| 报告 | 指标 | 门槛 |
|:---|:---|:---|
| `utilization_impl.rpt` | LUT、FF、DSP、BRAM36 | 两目标均不得 over-utilized；合计 DSP≤220、BRAM36≤140，LUT/FF 必须可放置 |
| `timing_impl.rpt` | setup/hold、WNS | WNS≥0，且报告不得有失败的 setup/hold 路径 |
| `check_timing.rpt` | no_clock、constant_clock、unconstrained endpoints、generated clocks | 四项计数全部为 0 |
| `drc_impl.rpt` | Error / Critical Warning | 0 |
| `cdc_impl.rpt` | core/cop 跨域 | 不得有未解释、未豁免的 unsafe CDC；邮箱以外的新跨域一律失败 |
| `vivado_version.txt` | 工具版本 | 记录实际版本，不借用历史版本结论 |

整机报告写入 `build/reports/pynq_cop_40mhz/`。`gate_summary.txt` 必须同时给出
WNS≥0、DSP≤220、BRAM36≤140、CDC unsafe/unknown=0、DRC blocking=0；任一缺失即 FAIL。
只有 Tcl 打印 `PYNQ COP WHOLE-SYSTEM GATE PASSED` 后才会生成
`build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit/.hwh/.xsa`。

`compute` 与 `storage` 是两个 OOC 实现，只能分别证明计算/控制逻辑和 K3 存储可实现；
资源相加只是容量预检，不能冒充整机布局布线。只有生产顶层实际完整实现通过上述整机门禁，
才能把“整机综合实现”升级为 PASS。

## 失败与回滚

1. 任一命令非零、WNS<0、存在未约束路径、DRC/CDC 未关闭或资源超限：该档位判 FAIL，
   保留本机报告供定位，但不提交、不发布 bitstream。
2. 100 MHz 失败：回滚到独立的 40 MHz 目录重跑，不修改或放宽门槛。
3. 40 MHz 失败：保持 `soc_top.ENABLE_COP=0`，不得交 NC 下载；修复后从干净报告目录重跑。
4. BRAM 未按预期推断：先核对 `storage/utilization_impl.rpt` 与 16×64-bit 权重 bank；不得用
   LUTRAM 成功布线替代 K2 的 BRAM 结论。
5. Windows 侧通过只表示“综合实现通过”；下载成功也不等于板级验收，现场稳定性另记。
