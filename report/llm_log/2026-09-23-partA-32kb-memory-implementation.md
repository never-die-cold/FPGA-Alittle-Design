# [2026-09-23] 协作记录：Part A 统一 32KB 存储器契约落地——固件重链接、仿真模型扩容、IMEM/DMEM RTL

> 标签：#riscv #架构决策 #验证 #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `f22f5a3`（8A 冻结 32KB 契约）；本轮 8B/8C/9A/9B 改动与本文档同批提交（哈希回填）

## 1. 任务与初始提示词

按已确认的 32KB 契约逐步落地（每步古法编程：先拆步、我确认后再动手；开工前照 `AGENTS.md` 三件事）：

> 8B：核对并调整 `link.ld`、`start.S`、`tohost`，必要时重新生成固件。
> 8C：把所有带存储模型的 tb 统一为 `8192×32` 和 `addr[14:2]`。
> 9A/9B：新增 `imem.v`（同步读）/ `dmem.v`（异步读 + 字节写）及模块级测试，接入 `run_iverilog.sh`。

## 2. 模型第一版方案

- **8B 固件**：`link.ld` 的 `LENGTH` 16K→32K；`_stack_top = ORIGIN(BRAM)+LENGTH` = `0x8000_8000`；加链接期断言防止静态段压到 `tohost`；用 `make -B CROSS=riscv64-unknown-elf-` + `bin2hex.py` 重建三套固件。
- **8C 仿真模型**：五个整核 tb 统一 `imem/dmem [0:8191]`、索引 `addr[14:2]`、初始化循环扩到 8192；`tb_core_fwd` 索引常量扩 13 位；arch-test 掩码 `0x3FFF`→`0x7FFF`、`ref_mem` 扩 8192。
- **9A `imem.v`**：8192×32、`$readmemh` 参数化预载（默认 `src/riscv_fw/hello.hex`）、`always @(posedge clk) rdata <= mem[addr[14:2]]`、`(* ram_style="block" *)`。
- **9B `dmem.v`**：8192×32、`assign rdata = mem[addr[14:2]]` 异步读、时钟沿按 `be` 字节写、`(* ram_style="distributed" *)`、上电清零。
- **`run_iverilog.sh`**：新增 `imem`/`dmem` 模式并纳入 `all`，编译加 `-s "$name"` 明确仿真顶层。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **工具链名不匹配**：WSL 无 `riscv32-unknown-elf-*`，用兼容 RV32 的 `riscv64-unknown-elf-*` 覆盖 `CROSS` 生成（产物仍留在仓库内，可复现）。
2. **8B 隐藏问题**：只改 `LENGTH` 不够——`_stack_top` 原仍是“静态段末尾 + 1KB”，新增 16KB 不会被栈使用；改为 `ORIGIN+LENGTH = 0x8000_8000` 并加断言。
3. **旧 tb 别名风险**：4096 深度 + `addr[13:2]` 会丢掉 `addr[14]`，高 16KB 访问绕回低地址，可能“侥幸 PASS”；8C 扩到 8192 才消除。
4. **Verilator 捕获真实可移植性问题**：IMEM 里未定宽字符串参数与空串比较导致宽度不一致 → 删除空路径判断，直接 `$readmemh`。
5. **iverilog 顶层问题**：不指定顶层时，未例化的 `imem` 也被当根模块执行 `initial` → 编译加 `-s "$name"`。
6. **arch-test 功能未运行**：仓库缺 `sim/arch_test/suite`，脚本在编译前明确退出（如实记录，不伪报为已验证）。
7. **无 Vivado**：`ram_style` 只是综合提示，BRAM/LUTRAM 实际映射与 Fmax 未测。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 无 `riscv32` 工具链 | 可用 `riscv64-unknown-elf-` 覆盖 `CROSS` | 仓库内重建并比对哈希 | ✅ 六个 `.hex/.dis` 哈希不变 |
| 2 | 只改 `LENGTH` 栈仍在低区 | `_stack_top` 未随容量变化 | 改 `_stack_top=0x8000_8000` + 链接断言 | ✅ 仅 `sp` 指令变，入口/`tohost` 不变 |
| 3 | 旧 tb 4096 深度会别名 | 丢 `addr[14]` 使高 16KB 绕回 | 五个 tb 统一 8192 / `addr[14:2]` | ✅ `all` 全绿，`tohost=142879` |
| 4 | IMEM 空串比较宽度不一致 | 未定宽参数与空串比较 | 删判断，直接 `$readmemh` | ✅ Verilator lint PASS |
| 5 | `imem` 被当额外顶层执行 | 未指定 top，`initial` 也运行 | 编译加 `-s "$name"` | ✅ `all` 只跑目标 tb |

## 5. 最终结论

今天完成 8B/8C/9A/9B：固件按 32KB 重链接（入口 `0x8000_0000`、`tohost 0x8000_3FF0`、`_stack_top 0x8000_8000`）、五个整核 tb 统一 `8192×32`/`addr[14:2]`、新增可综合 `imem.v`（同步读 + block 提示）与 `dmem.v`（异步读 + 字节写 + distributed 提示），并把模块测试接入 `run_iverilog.sh`。验证：`bash sim/scripts/run_iverilog.sh all` 全绿（RV32I smoke / 38 项 / 转发 / muldiv 模块 / imem / dmem / RV32IM `tohost=142879`），Verilator lint、`git diff --check` 通过。待办：10A SoC 仿真外壳（例化 `core_top+imem+dmem`，LED 锁存 `tohost` 低 4 位）、10B 板级时钟（MMCM，125 MHz > 86.8 MHz Fmax）、Vivado 资源/时序、补 arch-test suite。

## 6. 经验沉淀

- 触发条件：统一/扩容存储器契约——固件、仿真模型、RTL 三处必须同步。
- 排查步骤：
  1. 先改链接脚本容量 + 栈顶（`ORIGIN+LENGTH`）+ 链接断言；
  2. tb 的**数组深度与索引位宽必须一起改**，否则高区别名、假 PASS；
  3. IMEM 同步读放 `always` 块、DMEM 异步读用 `assign`；DMEM 不能写进 `always`，否则破坏 `lw` 同拍写回语义；
  4. 编译显式 `-s` 指定顶层，避免未例化模块的 `initial` 干扰；
  5. 资源映射（BRAM/LUTRAM）以 Vivado utilization report 为准，不凭容量折算断言。
- 适用范围：换板卡 / 换容量均成立；“固件-仿真-RTL 三同步 + 深度与索引成对改”可作通用清单。 #skill候选
