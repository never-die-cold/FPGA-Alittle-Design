# cop_top OOC 综合与实现（2026-10-19）

> 目的：回答 OPEN-7/OPEN-8 里"离板能不能先拿到资源/时序结论"，并给 J04b 一个明确的卡点。
> **这是 OOC 估计，不是整机时序、不是板端验收。** 约束只有寄存器到寄存器路径，I/O 无 delay。

## 1. 命令与环境

```bash
# Windows，Vivado 2026.1
D:/Vivado_downloads/2026.1/Vivado/bin/vivado.bat -mode batch -source build/build_cop.tcl
```

- part：`xc7z020clg400-1`；模式：`synth_design -mode out_of_context` + `opt/place/route`。
- 源码：`src/coprocessor/*.v`，用**默认 Verilog-2001 模式** `read_verilog`（不加 `-sv`），顺带验证综合语言边界。
- 时钟：`core_clk` 25 ns（40 MHz，对齐板端核时钟）、`cop_clk` 10 ns（100 MHz，C03 目标）；
  两者设为 asynchronous clock groups。
- 报告：`build/reports/cop/`；运行产物（DCP）在 `build/run/cop/`，不入库。

## 2. 结果

| 项 | 值 |
|:---|:---|
| Slice LUTs（impl） | 6,699 / 53,200（12.59%） |
| Slice Registers | 7,181 / 106,400（6.75%） |
| DSP48E1 | **136** |
| Block RAM | **0** |
| 综合告警 | 0 critical、0 error；119 warnings（多数是诊断模块未用寄存器被裁） |
| 实现 DRC | 0 critical |

### 时序（route 后，max delay）

| 时钟 | 周期 | WNS | 结论 |
|:---|---:|---:|:---|
| `cop_clk` | 10 ns | **−2.743 ns** | **不满足 100 MHz**，等效 Fmax ≈ 78.5 MHz |
| `core_clk` | 25 ns | +19.341 ns | 裕量很大（核域基本是寄存器） |

**关键路径全部落在 `cop_dma_loader` 的 CRC32**：`loader/crc_state_reg[*]` → `loader/crc32_o_reg[*]`，
13 级 LUT（`LUT6=8`），前 10 条违例路径都是这一族。也就是说 **100 MHz 的卡点是逐字节 CRC 的
单拍组合深度，不是 CNN 阵列**。

### CDC

| 方向 | 端点 | Safe | Unsafe | Unknown | No ASYNC_REG |
|:---|---:|---:|---:|---:|---:|
| `core_clk` → `cop_clk` | 45 | 45 | 0 | 0 | 1 → **0** |

- 修前 `cop_cdc_mailbox` 的两级同步链没标 `ASYNC_REG`，报告 `No ASYNC_REG=1`；
  给 `ack_sync1/2`、`req_sync1/2` 加 `(* ASYNC_REG = "TRUE" *)` 后归零（Icarus 也照常通过）。
- **"Safe" 的口径要说清**：它是在我声明的 async clock groups 前提下、工具认为没有不安全跨域；
  这不是功能正确性证明，CDC 行为仍要 TB 和上板复验。

## 3. 与历史数字的关系（不要混用）

10/13 的 `WNS +0.058 ns / DSP 192 / LUT 10,100` 是**控制器 wrapper OOC**，且当时带 1 ns 输入/输出假设；
本次是 `cop_top` 整层 OOC、无 I/O delay。两者顶层、输入假设、时钟数都不同，不能直接对比。
本次 136 DSP 与历史 192 的差异需要在同一 Tcl 下复跑才能解释，暂记为待核对项。

## 4. 卡点与可选修法（未实施）

`cop_dma_loader` 每拍吃 64 bit（8 字节），CRC32 在**一拍内**把这 8 字节折进 32 位状态，因此组合深度是
8 级字节异或树再叠 32 位状态。可选：

1. **两级流水**：4 字节 + 4 字节，插一拍寄存器；需要 loader 在 CRC 未收敛时对上游施加一拍背压。
2. **降频跑 CRC**：CRC 单独用低速时钟域，代价是 loader 吞吐要重新算。
3. **换查表法**：需要 ROM/BRAM，和现在"0 BRAM"的资源画像不同。

三种都要先冻结"loader 必须多少吞吐"，不能顺手改。改完必须重跑本目录的入口并更新本 README。

## 5. 边界

- 未跑 XSim；未做整机 SoC 时序；未上板。
- OOC 无 I/O delay，外部端口路径与时钟偏斜仍是估计。
- "100 MHz 不满足"只说明当前 `cop_top` 内部逻辑在 xc7z020-1 上跑到 ~78.5 MHz，**不改变 J04a 状态**，
  但它是 J04b 必须解决的门槛之一。
- 原始控制台日志：`vivado-console.log`（430 KB），退出码见 `vivado-console.exit.txt`。
