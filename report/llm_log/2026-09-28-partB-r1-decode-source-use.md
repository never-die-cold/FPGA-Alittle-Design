# [2026-09-28] 协作记录：Part B 契约冻结 + R1——decode 输出源操作数使用标志

> 标签：#riscv #架构决策 #流水线 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `473771e`（Part B 契约草案）；本轮“契约定稿 + R1”改动与本文档同批提交

## 1. 任务与初始提示词

两件事：① 完成 v1 契约剩余章节并冻结；② 阶段 2 首个 RTL 小步 **R1**——给 `decode.v` 增加 `uses_rs1/uses_rs2`，为转发/冒险提供“真实读取了哪些源寄存器”的判据（避免伪 RAW）。

## 2. 模型第一版方案

- **契约定稿**：`design_v1.md` 补 §11–§15——存储器与 regfile 三级语义、`forwarding.v`/`hazard.v`/`id_ex_stage.v`/`mem_wb_stage.v`/`core_top` 的端口与位宽、CPI/验证门禁、D1–D15 决策；状态清单全部勾选，用户最终确认冻结，进入阶段 2。
- **R1**：`decode.v` 新增两个组合输出 `uses_rs1`/`uses_rs2`——JALR/LOAD/IMM 置 `rs1`，BRANCH/STORE/REG 置 `rs1+rs2`，JAL/LUI/AUIPC 等不置；新增 `sim/riscv/tb_decode.v`（11 个语义用例）；`run_iverilog.sh` 增加 `decode` 模式并纳入 `all`。
- **收口文档**：`design_v0.md` 标记 Part A 完成（锚点 commit `962a4f5` / tag `partA-v0`）；`plan.md` 指标口径改为“记录实际最高通过频率/WNS，125 MHz 为非阻塞加分项”。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **写入工具仍被 WSL 挂载阻止**：`apply_patch` 报 `/mnt/wslg/distro` 嵌套挂载不受支持（同 09-27），改用仓库内 `python3` 写入同一段内容。
2. **CoreMark 耗时长**：全量回归含 CoreMark，约 2100 万周期、跑数分钟；期间只能等待自然结束，不能中断、也不能提前记为全绿。
3. **v1 RTL 尚未实现**：`forwarding.v`、`hazard.v`、`id_ex_stage.v`、`mem_wb_stage.v`、v1 `core_top` 都还没写；本轮是**契约冻结 + 译码准备**，不是三级重构完成。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 契约缺 §11–§15 且清单未勾 | 需补存储器/regfile、端口、门禁、决策 | 写入 §11–§15，勾满状态清单 | ✅ 用户确认冻结 |
| 2 | 伪 RAW 风险 | 源使用必须显式来自指令语义，不能按位域猜 | `decode.v` 增加 `uses_rs1/uses_rs2` | ✅ `tb_decode` 11 用例 PASS |
| 3 | 125 MHz 是否卡死 M1 | 应作非阻塞加分，按实际最高通过频率入档 | `plan.md`/`design_v0.md` 口径改写 | ✅ 文档一致 |
| 4 | CoreMark 长时间运行 | 正常计算，须等 golden 判据 | 不中断，等待结束 | ✅ CPI=2.105 golden 匹配 |

## 5. 最终结论

- **契约**：`design_v1.md` 定稿并冻结（§1–§15，D1–D15 已确认，状态清单全勾）。
- **R1**：`decode.v` 输出 `uses_rs1/uses_rs2`；`tb_decode.v` 11 用例 PASS；`run_iverilog.sh` 增 `decode` 模式并入 `all`。
- **收口**：`design_v0.md` 标记 Part A 完成（tag `partA-v0` = `962a4f5`）；`plan.md` 指标口径更新。
- **回归全绿**：IMEM / DMEM / RV32I / RV32I 38 / 转发 / decode / muldiv / RV32IM(`tohost=142879`) / CoreMark(`cycles=21275738, instrs=10106387, bubbles=1243809, CPI=2.105`，golden 全匹配) / SoC(`tohost=13, LED=1101`)。
- **待办**：阶段 2 按古法编程逐模块实现 `forwarding.v` / `hazard.v` / `id_ex_stage.v` / `mem_wb_stage.v` / v1 `core_top`。

## 6. 经验沉淀

- 触发条件：实现转发/冒险之前，先让译码提供“真实读取了哪些源寄存器”。
- 排查步骤：
  1. `uses_rs1/uses_rs2` 必须来自指令语义，不能仅根据指令位域推断（避免伪 RAW 停顿/转发）；
  2. 转发、冒险、RV32M 多拍都依赖同一套 `valid` 与源标志，先统一再落 RTL；
  3. 长时间回归（CoreMark）要等自然结束、看 golden 判据，不得中断或伪报；
  4. 指标口径（125 MHz 非阻塞、记录实际最高通过频率）必须在合同与计划里同步。
- 适用范围：任何带转发/冒险的流水线均成立；“译码显式源使用标志”可复用。 #skill候选
