# 协处理器 Vivado 检查清单

> 状态（2026-10-22）：**40 MHz compute/storage OOC VERIFIED**；`ENABLE_COP=0` 基线 PASS；
> Vivado 2026.1 整机 40 MHz 门禁 **PASS**。这不等于板级验收。

board-top 已增加 `pynq_cop_top`、100/40 MHz AXI/AXIS CDC、PS7+AXI DMA block-design Tcl
与严格整机门禁。JL 已在 Windows Vivado 2026.1 完成 CDC 解析/FIFO 修复后的复跑；
WSL 仍不具备 Vivado，不能在此重现综合实现。
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
第二次 Windows 整机实测确认 latch=0、check_timing 四项全 0；WNS +2.607 ns、
WHS +0.035 ns、LUT 48.32%、FF 33.68%、DSP 136/220、BRAM36 69/140、DRC 0。本次唯一失败
是旧脚本查找不存在的 `Unsafe/Unknown` 字样；位流在 `write_bitstream` 前被正确阻止。

最终 Windows 复跑门禁 **PASS**：WNS +2.498 ns、DSP 136/220、BRAM36 69/140、
LATCHES=0、DRC_BLOCKING=0；CDC-3=12、CDC-6=7、CDC-15=73，全部逐条命中 allowlist，
无 Critical。产物与 SHA256：

- `build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit`：`b499cabe3d9a54274b93c659199336d6bbcceaf4d6fb93ea152ab0f414ef7e0a`
- `build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh`：`6a0a398b6d95ef940beb0f66c9c105547e82f3dd4f7bdbb967ac0f72564042c6`

`build/reports/pynq_cop_40mhz/gate_summary.txt` 是本次数字的权威报告。JL 门禁通过只证明整机
综合实现，不等于 NC 下载、现场稳定或板级验收；PROVISIONAL payload 也不是发布模型。

## Vivado 2026.1 CDC 格式与 allowlist

汇总表格式是 `ID Severity Count Description`，最终实测为 `CDC-3 Info 12`、
`CDC-6 Warning 7`、`CDC-15 Warning 73`；报告不含 `Unsafe/Unknown` 字段。门禁要求
汇总与 detail 条数一致，每条 detail 恰好匹配一条 allowlist；Critical、未列 ID、
路径越界、数量超限或表格无法解析均立即 FAIL。

| 条目 | ID / Severity | 路径正则（摘要） | 单条上限 | 允许理由 |
|:---|:---|:---|---:|:---|
| `single_sync` | CDC-3 / Info | `pl/inst/{axil_cdc named toggle/response sync, axis_cdc gray sync, dma_* sync}` | 12 | 显式命名的两级 `ASYNC_REG` 单比特同步 |
| `gpio_sync` | CDC-3 / Info | `adapter/error_o_reg -> dma_control/.../INPUT_DOUBLE_REGS5/syncstages_ff_reg` | 1 | 厂商 AXI GPIO 内置两级同步器 |
| `axil_payload` | CDC-6 / Warning | `pl/inst/axil_cdc/(ar_m1\|aw_m1\|wd_m1\|ws_m1\|rdata_s1)_reg` | 7 | 源载荷在 toggle/ack 完成前保持，目标域两拍采样 |
| `fifo_rgray` | CDC-6 / Warning | `pl/inst/axis_cdc/(rgray_s1\|wgray_m1)_reg` | 5 | Gray 指针每次只变一位，经两级 `ASYNC_REG` 同步 |
| `fifo_read` | CDC-15 / Warning | `pl/inst/axis_cdc/mem_reg.*/C -> out_data_reg.*/D` | 73 | 仅 64 data + 8 keep + 1 last 的 FIFO 读口，由注册空状态门控 |

ID 总上限另固定为 CDC-3≤12、CDC-6≤7、CDC-15≤73；两条 CDC-6 不能因分项
而把总预算放大。CDC-6 在 [AMD UG906 2026.1](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/CDC-Rules-Precedence)
中分类为 Unsafe，因此只能通过上述精确路径证据，不是整类忽略。

CDC-15 的结构证据：FIFO 使用带回绕位的 5-bit 二进制指针，跨域前转 Gray 码；
读/写 Gray 指针均经两级 `ASYNC_REG` 同步；`full`/`mem_empty` 由 next pointer 比较后注册，
只有 `write_fire` 才写 RAM、只有 `read_load && !mem_empty` 才把 RAM 装入 73-bit 输出寄存器。
`tb_cop_axis_async_fifo_random` 在 `Ts:Tm=10:26,26:10,14:22,22:14` 四档，每档 257 beat
随机 valid/ready 背压，逐 beat 断言不重复、不丢失、顺序正确。PASS 行：
`PASS: axis_fifo_random all ratios no duplicate, loss, or reorder`。

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
WNS≥0、DSP≤220、BRAM36≤140、latch=0、CDC allowlist 逐条通过、DRC blocking=0；任一缺失即 FAIL。
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
