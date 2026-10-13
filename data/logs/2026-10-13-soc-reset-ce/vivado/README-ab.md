# SoC 复位/CE 结构 A/B（Vivado 2026.1，2026-10-13）

## 目的

验证一个有报告支撑的推断：`mem_wb_stage.v` 旧写法把 payload 字段放在异步复位块的 `else` 分支里。综合器据此为这些字段生成"复位期间保持"的 CE。这些 CE 引脚挂在复位网络上。在 SoC 中，`mem_addr` 驱动 32 KB 分布式 RAM（4140 个 LUT）。地址寄存器因此被复制约 86 份。每个副本都继承同一个复位派生 CE。复位网络被迫摊到整个 RAM 区域，形成高扇出慢路径。

## 方法

两侧使用同一 Vivado 2026.1、同一 XDC（`build/constraints/pynq_z2_soc.xdc`）、同一 generic（40 MHz、bht2）、同一 opt/place/route/phys_opt 指令（Explore）。

| 侧 | RTL 来源 | mem_wb_stage.v |
| --- | --- | --- |
| baseline | `git archive HEAD`（`3e2e1c9`）抽出，见 `baseline_root/` | 旧写法（payload 在 else 分支） |
| postpatch | 工作区 `src/riscv/` | 新写法（payload 独立无复位无使能块） |

两棵源码树逐文件 SHA-256 对比（`baseline-src-sha256.txt` / `postpatch-src-sha256.txt`）：仅 `mem_wb_stage.v` 不同。

- 入口：`sim/scripts/build_soc_ab.tcl`。它是 `build/build_soc.tcl` 的对照变体：源目录与输出目录参数化，综合后追加 control sets / high fanout 报告，不写 checkpoint 与 bitstream。门禁与原脚本一致（时钟检查、WNS≥0、DRC 无 Error/Critical Warning）。
- 调用命令见 `baseline-vivado.command.txt` / `postpatch-vivado.command.txt`；完整日志 `baseline-vivado.log` / `postpatch-vivado.log`（及 `*-stdout.log`）。
- 基线 WNS=3.618 ns，与 2026-10-07 归档报告 `build/reports/soc_40mhz_bht2/` 完全一致。这证明 A/B 条件复现了历史结果，两侧可比。

## 结果（实现后，40 MHz bht2）

| 指标 | baseline | postpatch | 变化 |
| --- | ---: | ---: | ---: |
| WNS | 3.618 ns | 6.447 ns | +2.829 ns |
| setup 失败端点 | 0 / 43808 | 0 / 43517 | −291 端点 |
| Slice LUTs | 6768 | 6766 | −2 |
| Slice Registers | 859 | 859 | 0 |
| LUT as Memory（dmem 分布式 RAM） | 4140 | 4140 | 0 |

端点数减少 291 与 control sets 中被删除的复位派生 CE 引脚数（291）一致。三处独立证据（control sets、时序端点计数、最差路径表）互相印证。

## 机制证据

1. baseline control sets（`baseline/soc_control_sets_synth.rpt`）：`CE = u_mem_wb/mem_mask_sel[1]_i_1_n_0`（复位反相网络）控制 **259 个 FF**；另有 `CE+SR` 集合 **32 个 FF**。合计 291 个 CE 引脚由复位派生网络驱动。postpatch 中同批 FF 变为 clock-only 259 + SR-only 32，该网络从 control sets 中消失。
2. baseline high fanout（`baseline/soc_high_fanout_synth.rpt`）：`reset_pipe[1]` 扇出 568；`mem_mask_sel[1]_i_1_n_0`（LUT1 反相器）驱动 291 个 CE 引脚；`u_mem_wb/Q[3]`（dmem 地址位）扇出 4097。
3. baseline 最差路径 top-10 全部是 `reset_pipe_reg[1] → … → u_mem_wb/mem_addr_reg[*]_rep*/CE`：数据路径 20.576 ns，布线占 96.5%。postpatch 该类路径不存在；新的最差路径是 imem 同步读（BRAM 读地址寄存器）→ 取指/译码 → mem_wb 地址寄存器 D 端，slack 从 6.447 ns 起。
4. 核 OOC 不受限的原因：`core_top` 中 `dmem_addr` 只是端口。OOC 综合没有 4097 负载，不触发地址寄存器复制。进 SoC 挂上分布式 RAM 后，同一 RTL 才出现"地址复制 + 每个副本带复位 CE"的派生路径。这解释了"核能过 86.8 MHz 约束、SoC 40 MHz 才剩 3.6 ns 余量"的差异。

## 频率外推（非实测 Fmax）

- baseline：25 − 3.618 = 21.382 ns → 约 46.8 MHz
- postpatch：25 − 6.447 = 18.553 ns → 约 53.9 MHz

这只是 40 MHz 约束下的外推。未在更高约束下重跑实现，不能当作达标频率。

## 下一步瓶颈（本轮未做）

- 新最差路径类：imem BRAM 读地址环路与 load-use 通路。
- dmem 仍是 32 KB 异步读分布式 RAM：4140 LUT、单地址位扇出 4097。分银行（banked read select）或改同步 BRAM 是候选方案；同步 BRAM 会改变访存拍序，必须单独评估 CPI 代价。
- 核 OOC fmax 的 A/B 未跑：本轮改动的收益证据在 SoC 侧。
