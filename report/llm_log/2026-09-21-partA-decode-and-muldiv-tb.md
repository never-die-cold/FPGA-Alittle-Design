# [2026-09-21] 协作记录：Part A 古法编程——RV32M 模块级自检 tb、回归接入与第 7A 步译码

> 标签：#riscv #工具链 #验证 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `bf4a180`；本轮改动为 `src/riscv/decode.v`、`sim/riscv/tb_muldiv.v`（新增）、`sim/scripts/run_iverilog.sh`（与本文档同批提交，哈希回填）

## 1. 任务与初始提示词

发现“设备上能验的东西没落库”，先要求写可复现的模块级测试，再做核内接入的第一步：

> 今天要验证的新程序是 `src/riscv/muldiv.v`（RV32M 乘/除，PR #30）。但它还没接入核：`core_top.v` 里仍是 `stall=1'b0`、`muldiv_op` 只有 2 位、没有 muldiv 实例；`decode.v` 的 `muldiv_op` 也还是 2 位……没有任何模块级 testbench（main / dev/rtl / dev/verify 三个分支都没有）……今天能做的最有价值的独立验证是——给它写一个模块级 testbench，直接驱动 muldiv 跑 8 种运算 + 边界。

Codex 指出新增 `sim/riscv/tb_muldiv.v` 会触碰验证线的 `sim/`，请求跨目录授权；我明确授权后开始。随后把原“第 7 步接入”拆为 7A（译码）/7B（核内接入）。

## 2. 模型第一版方案

- **新增 `sim/riscv/tb_muldiv.v`（74 行）**：覆盖八种操作（`mul/mulh/mulhsu/mulhu/div/divu/rem/remu`）、有/无符号与混合符号、除零、`INT_MIN/-1`；检查 `start→busy→done` 握手、精确 32 拍 `busy`、忙时二次 `start` 被忽略、`done` 单拍、`result` 完成后保持、异步复位取消；兼容 Icarus 与 XSim 并输出 VCD。
- **接入 `sim/scripts/run_iverilog.sh`**：新增 `muldiv` 单测模式，并把 `tb_muldiv` 加入 `all` 全量回归。
- **第 7A 步 `decode.v`**：`muldiv_op` 由 2 位扩为 3 位、新增 `muldiv_valid`；`funct7==7'h01` 时识别为 M 指令，`muldiv_op = funct3`，`wb_sel = WB_M(2'b11)`，`reg_write=1`（留待 7B 用 `done` 门控实际写回）。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **验证资产没落库**：此前乘除单元只有 `/tmp` 里的临时 tb，已被环境清理，不可复现，也不能作为 Vivado 验收材料——所以先补可复现的模块级 tb。
2. **Verilator 4.038 不支持新版 `--timing`**：无法 lint 含 `#` 延时的 testbench；只对可综合的 `muldiv.v` 单独 lint（通过）。
3. **环境无 Vivado/XSim**：不能代跑 XSim；tb 按现有 XSim 风格书写以保证兼容。且 `muldiv` 尚未接入 `core_top`，核心级/上板级 RV32M 暂时无法验证。
4. **预期中的跨步宽度警告**：`decode.v` 已变 3 位，但 `core_top.v` 仍是 2 位连线，出现 `Port 19 (muldiv_op) ... expects 3 bits, got 2`；留到 7B 消除。当前 M 指令尚不能安全进整核（`core_top` 未用 `done` 门控 `reg_write`）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | “为什么 VSCode 里没有代码改动” | 上一轮是接口审计，结论无需改 RTL，故无改动 | 无 | ✅ 澄清（代码早已在 `d4c1649`/`745d3b3`） |
| 2 | 没有可复现的模块级 tb | 临时 `/tmp` tb 被清理，不可作验收材料 | 新增 `sim/riscv/tb_muldiv.v`（跨目录已授权） | ✅ Icarus `PASS: muldiv 8 operations, boundaries and handshake` |
| 3 | tb 未进回归 | 只跑 RV32I 整机会完全碰不到未接入的 muldiv，改坏也发现不了 | `run_iverilog.sh` 增加 `muldiv` 模式并纳入 `all` | ✅ 全量回归（冒烟/38 项/转发/RV32M）全 PASS |
| 4 | `decode.v` 的 `muldiv_op` 仍是 2 位 | 需按契约扩 3 位并区分 M 指令；拆出 7A 单独做译码 | `muldiv_op` 3 位 + `muldiv_valid` + `WB_M` | ✅ 八种 M 译码定向 PASS；`core_top` 宽度警告留 7B |

## 5. 最终结论

本轮完成三件事：① 可复现的 RV32M 模块级自检 tb（`sim/riscv/tb_muldiv.v`）；② 回归脚本接入（`muldiv` 单测模式 + `all` 全量含它）；③ 第 7A 步 `decode.v` 完整 RV32M 译码。验证：`PASS: muldiv 8 operations, boundaries and handshake`、`PASS: decode all 8 RV32M operations`；全量回归 RV32I 冒烟 / 38 项自检 / 转发气泡 / RV32M 模块全 PASS；Verilator 对 `muldiv.v`、`decode.v` lint 通过；`git diff --check` 通过。待办：7B 在 `core_top.v` 例化 `muldiv`、用 `done` 门控写回并消除宽度警告；Vivado 核心级/上板级验证需等 7B。

## 6. 经验沉淀

- 触发条件：功能单元尚未接入顶层，却要做可信验证；或只有临时、不可复现的测试。
- 排查步骤：
  1. 未接入核的模块**必须做模块级 tb**——整机回归碰不到它，改了坏了也全绿；
  2. 验证资产要**落库可复现**（`sim/` 下、进回归脚本），`/tmp` 临时测试不算证据；
  3. 新增 tb 同时提供**单独快速模式**（开发时）与 **`all` 全量档**（长期防线）；
  4. 译码区分 M 指令不能只看 `opcode`，必须带 `funct7`；写回必须用 `done` 门控，别把译码的 `reg_write` 直接接寄存器堆。
- 适用范围：换模块 / 换板卡 / 换仿真器均成立；“未接入就用模块 tb 兜底”可作通用验证范式。 #skill候选
