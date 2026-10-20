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

| 时钟 | 周期 | 修 CRC 前 | 修 CRC 后 | 结论 |
|:---|---:|---:|---:|:---|
| `cop_clk` | 10 ns | **−2.743 ns**（78.5 MHz） | **+0.165 ns**（101.7 MHz） | 100 MHz 达标 |
| `core_clk` | 25 ns | +19.341 ns | +18.570 ns | 裕量很大（核域基本是寄存器） |

**修前的关键路径全部落在 `cop_dma_loader` 的 CRC32**：`loader/crc_state_reg[*]` → `loader/crc32_o_reg[*]`，
13 级 LUT（`LUT6=8`），前 10 条违例路径都是这一族。也就是说 **100 MHz 的卡点是逐字节 CRC 的
单拍组合深度，不是 CNN 阵列**。

### CRC 修复（已实施）

8 字节一拍折完的组合异或树改成**逐字节折叠**：beat 先进 `hold_data/hold_keep` 寄存器，
每拍只折一个字节，折完才收下一拍（消化期间 `stream_ready_o=0`，上游按 AXI-Stream 等待）。

| 项 | 修前 | 修后 |
|:---|---:|---:|
| `cop_clk` WNS | −2.743 ns | **+0.165 ns** |
| Slice LUTs | 6,699 | **6,308**（少 391，异或树变小） |
| Slice Registers | 7,181 | 7,256（+75：beat 保持寄存器） |
| DSP / BRAM | 136 / 0 | 136 / 0 |
| 权重装载耗时（36,032 B） | ~45 µs | ~365 µs（仍远小于一次 4.7 ms 推理） |

CRC 值不变（同一多项式、同一字节序），TB 用 `cecee288` 锚定；装载变慢按 C03 §9 的背压条款消化，
契约没有锁吞吐。C03 的相关要求只有一句："施加背压时必须保持 valid/data/last，不得丢字节或重复计数"，
TB 现在按 AXI-Stream 语义驱动（valid 保持到被接收），并断言消化期间 `ready=0`。

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

## 4. 卡点处置（已实施，见上）

三个候选里选了"逐字节折叠"：不新增时钟域、不需要 ROM，资源反而更省，代价只是装载变慢
（一次性动作，~365 µs）。另外两个被放弃：CRC 降频要加时钟域；查表法一拍仍要 8 次查表，
深度省不掉。

## 5. 边界

- 未跑 XSim；未做整机 SoC 时序；未上板。
- OOC 无 I/O delay，外部端口路径与时钟偏斜仍是估计。
- 修 CRC 前 `cop_top` 只能跑到 ~78.5 MHz，现在 **OOC 口径下 100 MHz 达标**；这不改变 J04a 状态，
  也不等于整机 100 MHz——SoC 里还有视频、存储、PS 与真实 I/O。
- 原始控制台日志：`vivado-console.log`（430 KB），退出码见 `vivado-console.exit.txt`。
