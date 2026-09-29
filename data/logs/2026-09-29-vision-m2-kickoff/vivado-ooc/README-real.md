# 模块二 OOC 综合基线（real 档：720p 行宽参数，不上板）

> 目的：真实行宽参数（WIDTH=1280/HEIGHT=720，scaler 目标 224×224 占位）下的资源与时序，供 10/5 评审定 HDMI 通路与模块三输入尺寸。OOC 模式，不集成、不上板。
> 入口：`bash sim/scripts/run_vivado_vision_ooc.sh real`（generics 见 synth_vision_ooc.tcl 头注释）。

## 结果汇总（Vivado 2026.1，xc7z020clg400-1，10 ns 约束）

| 模块 | WNS @10ns | ≈Fmax | LUT | FF | RAMB18（BRAM36 当量） |
|:---|:---:|:---:|:---:|:---:|:---:|
| line_buffer ×1（1280×8） | NA（单寄存器无内部弧） | — | — | 9 | 1（0.5） |
| gaussian_3x3（2 行缓存） | −3.162 | ≈76.0 MHz | 见 rpt | 见 rpt | 2（1） |
| sobel（2 行缓存） | −3.249 | ≈75.6 MHz | 见 rpt | 见 rpt | 2（1） |
| scaler（16 槽 1280×8） | −7.412 | ≈57.5 MHz | 见 rpt | 见 rpt | 16（8，5.7%） |

## 两次发现（本批核心产出）

1. **多驱动 RTL 缺陷（Vivado 抓到、iverilog 静默）**：`committed` 寄存器被两个 always 块驱动（帧复位修复时引入）。Vivado 报 20 个 Critical Warning `Synth 8-6895 multi-driven net`；iverilog 仿真行为完全正常（后写赢），10/10 tb 无一失败。已修复（committed 并入写侧单 always），复跑无 multi-driven 警告、WNS 与修复前综合结果一致（综合器原先恰好选了正确驱动），iverilog 10/10 回归不变。**教训：iverilog 干净 ≠ 综合干净，关键模块必须过一次综合看 Critical Warning。**
2. **BRAM 推断全部正确**：line_buffer 1280×8 → 1×RAMB18（READ_FIRST/WRITE_FIRST 端口对精确映射"同拍同址先读后写"）；gaussian/sobel 各 2 行 = 2×RAMB18；scaler 16 槽 = 16×RAMB18。**全链 BRAM 预算 ≈ 10 BRAM36（7%），7z020 上宽裕。**

## 时序解读与优化方向（10/5 评审输入）

- gaussian/sobel ≈76 MHz：对 720p60 像素钟 74.25 MHz 只有 ~2% 裕量。
- **scaler 57.5 MHz 不满足 74.25 MHz**，worst path 明确：行槽 16:1 选择 mux → 两级 8bit lerp → 输出寄存，21 级逻辑 17.4ns（逻辑 53%/布线 47%）。
- 优化方案（结构已定，10/5 后实施）：插值链切一级流水（x 方向 lerp 寄存一拍后再做 y 方向 lerp），fx/fy/像素操作数同步延迟对齐；tb 按像素序列对拍、不依赖绝对拍号，流水化后 golden 对拍判据不变，预期恢复到 75+ MHz。
- 1080p60（148.5 MHz）需要更深的流水 + 可能的多像素并行，列入 M2 后期目标；720p60 直通演示（M2 验收）在 scaler 流水化后可行。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-30 | 首版：real 档基线 + 多驱动缺陷发现与修复记录 | never-die-cold（模块二 RTL） |
