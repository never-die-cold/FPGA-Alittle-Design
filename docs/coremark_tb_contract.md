# CoreMark 基准 testbench 契约

> 状态：草案全文完成（2026-09-23，§1–§7；待 §7 列出的未决项收口后转"已冻结 v1.0"）
> 起草：基准线（`dev/bench`）｜消费者：基准线（移植层）、验证线（tb/回归/证据）、RTL 线（存储/计数器）
> 依据：`docs/core_comparison.md`（执行决策）、`src/riscv/design_v0.md`（接口唯一权威）、`sim/riscv/tb_core_coremark.v`（既有通用 tb）
> 本文与 `design_v0.md` 冲突时以 `design_v0.md` 为准，并立即修正本文；变更流程见 §7。

## 1. 目的与范围

### 1.1 为什么要有这份契约

CoreMark 是本项目唯一正式基准（`docs/core_comparison.md` §1 决策 1），它横跨三条线：
移植层决定程序写什么、tb 决定怎么判、RTL/SoC 决定硬件提供什么。
三者任何一处对不上（如 2026-09-15 `muldiv` 接口缺口），都要在实现之后返工。
本契约把接口、观测、判据在写码前冻结，作为仿真跑分 PASS/FAIL 的唯一判定依据。

### 1.2 范围（本文管什么）

- 仿真侧（iverilog）：镜像加载、运行、结果观测与判据
- 四档对比口径：v0 / v1 无转发 / v1+转发 / v1+BHT（同 hex、同 tb，只换 RTL）
- 与板上跑分共享的接口：计时计数器语义（板上正式 ≥10s 跑分流程不在本文）

### 1.3 不做什么

- 不定义 CoreMark 算法本身的实现（以 EEMBC 官方源码为准）
- 不替代 `design_v0.md` 的核接口权威（本文只引用其 §3 / §5.7 / §8）
- 不覆盖上板流程、综合与时序约束、PicoRV32 对比（见 `docs/core_comparison.md` §4）

### 1.4 读者与角色

| 角色 | 线 | 在本文中负责 |
|:---|:---|:---|
| 移植层 | 基准线 `dev/bench` | `core_portme.c/h` + 适配；产出 `coremark.hex`、golden、原始输出 |
| testbench | 验证线 `dev/verify` | `tb_core_coremark.v` 维护与判据扩展；回归与证据归档 |
| 存储/计数器 | RTL 线 `dev/rtl` | 32KB 存储实现（8B）、SoC 计时计数器（本文 §3 提案待其确认） |

### 1.5 与既有文档的关系

| 文档 | 关系 |
|:---|:---|
| `src/riscv/design_v0.md` | 接口唯一权威；本文引用其 §3（存储）、§5.7（core_top）、§8（tohost 约定） |
| `docs/core_comparison.md` | 执行决策与指标定义（CoreMark/MHz、四档、仿真外推口径） |
| `sim/riscv/tb_core_coremark.v` | 既有通用 tb；本文冻结的 plusargs/判据以它为基础并向后兼容 |
| `report/llm_log/2026-09-23-coremark-tb.md` | 通用 tb 的落地记录与理解门槛 |

## 2. 依赖现状与未决项（2026-09-23 快照）

### 2.1 已就绪

- 存储契约（8A）：IMEM/DMEM 8192×32、`addr[14:2]`、DMEM 异步读、`tohost` 地址不变（已随 PR #32 并入 main）
- RV32IM 核：`muldiv` 整核冒烟 PASS（`bash sim/scripts/run_iverilog.sh rv32im`）
- 通用 tb：`tb_core_coremark.v` 可运行（`+hex` 冒烟、plusargs 参数化、写事件判结束）
- 回归脚本五档：`v0 | fwd | muldiv | rv32im | all`

### 2.2 未决项（阻塞与排期）

| # | 未决项 | 现状 | 责任线 | 阻塞了本文哪节 |
|:--:|:---|:---|:---|:---|
| 1 | 8B 存储模型实现（RTL/固件/链接统一 32KB） | 未开始 | RTL 线 | §4 运行前提；§6 `coremark` 回归模式 |
| 2 | 计时计数器（地址/读时序/RTL） | 未开始；本文 §3 提案 | RTL 线确认 | §3 冻结 |
| 3 | `coremark.hex` 移植层 | 未开始 | 基准线 | §4/§5 判据全部 |
| 4 | crcfinal golden（PC 同源 32 迭代） | 未开始 | 基准线出、验证线复核 | §5 判据 |
| 5 | 观测块判据扩展（tb 读取 CRC 字段） | 未开始；按需 | 验证线 | §4/§5 判据完整性 |
| 6 | `coremark` 回归模式接入 `run_iverilog.sh` | 等 #1 | 验证线/基准线 | §6 运行入口 |

### 2.3 依赖链与开工顺序

- #3（移植层）依赖 #1（32KB 实现）与 #2（计数器地址冻结）
- #5（tb 判据扩展）依赖 #3 产出的镜像与观测块；#4（golden）可与 #3 并行
- #6（脚本模式）依赖 #1，避免与 RTL 线改同一文件造成分叉（见 `report/llm_log/2026-09-23-coremark-tb.md` §2/§3）

## 3. 接口契约

> 本节冻结"程序 ↔ 硬件（tb 模型 / SoC RTL）"的接口。与 `design_v0.md` 冲突时以 `design_v0.md` 为准。
> 计时计数器为**提案**：地址/时序待 RTL 线确认后回写 `design_v0.md` §3.3；确认前只影响 §6 的运行参数，不阻塞其他节。

### 3.1 核对外接口（引用，不重复定义）

- `core_top` 端口：`imem_addr/imem_rdata`（读数据**下一拍**有效）、`dmem_addr/dmem_wdata/dmem_be/dmem_we/dmem_rdata`（读数据**同拍**有效）——见 `design_v0.md` §5.7
- 核内无存储器；全部存储与 MMIO 由 tb 模型（仿真）或 `soc_top`（板上）提供，两处必须同语义

### 3.2 存储模型与地址地图

| 项 | 约定 | 出处 |
|:---|:---|:---|
| IMEM | 8192×32（32KB），**同步读**，`addr[14:2]` 索引，`$readmemh` 预载 `coremark.hex` | 8A 契约 / `design_v0.md` §3.1 |
| DMEM | 8192×32（32KB），**异步读**，4 位字节写使能，上电全 0（不预载） | 8A 契约 / `design_v0.md` §3.2 |
| 地址空间 | 两侧均 `0x8000_0000–0x8000_7FFF`；哈佛分离 | `design_v0.md` §3.3 |
| `tohost` | `0x8000_3FF0`（字索引 `0x0FFC`），程序写结果值 | `design_v0.md` §8 |
| `tohost_exit` | `0x8000_3FF4`（字索引 `0x0FFD`），程序写退出码 | `design_v0.md` §8 |
| 观测块 | **提案**：`0x8000_7F00–0x8000_7FFF`（64 字），linker 排除，字段表见 §4 | 本文 §4 |
| 计时计数器 | **提案**：`0x8000_8000`，只读，语义见 §3.3 | 本文 §3.3 |

- 观测块放 DMEM 顶部：tb/Soc 都按 `addr[14:2]` 直接索引，且与 CoreMark 数据/栈区（链接脚本安排在中低部）物理隔离
- 计时计数器放 32KB 之外：DMEM 内任何地址都是合法数据地址，MMIO 放进去会与程序数据访问产生歧义（误写不可见）；放界外后译码无二义

### 3.3 计时计数器（提案，待 RTL 线确认）

| 项 | 约定 |
|:---|:---|
| 形态 | 32 位自由运行计数器（每 `clk` 加 1），复位释放后从 0 起计 |
| 地址 | `0x8000_8000`（**提案值**，待 RTL 线确认后入 `design_v0.md` §3.3） |
| 读语义 | **同拍组合读**：地址给出的当拍返回当前计数值；与 DMEM 异步读一致（`lw` 无需额外等待） |
| 写语义 | 只读；程序不得对该地址写（写被忽略 / 未定义，契约直接禁止） |
| 位宽/回绕 | 32 位无符号自然回绕；软件用 `end - start`（模 2^32）算经过周期数，区间 < 2^32 拍时恒正确 |
| 频率 | 等于核时钟；仿真中 1 tick = 1 周期 |
| 仿真对应 | tb `+timer_addr=<HEX>` 时该地址读返回 `cycle_count`（既有实现）；未给参数时计数器不存在（移植层需禁用计时路径或改用仿真专用构建） |

- 板上实现要求（RTL 线）：`soc_top` 内计数器 + 地址译码，读路径与 DMEM 一致；确认后把地址写入 `design_v0.md` §3.3
- 计数器不参与功能判据；只服务移植层 `get_time()` 的起止打点（评分口径见 §5）

### 3.4 复位、时钟与看门狗

| 项 | 约定 |
|:---|:---|
| 时钟 | 仿真周期 10 ns（标称 100 MHz，仅影响秒数换算，不影响 CoreMark/MHz） |
| 复位 | `rst_n=0` 保持 8 拍后释放；复位后 PC=`0x8000_0000`，计数器从 0 起 |
| 看门狗 | tb `+max_cycles=<N>`；运行时必须显式给值；N ≥ 同配置实测最坏周期 × 2，首轮实测后于 §6 固化 |
| 超时判据 | 未观察到 `tohost_exit` 写事件即 FAIL（tb 既有行为），打印 PC / `tohost` 现场 |

## 4. 镜像与观测契约

### 4.1 源码基线与移植边界

- 源码：EEMBC 官方 `github.com/eembc/coremark`；拉取 commit 哈希、日期与全部使用文件的 **SHA-256** 入 `data/evidence/`
- **不得改动**（官方成绩规则）：算法文件 `core_list_join.c` / `core_matrix.c` / `core_state.c`、`core_util.c`、`coremark.h`
- 允许改动：`core_portme.c/h`（移植层）；`core_main.c` 只允许加"结果导出钩子"（把 CRC/ticks 写观测块），改动 diff 入证据
- 仿真档（冻结）：2K performance profile——`TOTAL_DATA_SIZE=2000`、seeds `0/0/0x66`（经 `core_portme.c` 的 volatile seeds 通道给定）、`ITERATIONS=32`、三个算法全跑、`MEM_METHOD=MEM_STATIC`（不用 malloc/堆）
- 编译参数（与 `src/riscv_fw/Makefile` 一致）：`-march=rv32im -mabi=ilp32 -mcmodel=medany -mno-relax -O2 -ffreestanding -nostdlib -nostartfiles`
- 注意：官方 `core_main.c` 的"<10s 计一次错误"在仿真必然触发（见 §5），`errors_raw` 字段会携带它，**只作证据不作判据**

### 4.2 链接与内存布局

| 区域 | 地址范围 | 要求 |
|:---|:---|:---|
| IMEM 代码 | `0x8000_0000` 起 | `.text` + `.rodata`，入口 `_start`；`coremark.hex` 按 `design_v0.md` §8 格式（每行 8 位十六进制小端字、行号 = 地址/4） |
| DMEM 数据 | `0x8000_0000` 起 | `.data` / `.bss` / 栈；不得落入 `tohost` 与观测块 |
| 栈 | linker 安排（建议 `.bss` 之后） | 大小 ≥ CoreMark 单线程所需；linker 必须显式预留并记录，不与下方保留区碰撞 |
| `tohost` | `0x8000_3FF0` | 保留；`.tohost` 段 KEEP，程序写 `crcfinal` |
| `tohost_exit` | `0x8000_3FF4` | 保留；程序写退出码（成功 0） |
| 观测块 | `0x8000_7F00–0x8000_7FFF` | **保留区**；linker 不得分配任何数据；字段表见 §4.3 |

- 哈佛双口同基址（`design_v0.md` §3.3）；链接脚本按 32KB 布局调整（基准线负责，8B 后统一）

### 4.3 观测块字段表（冻结）

观测块基址 `0x8000_7F00`（字索引 `0x1FC0`）；全部 32 位小端字；未列字全 0。

| 字# | 字节偏移 | 字段 | 写入者/时机 | 含义与取值 |
|:--:|:--:|:---|:---|:---|
| 0 | +0x00 | `MAGIC_ID` | 移植层，块首写 | `0x434D_4B31`（"CMK1"），标识本块属于一次 CoreMark 运行 |
| 1 | +0x04 | `iterations` | 移植层 | 实际迭代数（仿真档 = 32） |
| 2 | +0x08 | `seedcrc` | 移植层 | 预期 `0xe9f5`（2K profile 标识，等价于校验 seeds+size） |
| 3 | +0x0C | `crclist` | 移植层 | 官方列表算法 CRC |
| 4 | +0x10 | `crcmatrix` | 移植层 | 官方矩阵算法 CRC |
| 5 | +0x14 | `crcstate` | 移植层 | 官方状态机算法 CRC |
| 6 | +0x18 | `crcfinal` | 移植层 | 全迭代累计 CRC（迭代相关，判据用 golden） |
| 7 | +0x1C | `t_start` | 移植层 | 官方 `start_time()` 时刻的计数器读数 |
| 8 | +0x20 | `t_end` | 移植层 | 官方 `stop_time()` 后的计数器读数 |
| 9 | +0x24 | `errors_raw` | 移植层 | 官方框架 `total_errors` 原值（证据；含仿真 <10s 错误） |
| 10 | +0x28 | `DONE_MAGIC` | 移植层，**最后写** | `0x444F_4E45`（"DONE"），封口标志 |
| 11–63 | +0x2C+ | 保留 | — | 全 0 |

- 每个字段**恰好写一次**（`sw`，字对齐）；观测块写入必须先于 `tohost_exit`
- `t_start/t_end`：同一计数器两次读数，评分公式用 `t_end - t_start`（§5）；计数器语义见 §3.3

### 4.4 结束协议（程序 ↔ tb）

| 步骤 | 程序（移植层） | tb |
|:--|:--|:--|
| 1 | 运行官方 `core_main` 主流程 | 正常仿真，统计周期/指令/气泡 |
| 2 | 按 §4.3 写观测块（`DONE_MAGIC` 封口） | — |
| 3 | `tohost = crcfinal`（零扩展 32 位） | — |
| 4 | `tohost_exit = 0`（成功）/ 非 0（移植层自检失败码） | — |
| 5 | 死循环自旋（不返回） | 检测到 `tohost_exit` **写事件**即结束（不看值等 0；成功值 0 与上电初值 0 不可区分——既有 tb 实现） |
| 6 | — | 退出后读观测块，按 §5 判据判定；超时（`+max_cycles`）则 FAIL 并打印现场 |

- tb 既有接口兼容：`+exp_tohost` 可直接校验 `crcfinal`；观测块判据扩展属未决项 #5（§2.2）
- 观测块缺 `MAGIC_ID`/`DONE_MAGIC` 或字段未写 → 视为镜像不合格（FAIL），不进入 CRC 判定

## 5. 判据契约

### 5.1 功能判据（PASS 条件，全部满足才算 PASS）

| # | 判据 | 期望 | 依据 |
|:--:|:---|:---|:---|
| 1 | `tohost_exit` | `0` | `design_v0.md` §8 退出码约定 |
| 2 | 观测块封口 | `MAGIC_ID=0x434D_4B31` 且 `DONE_MAGIC=0x444F_4E45` | §4.3 镜像有效性 |
| 3 | `iterations` | `32` | §4.1 仿真档冻结 |
| 4 | `seedcrc` | `0xe9f5` | 官方 2K performance profile 指纹（seeds+size+算法集合） |
| 5 | `crclist` | `0xe714` | 官方 `core_main.c` `list_known_crc[3]`（known_id=3） |
| 6 | `crcmatrix` | `0x1fd7` | 官方 `matrix_known_crc[3]` |
| 7 | `crcstate` | `0x8e3a` | 官方 `state_known_crc[3]` |
| 8 | `crcfinal` | golden（32 迭代） | §5.2 生成与复核 |
| 9 | `tohost` | 等于 golden（零扩展 32 位） | §4.4；现有 tb 用 `+exp_tohost` 校验，无需扩展 |

- 判据 5–7 与迭代数**无关**（源码时机：`crclist` 在首迭代末尾赋值，`crcmatrix/crcstate` 在首次调用时赋值），可直接写死
- 判据 8/9 与迭代数**相关**（`crcfinal` 是全迭代累计），必须比对 golden

### 5.2 golden 生成与复核（`crcfinal`）

| 步骤 | 负责 | 内容 |
|:---|:---|:---|
| 生成 | 基准线 | 同一份官方源码、同一 profile（§4.1）、`ITERATIONS=32`，在 PC 侧用 gcc 原生编译运行，打印 `crcfinal`；命令、编译器版本、defines、原始输出一并入 `data/golden/coremark_2k_32iter/` |
| 复核 | 验证线 | 独立环境重算（不同机器/编译器版本）比对；三常数与官方公开值一致性作为管线自检 |
| 冻结 | 双方 | 两路一致后写入 golden 文件并记 hash；不一致 → **冻结交付、查清差异，禁止选一个先用**（金标准不允许二选一） |
| 使用 | 运行者 | `+exp_tohost=<golden>` 叠加上表判据；golden 变更须走 §7 |

- 前提：`crcfinal` 不含时间量，只由算法结果累计，故跨平台可复现；复核正是为了验证该前提在本移植上成立

### 5.3 性能判据与评分公式

- 计时窗口：移植层官方 `start_time()`/`stop_time()` 两次计数器读数，`ticks_elapsed = t_end - t_start`（无符号模 2^32，§3.3）
- 公式（推导：score = iterations / 秒数；秒数 = ticks / (f×10^6)；故 score / f = iterations×10^6 / ticks，频率约去）：

```text
CoreMark/MHz = iterations × 1_000_000 / ticks_elapsed
```

- 仿真周期 10 ns 只影响"秒数"换算，**不影响** CoreMark/MHz；四档对比用同一公式、同一迭代数
- tb 的全局 `cycles/instrs/bubbles/CPI` 只作健康检查与报告，**不参与**评分（评分必须与板上同口径）
- 四档对比判据：同一 hex + 同一 golden；**CRC 判据必须四档全等**（优化不改语义）；CoreMark/MHz 按档记录，入 `docs/core_comparison.md` §2/§5 与 `data/metrics.csv`
- 有效性层级：
  - 仿真（本文）：功能有效性 = §5.1 + §5.2；成绩按"仿真外推口径"注明（短迭代，不满足官方 ≥10s）
  - 板上（M3，`core_comparison.md`）：官方 ≥10s 有效性；用实测频率换算 score；观测协议与本文相同

### 5.4 官方 10 秒陷阱（显式禁令）

- 官方 `core_main.c` 在运行时间 < 10 秒时执行 `total_errors++` 并打印 `ERROR! Must execute for at least 10 secs`；仿真 32 迭代（约百万周期量级）必然触发
- **禁止**把程序侧 `errors_raw`、"Errors detected"、或缺少 "Correct operation validated" 作为 FAIL 判据——程序在仿真下必然报错，这不是硬件错误
- `errors_raw` 仅作证据字段（§4.3）用于对照排查；仿真判据只看 §5.1

### 5.5 失败诊断输出（最低要求）

- 单项判据不符：打印判据编号、期望值、实际值（十六进制）
- 整体 FAIL：附带 `cycles`、`tohost`/`tohost_exit` 值、`PC`、观测块全字段 dump，便于定位镜像/移植/硬件问题
- 原始日志归档 `data/logs/`（路径与命名见 §6.3）

## 6. 运行与证据

### 6.1 运行入口

手动（当前可用；在 `sim/` 下执行）：

```bash
iverilog -g2012 -Wall -o build/tb_core_coremark.vvp riscv/tb_core_coremark.v ../src/riscv/*.v
vvp build/tb_core_coremark.vvp +hex=<镜像> +exp_exit=0 +timer_addr=80008000 +max_cycles=<N> [+exp_tohost=<golden>]
```

回归脚本（8B 合入后）：`bash sim/scripts/run_iverilog.sh coremark`——**单独模式**，`coremark.hex` 稳定前不进 `all`（避免拖慢常规回归）。

### 6.2 plusargs 约定（既有 tb 接口，冻结）

| plusarg | 默认 | 用途 |
|:---|:---|:---|
| `+hex=<路径>` | `../src/riscv_fw/coremark.hex` | 固件镜像（`$readmemh` 预载 IMEM） |
| `+exp_tohost=<值>` | 不校验 | 校验 `tohost`（= `crcfinal` = golden） |
| `+exp_exit=<值>` | `0` | 校验退出码 |
| `+max_cycles=<N>` | `10000000` | 看门狗；CoreMark 运行**必须显式给值** |
| `+timer_addr=<HEX>` | `0`（关） | 计时计数器地址；本文提案 `80008000`，确认后固化 |
| `+vcd` | 关 | 导出波形（调试用，不用于回归） |

看门狗取值：首轮四档实测后取 `N = 2 × 最坏配置周期数` 写入本表（**当前未定，未决项 #6**）；在此之前运行者按保守上界给值。

### 6.3 证据归档

| 产物 | 位置 | 要求 |
|:---|:---|:---|
| 原始日志 | `data/logs/YYYY-MM-DD-coremark/` | 四档各一份；附运行命令、参数、commit hash |
| golden | `data/golden/coremark_2k_32iter/` | golden 值 + 生成/复核命令 + 源码 SHA-256（§5.2） |
| 指标 | `data/metrics.csv` | 增行：CoreMark/MHz、CoreMark/LUT；测量条件按 `data/README.md` 填全 |
| 对比表 | `docs/core_comparison.md` §2/§5 | 刷实测值（四档 + 引用数据口径） |

### 6.4 四档运行矩阵（M1 内完成）

| 配置 | RTL 来源 | hex/golden | 判据 |
|:---|:---|:---|:---|
| v0（两级锚点） | main 当前 | 同一 `coremark.hex` + 同一 golden | §5.1 全部通过 |
| v1 无转发 | Part B 阶段标签 | 同上 | 同上；CRC 与 v0 全等 |
| v1+转发 | Part B/C | 同上 | 同上 |
| v1+BHT | Part C | 同上 | 同上；另记命中率 |

- 四档的成绩按 §5.3 公式分别记录；**任一档 CRC 与 golden 不符即该档 FAIL**，不得进入对比表
- 所有运行必须可由仓库内命令一键复现（项目铁律：禁止临时文件/手工改数）

## 7. 变更控制与未决项收口

### 7.1 变更规则

- 本文转"已冻结 v1.0"后：任何改动走 PR；涉及接口/判据的改动须 ① 受影响线在 PR 确认 ② `report/llm_log/` 留决策记录 ③ 同步更新引用方（`sim/README.md`、`docs/core_comparison.md`）
- 与 `design_v0.md` 冲突：以 `design_v0.md` 为准并立即修正本文（§1.5）

### 7.2 未决项收口（标志达成即关闭）

| # | 未决项 | 收口标志 |
|:--:|:---|:---|
| 1 | 8B 存储模型实现 | RTL/固件/tb 统一 8192×32，五档回归 PASS |
| 2 | 计数器地址确认 | 地址写入 `design_v0.md` §3.3；本文 §3.3 去"提案"字样 |
| 3 | `coremark.hex` 移植 | 镜像入库且 `+hex` 冒烟 PASS |
| 4 | crcfinal golden | 两路结果一致并入库 `data/golden/` |
| 5 | 观测块判据扩展 | tb 能按 §5.1 全 9 条判（或由运行脚本外部判） |
| 6 | `coremark` 回归模式 | `run_iverilog.sh coremark` 可用并写入 `sim/README.md` |

### 7.3 变更记录

| 日期 | 变更 | 关联 |
|:---|:---|:---|
| 2026-09-23 | 起草 §1–§2：范围/角色/依赖现状 | `report/llm_log/2026-09-23-coremark-tb-contract.md` |
| 2026-09-23 | 起草 §3：接口契约（存储/地址/计数器提案/时序/看门狗） | 同上 |
| 2026-09-23 | 起草 §4：镜像与观测契约（观测块字段表/结束协议） | 同上 |
| 2026-09-23 | 起草 §5：判据契约（CRC/golden/公式/10s 禁令） | 同上 |
| 2026-09-23 | 起草 §6–§7：运行/证据/变更控制与未决项收口 | 同上 |
