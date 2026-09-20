# [2026-09-20] 协作记录：PYNQ-Z2 最小流水灯上板工程的只读核查与独立落地

> 标签：#build #工具链 #上板验证 #架构决策
> 平台：Codex（VSCode 插件，WSL Ubuntu-22.04） ｜ 模型：GPT-6 Astra（gpt-6-astra）
> 相关 commit：`1fb6787`（board/smoke_test 七个文件）、`93eeb97`（PR #15 合并入 `dev/rtl`）；本文档随本次提交入库

## 1. 任务与初始提示词

分两轮。第一轮只读核查：

> 请先阅读当前仓库中的 AGENTS.md、README.md，以及所有与 board、RTL、仿真、Vivado 构建和 PYNQ-Z2 有关的说明……本阶段只做只读检查，不要修改任何文件，不要执行 git commit、git push、git reset 或文件删除……不得猜测任何 PACKAGE_PIN。若仓库内没有可信约束，请明确说明需要从哪份 PYNQ-Z2 官方约束获得。

第二轮实施，带强约束：

> 现在按照刚才的检查结果实施 PYNQ-Z2 最小上板测试……只允许在 board/smoke_test/ 目录内创建或修改文件……如果仓库现有规范要求使用不同目录，请先停止并说明，不要自行扩大修改范围……XDC 只能来自以下来源之一：当前仓库已有且能够说明来源的可信 PYNQ-Z2 约束；官方 PYNQ-Z2 master XDC……严禁猜测时钟、LED 或按钮的 PACKAGE_PIN、电压标准与时钟周期。

## 2. 模型第一版方案

- 只读结论：分支 `test/pynq-z2-smoke`、工作区干净；仓库唯一的 XDC `build/constraints/core_top.xdc` 只有 `create_clock` 与 `HD.CLK_SRC`，**无任何 `PACKAGE_PIN`/`IOSTANDARD`**；没有 LED、按键、板级顶层或板卡测试代码（`tb_core_smoke.v` 是 CPU 仿真，不是上板测试）；`src/soc` 仅存在于规划。
- 初版放置建议（只读报告里）：`src/board_tests/pynq_z2_smoke/` + `sim/board_tests/` + `build/pynq_z2_smoke.tcl` + 从官方 Master XDC 提取的约束。
- 实施版（用户收敛目录后）：在 `board/smoke_test/` 内交付 7 个文件——`rtl/pynq_z2_smoke_top.v`（125 MHz 计数器时钟使能、默认 `DIV_CYCLES=62500000` 即每 0.5 秒一步、one-hot `0001→0010→0100→1000`、BTN0 异步置位/两拍同步释放复位、寄存器 INIT 上电即走）、`constraints/pynq_z2_smoke.xdc`、`sim/pynq_z2_smoke_tb.v`、`sim/run_iverilog.sh`、`scripts/build.tcl`、`.gitignore`、`README.md`。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **目录规范冲突 → 主动停工**：模型初版把文件规划到 `src/board_tests`/`sim/board_tests`/`build`，与用户"只允许 `board/smoke_test/`"以及仓库既有目录约定（`docs/repo_structure.md`、`README.md`）冲突；按用户"冲突先停止"的指令，第二轮首轮 **0 文件产出**并请求目录例外授权。
2. **参数化计数器在 `DIV_CYCLES=1` 的边界隐患**：`localparam [COUNT_WIDTH-1:0] LAST_COUNT = DIV_CYCLES - 1` 在分频值为 1 时存在负数/位宽截断风险，自检阶段定位并改写为整数中间量再切片。
3. **无 Vivado 环境**：WSL 侧只有 `iverilog 11.0 / vvp 11.0 / verilator 4.038`，没有 Vivado；综合、实现、时序和 bitstream **全部未实测**，只能交付脚本与仿真证据，不能声称构建已通过。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 只读报告把文件放在 `src/`、`sim/`、`build/` | 与仓库目录约定及用户"只动 `board/smoke_test/`"冲突 | 停止实施，请求"目录例外"授权 | ✅ 用户批准例外，仅在 `board/smoke_test/` 落地 |
| 2 | 自检 `DIV_CYCLES=1` 边界 | `LAST_COUNT` 存在负数/位宽截断 | 改为整数中间量 `LAST_COUNT_INTEGER` 再切片 | ✅ `DIV=1` 仿真 `TEST PASSED` |
| 3 | 仿真只覆盖会通过的情形 | 无法证明失败会报警 | 故意打乱 one-hot 顺序后复跑 | ✅ 打印 `TEST FAILED` 且非零退出 |
| 4 | 官方 Master XDC 引脚与极性 | 不能凭记忆或习惯填 `PACKAGE_PIN` | 解包官方 zip + TUL 手册第 14 节核对极性 | ✅ 记录成员名、SHA256 与来源 |

## 5. 最终结论

在 `board/smoke_test/` 内独立交付 PYNQ-Z2 最小流水灯：板载 125 MHz 时钟（H16，周期 8 ns）、用户 LED0–3（R14/P14/N16/M14，高有效）、BTN0（D19，按下为高）全部取自官方 Master XDC（成员 `PYNQ-Z2 v1.0.xdc`，SHA256 `07441e999bac956c77e78091c782cade278efc5a78affc51e5b12b4800b1fe73`），极性由 TUL 参考手册第 14 节核实；`bash board/smoke_test/sim/run_iverilog.sh` 在 `DIV_CYCLES=1/2/5/8` 四组下全部 `TEST PASSED`，故意破坏顺序时 `TEST FAILED` 且非零退出，`git diff --check` 通过。Vivado 综合/实现/bitstream 未运行，留待 Windows 侧按 README 执行。成果经 PR #15 合并入 `dev/rtl`（`1fb6787`）。

## 6. 经验沉淀

- 触发条件：给一个"完全没有引脚映射"的仓库新增首次上板工程，或让不熟悉硬件的成员做板级冒烟。
- 排查步骤：
  1. 先只读核查：确认分支/工作区、现有 XDC 是否含 `PACKAGE_PIN`、有无板级顶层与按键/LED 代码、工具链版本；
  2. 引脚与极性只认官方 Master XDC + 厂商参考手册，并把来源 URL、成员名、SHA256、手册章节写进 XDC 与 README，绝不猜测；
  3. 顶层用"参数化计数器时钟使能 + 异步置位/同步释放复位 + 寄存器 INIT 上电自走"，仿真覆盖分频边界值（含 1），并故意制造失败验证告警通路；
  4. 没有综合工具时明确声明"未验证构建"，只交付可在有工具环境复现的脚本。
- 适用范围：换板卡只需替换官方 XDC 与极性依据；换 EDA 工具时"未验证就不声称通过"的原则不变。 #skill候选
