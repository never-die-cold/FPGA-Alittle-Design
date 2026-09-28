# 模块二 OOC 综合基线（不上板）

> 目的：模块二首批四模块的 Vivado 资源/时序基线。OOC 模式，不集成 SoC、不生成 bitstream、不上板。
> 结论：gaussian/sobel/scaler 在 10 ns（100 MHz）约束下 WNS −1.24/−1.44/−1.35 ns（≈88 MHz 通过），对 720p60 像素钟 74.25 MHz（13.47 ns）均有 >3 ns 裕量。

## 环境

| 项 | 值 |
|:---|:---|
| Vivado | v2026.1（64-bit），与 Part A 同版本 |
| 器件 | xc7z020clg400-1，`synth_design -mode out_of_context` |
| 约束 | `create_clock -period 10.0 [get_ports clk]`（综合后创建） |
| 入口 | `bash sim/scripts/run_vivado_vision_ooc.sh`（逐模块 batch） |
| 本目录文件 | 各模块 `_utilization.rpt` / `_timing.rpt` / `_ooc_result.txt` |

## 结果汇总（单元级参数 WIDTH=16 / HEIGHT=8 / NLINES=16）

| 模块 | WNS @10ns | ≈Fmax | LUT | FF | BRAM |
|:---|:---:|:---:|:---:|:---:|:---:|
| rgb2gray | NA（见口径 1） | — | 87 | 11 | 0 |
| gaussian_3x3 | −1.241 | ≈88.9 MHz | 179 | 117 | 0 |
| sobel | −1.439 | ≈87.4 MHz | 216 | 117 | 0 |
| scaler | −1.347 | ≈88.2 MHz | 469 | 291 | 0 |

## 口径与边界（重要）

1. **rgb2gray WNS=NA 是口径正常**：单级流水（input→reg 一级），OOC 网表无 reg-to-reg 内部路径，WNS/WHS 无从建立；11 个 FF 均在（out_y 8 + de/vs/hs 各 1）。input→reg 组合延迟需在 vision_top 集成时以 input delay 约束评估，OOC 单元结论不覆盖。
2. **BRAM=0 不可外推**：单元级行深 16 太浅，line_buffer 综合为 LUTRAM；真实行宽（1280）时 gaussian/sobel 各 2 行 + scaler 16 槽会转 BRAM/ULTRA 资源，届时 utilization 结论需重测。
3. 100 MHz 收口需 ~1.4 ns 优化（scaler 插值链/随机槽 mux 是关键路径候选）；720p60 @74.25 MHz 当前有裕量，1080p60 @148.5 MHz 需流水切刀，均留 10/5 评审后处理。
4. 本批次为**首批基线**：用于发现时序结构问题，不作为验收数据（验收口径按 plan.md §4.x 于 M2 收口时以集成后报告为准）。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版：四模块 OOC 基线 + 口径说明 | never-die-cold（模块二 RTL） |
