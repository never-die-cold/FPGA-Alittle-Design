# build —— 可复现构建

Vivado 构建脚本与综合/实现报告，保证工程可由他人从零复现。

## 内容

- `build.tcl`：一键构建脚本（无工程模式：读 RTL/XDC → 综合 → opt/place/route → 报告归档）
- `constraints/core_top.xdc`：v0 核时序约束（100 MHz 目标 + OOC 时钟源标注）
- `reports/`：综合与实现报告归档（资源占用、Fmax/WNS、最差路径）——指标证据，入库
- `run/`：临时产物（checkpoint / 日志，不入库）

## 用法（Vivado 2026.1）

```bash
vivado -mode batch -source build/build.tcl
```

> v0 核暂无板级顶层，采用 **out_of_context（OOC）** 模式做核级基线：
> 直接做含 I/O 的实现会因顶层端口（166）超过 CLG400 可用引脚（125）而报 Place 30-58；
> bitstream 流程待 SoC 顶层就位后（M3）再挂接。

## v0 核基线（2026-09-14，post-route，OOC）

| 指标 | 实测 | 证据 |
|:---|:---|:---|
| WNS / Fmax（约束 10 ns / 100 MHz） | **-1.530 ns / 86.8 MHz**（未达标，Part B 优化对象） | `reports/timing_impl.rpt` |
| 失败端点 / 全端点 | 101 / 661 | 同上 |
| 最差路径 | `u_if_stage/flush_q_reg` 反馈路径：数据路径 11.405 ns（逻辑 3.450 / 布线 7.955），逻辑 17 级 | `reports/timing_worst_paths.rpt` |
| 资源 | LUT 846 / FF 65 / BRAM 0 / DSP 0（XC7Z020 占用 < 2%） | `reports/utilization_impl.rpt` |

## 约定

- 工具版本：Vivado 2026.1（BASIC 免费档，见 issue #2），版本写入报告
- 每次里程碑打 tag，并归档当次构建报告
- 报告数据与 `data/metrics.csv`、`report/` 设计报告保持一致

> 状态：🚧 v0 核综合基线已归档；SoC 顶层与 bitstream 流程待 M3
