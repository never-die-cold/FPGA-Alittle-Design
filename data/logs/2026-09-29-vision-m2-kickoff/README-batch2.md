# 2026-09-29 模块二第二批：scaler / sobel / 链式冒烟单元回归

> 目的：模块二第二批 RTL——双线性缩放器、Sobel 边缘、rgb2gray→gaussian 链式冒烟。
> 结论：6/6 tb PASS（含第一批三模块无回归），像素级 0 错误。

## 环境

| 项 | 值 |
|:---|:---|
| 分支 | dev/vision（PR #41），基线 23a082b |
| iverilog | Icarus Verilog 13.0 (stable) (v13_0) |
| 黄金参考 | data/golden/vision/{scaler,sobel}/（gen_*.py，含定点 vs 浮点自检） |
| 命令 | `bash sim/scripts/run_vision_iverilog.sh all` |
| 原始日志 | 本目录 `vision-all-6tb.log` |

## 结果（6/6 PASS）

| tb | 结果 | 说明 |
|:---|:---|:---|
| tb_rgb2gray / tb_line_buffer / tb_gaussian3x3 | PASS | 第一批无回归 |
| tb_scaler | PASS | 16x8→32x16，512 px 逐像素 0 错误 |
| tb_sobel | PASS | 128 px，L1 幅值 + 边界复制，0 错误 |
| tb_chain | PASS | rgb2gray→gaussian 级联，中间级+末端双双对拍，0 错误 |

## scaler 实现口径 v0.1（design_v0.md §3.1 同步）

- 契约：16.16 定点坐标 `(2d+1)*S/(2D)-0.5` clamp，x0/x1=相邻列，fx/fy 取小数高 8 位，两级 8bit lerp。
- 架构：NLINES 个行槽滑动缓存（写指针按行号取模），2 拍/像素双相位随机列读，读地址由坐标累加器组合产生。
- 约束/约定：行槽数 2 的幂；行步进 SH/DH ≤ NLINES-2 时读槽不被写覆盖（RTL 不含检查，tb 断言覆盖默认参数）；吞吐 1 像素/2 拍——缩小档（720p→CNN 输入）预算充足，放大档受帧预算约束。
- 发射与源写入解耦：行尾下一行源未就绪则挂起，hs 提交后续发；vblank 给足发射追赶时间。

## 调试记录（4 轮，供评审参考）

1. 触发就绪判据差一（`y1 <= committed` → `y1 < committed`），提前发射读了未写入行。
2. `committed` 由组合改寄存器（sticky）：hs 脉冲瞬间的完成计数在 vblank 挂起期已不可见。
3. 末像素插值发生在行尾后一拍而行坐标已更新 → 行坐标装 pending、末像素算完再提交 + drain 拍防丢末像素。
4. 末行后 `out_row` 未推进导致空闲条件重触发重复发射 → row_end 无条件推进。

## 遗留

- Vivado OOC 综合（资源/时序基线）下一批做。
- scaler 放大档吞吐与多像素并行化、链式 scaler（rgb2gray→gaussian→scaler 全链）、与 vision_top 的集成：10/5 评审后。
- 本批文件未 commit（将 push 至 PR #41）。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版：第二批 6/6 PASS + scaler 调试记录 | never-die-cold（模块二 RTL） |
