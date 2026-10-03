# PicoRV32 vs 自研 v0 核 Fmax 对比实测（验证线，M4 前置提前完成）

日期：2026-10-03。分支 codex/vision-offboard @ 19d1088。
任务与口径：[docs/core_comparison.md](../../../docs/core_comparison.md) §3——同器件
xc7z020clg400-1、同 Vivado 2026.1、同 OOC post-route、约束递减收敛法（10ns→5ns→收敛）
两边同法。计划原排 M1 收口后（10/21–10/24），经批准提前执行，不占用 M1 验收资源。

## 复现入口

```bash
bash sim/scripts/run_fmax_compare.sh          # 全部轮次（pico | core 可过滤）
```

组成：`sim/scripts/fetch_picorv32.sh`（钉 commit 取上游）+ `build/build_fmax.tcl`
（周期参数化 OOC post-route，步骤与 build/build.tcl 一致，无额外优化 directive）。

## 源与配置

- **PicoRV32**：上游 YosysHQ/picorv32 固定 commit `ef203c2b0a3fb793280f5114941416c425c5b461`
  （2026-10-03 master tip）。regular = `picorv32` 默认参数（`top_regular` 包装）；
  large = COMPRESSED_ISA+BARREL_SHIFTER+ENABLE_PCPI+ENABLE_MUL+ENABLE_IRQ
  （上游 README 面积表同参数集，无 ENABLE_DIV），包装层 `scripts/vivado/synth_area_top.v`。
- **自研 v0**：`partA-v0` tag（= 962a4f5）的 `src/riscv` 快照（基线锚点，不含后并入的
  v1 积木文件），top `core_top`。现工作区 src/riscv 已含 v1 模块且 `id_ex_stage.v:20`
  使用 SV `.*` 隐式端口连接（Vivado 默认模式 Synth 8-2716 报错），故 tcl 以
  `read_verilog -sv` 解析、对比源码仍取 tag 快照钉死基线。
- 约束风格同 `build/constraints/core_top.xdc`（create_clock + HD.CLK_SRC），周期由
  tcl 参数化落 run 目录。

## 结果（post-route；WNS 单位 ns，Fmax = 1/(周期+WNS 取负) = 1000/(周期−WNS)）

| 配置 | 轮次 | WNS | Fmax | LUT | FF |
|:---|---:|---:|---:|---:|---:|
| PicoRV32 regular | 10ns | +3.705 | ≥158.9 | 891 | 575 |
| PicoRV32 regular | 5ns | −0.139 | 194.6 | 905 | 575 |
| PicoRV32 regular | 5.1ns | −0.118 | 191.6 | 899 | 575 |
| PicoRV32 large | 10ns | +0.594 | ≥106.3 | 1930 | 1031 |
| PicoRV32 large | 5ns | −2.110 | 140.6 | 2096 | 1031 |
| PicoRV32 large | 7ns | −0.445 | 134.3 | 2006 | 1031 |
| 自研 v0 | 10ns | −1.935 | **83.8** | 1606 | 401 |
| 自研 v0 | 5ns | −7.134 | 82.4 | 1625 | 401 |

**收敛结论**：

- PicoRV32 regular **≈ 192–195 MHz**（10→5→5.1ns 三轮；5ns 与 5.1ns WNS 已近零）
- PicoRV32 large **≈ 134 MHz**（10→5→7ns 三轮；界 106.3–140.6）
- 自研 v0 **≈ 83–84 MHz**：10ns 轮 WNS −1.935 / 83.8 MHz 与 `data/metrics.csv`
  2026-09-28 重综合基线**逐位一致**，5ns 轮 82.4 佐证——同脚本复现既有基线，
  方法自洽性成立，对比数据可直接引用。
- 资源对上游公开表（Artix-7 xc7k70t）：regular 905 vs 917 LUT、large 2006 vs 2019 LUT，
  量级吻合（器件与约束不同，小差异正常）。
- 上游公开 Fmax 口径 regular ~196–200 MHz（作者精调约束）；本测 194.6 可对上。

## 目录

- `<label>/utilization_impl.rpt`、`timing_impl.rpt`：各轮 post-route 报告
- `vivado-logs/`：各轮完整 Vivado 批处理日志（含命令回显与 FMAX RUN DONE 摘要）

## 限制与未实现

- OOC 无 I/O 约束，与 v0 基线同口径；未跑板级时序。
- 本对比只覆盖 Fmax/资源；CoreMark/MHz、CPI 引用官方公开口径（0.309 DMIPS/MHz、
  CPI 4–5），未重跑 PicoRV32 基准（core_comparison.md §1 决策 5）。
- v1 三级核验收（10/4）后可同法补 v1 两档/四档行。
