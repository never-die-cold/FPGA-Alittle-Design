# sim —— 仿真脚本与结果

各模块 testbench、仿真脚本与波形结果。**所有 RTL 模块必须先过仿真再上板。**

## 规划结构

```
sim/
├── riscv/           # RISC-V 核各级、整核与 SoC 外壳 testbench
├── coprocessor/     # 协处理器 testbench
├── vision/          # 预处理流水线 testbench（含测试图样生成）
├── scripts/         # xsim 批处理脚本（可复跑）
└── tools/           # 辅助工具（RV32I 编解码自测等）
```

辅助工具用法：`python sim/tools/verify_rv32i.py`（阶段 0 指令编码自测：22 组汇编→机器码 + 10 组反汇编双向校验，输出 `ALL OK` 即通过）

## 仿真工具（双工具复核对拍，2026-09-14 更新）

- **主力回归**：Icarus Verilog 13.0（MSYS2 ucrt64 包 `mingw-w64-ucrt-x86_64-iverilog`）——一键跑全部 tb
- **XSim 复核**（Vivado 2026.1 已装，issue #2）：同一套 tb 已复核对拍，**两工具结论一致**（2026-09-14；`xvlog → xelab → xsim -R`，从 `sim/` 目录运行以保证 `$readmemh` 相对路径正确）
- 用法（MSYS2 UCRT64 shell 中，产物在 `sim/build/`）：
  - 一键跑全部：`bash sim/scripts/run_iverilog.sh`；两档回归：`bash sim/scripts/run_iverilog.sh v0`（冒烟 + 逐指令）/ `fwd`（转发专项）
  - `tb_core_smoke.v`：加载 `src/riscv_fw/hello_v0.hex`，检查 `tohost==13 && tohost_exit==0`（程序级冒烟）
  - `tb_core_test.v`：加载 `src/riscv_fw/hello_test.hex`，检查 `tohost_exit==0`（RV32I 逐指令自检 38 用例；失败值为用例编号）
  - `tb_core_fwd.v`：加载 `riscv/fwd/fwd_test.hex`（转发专项，Part B 测试先行）——数据冒险零气泡 + taken 分支 1 拍契约，气泡/结果双自检
- tb 接口以 [`src/riscv/design_v0.md`](../src/riscv/design_v0.md) 为唯一权威

> 当前状态：v0 核（RV32I）两个 tb 均 PASS（2026-09-11 iverilog；2026-09-14 XSim 复核对拍一致），见 `report/llm_log/2026-09-14-vivado-2026-1-acceptance.md`

## v0 八模块验证观察点（仿真时看什么、怎么判对错）

> 这是给写 testbench 的人用的「看对错清单」：每个模块在仿真里**要看什么、什么算对、什么算错**。
> 判据以 [`src/riscv/design_v0.md`](../src/riscv/design_v0.md) 为唯一权威；目前只有整核级的两个 tb，模块级 tb 还没写。
> `muldiv` / `soc_top` 还没有 RTL（只有空壳），先按契约写好观察点，等 RTL 到位直接用。

| 模块 | 出处 | 观察点（看什么、怎么判对错） | 现有覆盖 |
|:---|:---|:---|:---|
| `pc` | §5.1 | 复位后 PC 从 `0x8000_0000` 起步；没跳转时每拍 +4，跳转时下一拍变成目标地址；`stall=1` 时即使来了跳转 PC 也保持不动。**判错**：跳转后停着不走，或一次跳两格（+8） | 整核 tb 间接覆盖 |
| `if_stage` | §5.2 | 复位后第一拍只输出空指令（`instr=NOP`）且 `instr_valid=0`，保证第一条指令不被执行两次；分支/跳转生效后，下一拍必须**恰好是 1 拍 NOP**——这就是从波形数气泡的锚点。**判错**：气泡 0 拍或 2 拍 | 整核 tb 间接覆盖 |
| `decode` | §5.3 / §6 | 拿各类代表指令对照真值表逐条查控制信号；重点：B/J 型立即数最低位有没有补 0、`lui` 时 ALU 的 a 端是不是固定为 0、`jal/jalr` 写回的是不是 PC+4、load 的符号/零扩展对不对、`fence/ecall/ebreak` 这类系统指令有没有被当 NOP。**判错**：`funct7[5]` 区分不出 ADD/SUB 或 SRL/SRA。M 扩展的 `muldiv_op` 目前是占位映射（已知缺口） | 整核 tb 间接覆盖（38 用例） |
| `regfile` | §5.4 | 往 `x0` 写东西再读出来必须还是 0；寄存器堆是「组合读、时钟沿写」，所以一条指令在拍末写回，下一条紧跟着的指令当拍就能读到新值——这正是 v0 没有数据停顿的原因。注意：同一拍写读同一个寄存器读到的是旧值；寄存器没有复位，上电是未知值 X，测试程序必须先写后读 | 整核 tb 间接覆盖 |
| `alu` | §5.5 / §6.1 | 每种运算抽边界值查：负数的算术右移（SRA）、有符号与无符号比较（SLT vs SLTU）、移位只认 b 的低 5 位。`zero/lt/ltu` 三个标志由 a、b 直接比较得出，和结果同拍。**判错**：没定义的运算编码会被当 ADD 处理，而不是报错 | 整核 tb 间接覆盖 |
| `muldiv` | §5.6 | RTL 未实现（空壳），先按契约查：`op` 两位能不能区分 8 种乘除运算（**目前分不出，是已知缺口**）；`busy` 忙时 PC 和指令要停住、寄存器不许写、忙结束只写一次 rd；`start` 只能触发一次、`busy` 期间不能重复启动；除法四个边界（除零、`INT_MIN/-1`） | 待建 |
| `core_top` | §5.7 / §2 | 第 k 拍给出的指令地址，第 k+1 拍才拿到对应指令（指令存储器延迟恰好 1 拍）；分支目标是「本指令的 PC + 立即数」；`jal/jalr` 无条件跳转、每次都**恰好 1 拍气泡**；`jalr` 目标地址末位清 0；`lw` 当拍就能写回、字节使能只在写的时候有效。**判错**：跳转没清气泡、`jalr` 末位没清、`lw` 多等一拍 | `tb_core_smoke` + `tb_core_test` |
| `soc_top` | §5.8 | RTL 未实现（空壳；板卡 2026-09-20 到货并验证，上板观察点启用）。仿真里：能预载 hex、指令存储器同步读（本拍地址、下拍出数据）、数据存储器异步读 + 4 位字节写使能、复位后 PC 对。上板：LED 按分频周期闪、JTAG 下载成功 | 待建 |

> `muldiv` 的接口缺口（`op` 只有 2 位、装不下 RV32IM 的 8 种运算等）详见 [`report/llm_log/2026-09-15-muldiv-interface-gap.md`](../report/llm_log/2026-09-15-muldiv-interface-gap.md)。

## 转发专项测试（Part B 测试先行，2026-09-20 建立）

- 被测程序：`riscv/fwd/fwd_test.S`（生成 `fwd_test.hex/.dis` 入库）；构建：`bash sim/scripts/build_fwd.sh`
- 判据（v0 对照档）：阶段 A（R 型连读）气泡 0、阶段 B（lw→运算）气泡 0、阶段 C（taken 分支/跳转）气泡 = 5、阶段 D（not-taken 分支）气泡 0；各阶段结果与期望常数逐一比对
- v1 接入：用 `+exp_a/+exp_b/+exp_c/+exp_d` 覆盖期望（如 v1 无预测档 `+exp_b=4`），机制演示见 `data/logs/2026-09-20-fwd-baseline/plusarg_override_demo.log`
- 证据与对照数据：`data/logs/2026-09-20-fwd-baseline/`；口径决策：`report/llm_log/2026-09-20-v0-no-stall-cpi-reframe.md`

## riscv-arch-test 接入（第三方「优化不改语义」判据，2026-09-20 建立）

- 套件：`riscv-non-isa/riscv-arch-test` `old-framework-2.x`（自带 `references/*.reference_output` 参考签名）；获取：`bash sim/scripts/fetch_arch_test.sh`（克隆到 `sim/arch_test/suite/`，不入库）
- 目标配置：`sim/arch_test/target/pynq_z2_v0/`（`model_test.h` + `env/link.ld` + 框架 Makefile 配置），编译经套件的 `make` 流程驱动
- 跑法：`bash sim/scripts/run_arch_test.sh <测试名>`（默认 `add-01`）——编译 → 统一镜像双预载 → 逐字签名比对 → PASS/FAIL；签名输出兼容框架 `make verify` 的文件约定
- 已纳入回归：`add-01` / `addi-01` / `and-01` 全 PASS；证据与边界：`data/logs/2026-09-20-arch-test/`
- 说明：arch-test 需要 ELF 编译流程，不并入 `run_iverilog.sh`（后者只跑源码级 tb）

## 约定

- 每个 testbench 输出 PASS/FAIL 自检结果，禁止只靠肉眼看波形
- 关键波形截图归档到 `report/`，供设计报告引用
- 黄金参考数据放 `data/`，仿真比对脚本引用相对路径

> 状态：🚧 进行中（v0 核 RV32I 已过冒烟与逐指令自检；转发专项 v0 对照基线已建立，2026-09-20）
