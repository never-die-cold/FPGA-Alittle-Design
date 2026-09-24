# CoreMark v0（两级核）32 迭代跑分证据

> 契约：`docs/coremark.md` §5/§6；golden：`data/golden/coremark_2k_32iter/`
> 日期：2026-09-23｜配置：v0 两级流水（main 合并态）

## 测试条件（可复现）

| 项 | 值 |
|:---|:---|
| 固件 | `src/riscv_fw/coremark.hex`（4094 字，commit 见 git log） |
| profile | 2K、seeds 0/0/0x66、`ITERATIONS=32`、`MEM_STATIC` |
| tb | `sim/riscv/tb_core_coremark.v`（8192×32 双口预载、`+timer_addr=80008000`） |
| 时钟 | 10 ns（标称 100 MHz） |
| 工具 | iverilog 13.0（MSYS2 ucrt64）；riscv32-unknown-elf-gcc 14.2.0 |

复现命令（在 `sim/` 下）：

```bash
iverilog -g2012 -o build/tb_core_coremark.vvp riscv/tb_core_coremark.v ../src/riscv/*.v
vvp build/tb_core_coremark.vvp +hex=../src/riscv_fw/coremark.hex +exp_exit=0 \
    +timer_addr=80008000 +max_cycles=50000000 +exp_iter=32 +exp_seedcrc=e9f5 \
    +exp_crclist=e714 +exp_crcmatrix=1fd7 +exp_crcstate=8e3a +exp_crcfinal=8799
```

## 结果（原始日志：`run_v0_32iter.log`）

```text
== obs iter=32 seedcrc=0xe9f5 crclist=0xe714 crcmatrix=0x1fd7 crcstate=0x8e3a crcfinal=0x8799
   t0=20298 t1=21274167 errors=1
PASS: coremark cycles=21275738 instrs=10106387 bubbles=1243809 cpi=2.105
```

| 指标 | 值 | 口径 |
|:---|:---|:---|
| 计时窗口 ticks（t1−t0） | 21,253,869 | 移植层官方 start/stop 读计数器（契约 §5.3） |
| CoreMark/MHz | **1.506** | `32 × 1e6 / 21,253,869`，仿真外推口径（不满足官方 ≥10s） |
| CoreMark 分数（标称 100 MHz） | ≈150.6 iter/s | 仅参考，不作正式上报 |
| CPI（全局口径） | 2.105 | tb 全局 cycles/instrs，含初始化；仅供体检 |
| CRC 判据 | 4 常数 + golden 全对 | 契约 §5.1（errors_raw=1 为官方 <10s 计数，不作判据） |

## 备注

- 哈佛加载器语义：镜像同时预载 IMEM/DMEM（`.data` 初值与 `.rodata` 跳转表可读），见契约 §3.2 注释与 `tb_core_coremark.v`
- 板上 soc_top 需支持 DMEM 预载后此镜像才可直接上板（契约 §7.2 未决项 #7）
- `run_v0_32iter_preexp.log` 为未加 `+exp_*` 的首次通过记录（同结果）
