# 协处理器 Vivado 检查清单

> 状态：**UNVERIFIED — 需 Windows 侧 Vivado 执行**。WSL 未安装 Vivado；本文和 Tcl/XDC
> 不是综合、实现、时序或板级 PASS 证据。默认安全档为 40 MHz。

## JL 执行命令

从仓库根目录打开 `cmd.exe`，将 Vivado 路径替换为实际安装位置：

```bat
set VIVADO=D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat
call "%VIVADO%" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 compute
call "%VIVADO%" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 storage
```

只有两个 40 MHz 命令均通过后，才可选择性尝试 `-tclargs 100 compute` 与
`-tclargs 100 storage`；100 MHz 失败不覆盖 40 MHz 目录。报告分别写入
`build/reports/coprocessor/<档位>/<compute|storage>/`，临时 checkpoint 写入
`build/run/coprocessor/`。这些目录和 `.xpr` 已忽略，不提交生成物。

`coprocessor_board_clock.xdc` 是板级集成约束模板：默认 `core_clk_divide=25`，与
`pynq_z2_top.CORE_CLK_DIVIDE=25` 同档，125 MHz×8÷25=40 MHz。当前尚无包含协处理器、
物理 bank 与板级 IO 的生产顶层，因此该派生时钟及整机实现仍为 **UNVERIFIED**。

## 每个档位必看指标与判定

| 报告 | 指标 | 门槛 |
|:---|:---|:---|
| `utilization_impl.rpt` | LUT、FF、DSP、BRAM36 | 两目标均不得 over-utilized；合计 DSP≤220、BRAM36≤140，LUT/FF 必须可放置 |
| `timing_impl.rpt` | setup/hold、WNS | WNS≥0，且报告不得有失败的 setup/hold 路径 |
| `check_timing.rpt` | no_clock、constant_clock、unconstrained endpoints、generated clocks | 四项计数全部为 0 |
| `drc_impl.rpt` | Error / Critical Warning | 0 |
| `cdc_impl.rpt` | core/cop 跨域 | 不得有未解释、未豁免的 unsafe CDC；邮箱以外的新跨域一律失败 |
| `vivado_version.txt` | 工具版本 | 记录实际版本，不借用历史版本结论 |

`compute` 与 `storage` 是两个 OOC 实现，只能分别证明计算/控制逻辑和 K3 存储可实现；
资源相加只是容量预检，不能冒充整机布局布线。只有未来生产顶层使用同一 RTL、manifest
地址适配与 `coprocessor_board_clock.xdc` 完整实现后，才能把“整机综合实现”升级为 PASS。

## 失败与回滚

1. 任一命令非零、WNS<0、存在未约束路径、DRC/CDC 未关闭或资源超限：该档位判 FAIL，
   保留本机报告供定位，但不提交、不发布 bitstream。
2. 100 MHz 失败：回滚到独立的 40 MHz 目录重跑，不修改或放宽门槛。
3. 40 MHz 失败：保持 `soc_top.ENABLE_COP=0`，不得交 NC 下载；修复后从干净报告目录重跑。
4. BRAM 未按预期推断：先核对 `storage/utilization_impl.rpt` 与 16×64-bit 权重 bank；不得用
   LUTRAM 成功布线替代 K2 的 BRAM 结论。
5. Windows 侧通过只表示“综合实现通过”；下载成功也不等于板级验收，现场稳定性另记。
