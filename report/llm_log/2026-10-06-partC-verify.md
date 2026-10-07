# [2026-10-06] 协作记录：Part C 可切换 BHT 验证（XSim 四档对拍 + 核 OOC 四档 + 主档上板）

> 标签：#riscv #验证 #build #hardware
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：被测 `dev/rtl@3c6b794`（Part C）；证据随本条记录入库
> 用途：Part C 主验证；记录 core_top 编译缺陷与 BHT 主频代价

## 1. 任务与初始提示词

> "（part-c）开始吧" → 后续确认"队友的修改做完了，开始工作吧"

被测件 = `dev/rtl` 的 Part C：`branch_predict.v`（三档 BHT）、误预测恢复接入 `core_top`、四档入口、板级/构建四档参数化（`3c6b794`）。工作项（`docs/partC-rtl-handoff.md`）：①arch-test 四档签名 ②XSim 四档对拍 ③Vivado OOC/SoC WNS/资源 ④上板。

## 2. 模型第一版方案

切临时分支到被测提交 → XSim 单元/整核/四档 → 核 OOC 四档 → SoC 主档构建 → JTAG 上板 → 归档。

## 3. 失败现象（真实偏差）

1. **`core_top.v` 前向引用导致 XSim/综合 `-sv` 编译失败**：`bp_predict_taken`（L30 用、L161 声明）、`redirect_target`（L38–44 用、L72 声明）→ `xvlog -sv` 报 `used before its declaration`。Icarus 容忍（故 RTL 线回归能过），Vivado 不容忍；`build_fmax.tcl` 也用 `read_verilog -sv`。**用户授权后修（仅 core_top.v，两处声明前移，功能等价）**，已请 RTL 线采纳。
2. **XSim `-generic_top` 参数被 PowerShell 转义**：`BHT_MODE=0` 被拆成 `BHT_MODE 0`，`0` 被当成顶层 → 改用 `cmd /c` + 显式引号解决。
3. **CoreMark tb 默认 `max_cycles=10,000,000` 太小**：XSim 首跑 10M 周期即超时（未到 tohost），须传 `run_iverilog.sh` 同款 plusargs（`+max_cycles=50000000 +hex +exp_*`）才跑到 ~1600–1900 万周期。
4. **arch-test 四档未做**：本机无 riscv 工具链/iverilog；且 `run_arch_test*.sh` 仅支持 `fwd|nofwd`、不含 BHT 档。
5. **BHT 主频代价**：核 OOC @10 ns，主档 bht2 WNS −1.955（外推 83.6 MHz），低于 100 MHz 与 v0 基线 86.8。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `xvlog -sv` 报 used before declaration | `core_top` 先用后声明（隐式 wire） | 用户授权后前移 2 处声明 | ✅ `xvlog -sv` 通过 |
| 2 | `-generic_top` 被拆开 | PowerShell→.bat 参数转义 | 改 `cmd /c` + 引号 | ✅ 快照构建成功 |
| 3 | CoreMark 10M 周期超时 | tb 默认 max_cycles 小 | 传 `+max_cycles=50000000 +exp_*` | ✅ 四档跑到终值、与 Icarus 一致 |
| 4 | 无 riscv 工具链 | arch-test 无法在本机跑 | 记为缺口 | ⏸ 待补 |
| 5 | 主档 Fmax 偏低 | BHT 进 flush/PC 逻辑 | 记录并反馈 RTL | ✅ 归因 |

## 5. 最终结论

- **功能（XSim）**：单元 `tb_branch_predict` PASS（21 checks）、整核 `tb_core_bht_flow` 三档 PASS、**四档 CoreMark 全 PASS 且 cycles 与 Icarus 逐位一致**（nofwd 19057438 / fwd 17114141 / bht1 16335562 / bht2 16232079；bht2 命中率 91.18%）。
- **核 OOC 四档 @10 ns**：nofwd +0.447（104.7）、fwd −0.383（96.3）、bht1 −1.928（83.8）、bht2 −1.955（83.6）；LUT 1853/2046/2248/2314、FF 508/508/573/637。**发现：转发 −8MHz、BHT −13MHz，主档低于 100MHz 与 v0 86.8；关键路径 `flush_q→pc_reg`（BHT 进 flush/PC 逻辑）**。
- **SoC 主档（bht2）**：40 MHz `BUILD PASSED`（WNS +5.599），上板 `PROGRAM PASSED`，**LED=`1101`**（与 v0/Part B 一致）。
- **未完成**：arch-test 四档（工具链/脚本缺口）；四档 Fmax 收敛与 SoC 四档未做。
- 证据：`data/logs/2026-10-06-partC-verify/`（`core_top_fix.diff`、`cm_*.log`、`reports/fmax/*`、`reports/soc_40mhz_bht2/*`）；上板记录 `board/logs/2026-10-06-partC-bht2-board/README.md`。

## 6. 经验沉淀

- 触发条件：验证"含新组合逻辑（如 BHT）的性能提交" #skill候选
- 排查步骤：
  1. **先 `xvlog -sv` 编译一遍**：Icarus 容忍的"先用后声明/隐式 wire"在 Vivado 会致命；这一步能提前暴露并定位。
  2. **XSim 传参用 `cmd /c` + 引号**：`-generic_top "K=V"` 经 PowerShell 会被转义拆开。
  3. **CoreMark 必须带 `+max_cycles` 与 `+exp_*`**：默认 10M 周期跑不到 tohost，会得到假 PASS/短窗数据。
  4. **Fmax 用四档同点对比**：能分离"转发"与"BHT"各自的主频代价；本例 BHT −13MHz，且关键路径在 `flush_q→pc`，不是 BHT 表本身。
  5. 工具链缺口（无 riscv gcc/iverilog）要在记录里显式标"未做/待补"，不得跳过。
- 适用范围（换题目/换板卡是否成立）：成立；任何"新逻辑 + 多档参数"的性能验证均适用。
