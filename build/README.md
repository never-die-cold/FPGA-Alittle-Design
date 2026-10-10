# build —— 可复现构建

Vivado 构建脚本与综合/实现报告，保证工程可由他人从零复现。

> 模块一核＋最小 SoC 已完成收口，见[收口报告](../report/module1-closure.md)。
> 本轮无本地 Vivado/XSim；下面命令按现有脚本核对，未在本机执行，不产生新 WNS 结论。

## 内容

- `build.tcl`：一键构建脚本（无工程模式：读 RTL/XDC → 综合 → opt/place/route → 报告归档）
- `constraints/core_top.xdc`：核 OOC 100 MHz 参考约束；v0 重现须在 tag 对应源码，不能用当前 v1 冒充
- `build_fmax.tcl`：核 OOC 周期／配置入口；`-core_profile nofwd|fwd|bht1|bht2` 显式传参
- `build_soc.tcl`：板级 40／125 MHz 与四配置构建；默认 40 MHz、fwd、BHT 关
- `reports/`：综合与实现报告归档（资源占用、Fmax/WNS、最差路径）——指标证据，入库
- `run/`：临时产物（checkpoint / 日志，不入库）

## 用法（Vivado 2026.1）

```bash
vivado -mode batch -source build/build.tcl
```

SoC 从仓库根目录运行，频率和配置显式传入；使用同一 RTL/XDC。Windows Vivado 路径按本机安装位置替换：

```bat
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_soc.tcl -tclargs 40 fwd
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_soc.tcl -tclargs 40 bht2
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_soc.tcl -tclargs 125 bht2
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_fmax.tcl -tclargs core_top v1_bht2_11p52ns 11.520 -core_profile bht2 src/riscv
```

fwd 报告／位流目录为 `soc_40mhz/` 或 `soc_125mhz/`；其他配置加 `_nofwd/_bht1/_bht2` 后缀。
例如主档位流为 `build/run/soc_40mhz_bht2/pynq_z2_soc_40mhz_bht2.bit`，默认 fwd 为
`build/run/soc_40mhz/pynq_z2_soc_40mhz.bit`。脚本在时钟对象、未约束路径、WNS 或 DRC
门禁失败时停止，不生成该档位流。125 MHz 未过只能记录实际结果，不能写成已达标。

> 核 OOC 不含外部存储器，不能代替 SoC 全路径验收；核顶层不直接按板级 I/O 布局。
> 板级 `pynq_z2_top` 和 SoC bitstream 流程已存在；上板还需对应配置实机观测。

## v0 核基线（2026-09-14，post-route，OOC）

**历史数据保留**：下表是 9/14 快照，不能与当前 `build/reports/` 内容混用。
现存重综合报告为 WNS −1.935 ns、LUT=1606、FF=401，详见下表。

| 指标 | 实测 | 证据 |
|:---|:---|:---|
| WNS / Fmax（约束 10 ns / 100 MHz） | **-1.530 ns / 86.8 MHz**（历史外推、未达标） | [9/14 验收记录](../report/llm_log/2026-09-14-vivado-2026-1-acceptance.md) |
| 失败端点 / 全端点 | 101 / 661 | 同一历史记录 |
| 最差路径 | `u_if_stage/flush_q_reg` 反馈路径：11.405 ns（逻辑 3.450／布线 7.955），17 级 | 同一历史记录 |
| 资源 | LUT 846 / FF 65 / BRAM 0 / DSP 0 | 同一历史记录 |

### 当前归档报告与后续通过点（不替换历史失败）

| 对象／方法 | 结果 | 原始证据 |
|:---|:---|:---|
| v0 @10 ns OOC | WNS −1.935；101/1394 失败端点；LUT 1606／FF 401；83.8 MHz 仅外推 | [timing](reports/timing_impl.rpt)、[资源](reports/utilization_impl.rpt) |
| v0 最差路径 | 11.876 ns、13 级；logic 19.628%／route 80.372% | [worst paths](reports/timing_worst_paths.rpt) |
| BHT2 核独立实现 @11.520 ns | 86.806 MHz 实点通过，WNS +0.538；不等于绝对 Fmax | [核收口报告 §5](../report/module1-closure.md) |
| BHT2 SoC／板级 @40 MHz | WNS +3.618；有实际下载和 LED 观测；125 MHz 历史 FAIL 保留 | [实机证据](../data/logs/2026-10-07-partC-postopt/README.md) |

## 约定

- 工具版本：Vivado 2026.1（BASIC 免费档，见 issue #2），版本写入报告
- 每次里程碑打 tag，并归档当次构建报告
- 报告数据与 `data/metrics.csv`、`report/` 设计报告保持一致

> 当前构建与实机结论见[模块一收口报告](../report/module1-closure.md)；核 OOC、SoC 和板级频率分别记录。
