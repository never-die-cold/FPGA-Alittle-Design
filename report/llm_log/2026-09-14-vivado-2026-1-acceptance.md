# [2026-09-14] 协作记录：Vivado 2026.1 环境验收——XSim 复核对拍 + v0 核综合基线（Fmax 86.8 MHz）

> 标签：#工具链 #验证 #构建
> 平台：OpenCode ｜ 模型：opencode-go/deepseek-v4.1-flash
> 相关 commit：本条记录本身
> 前置：`report/llm_log/2026-09-14-vivado-2026-1-decision.md`（版本决议改用 2026.1）

## 1. 任务与初始提示词

> "ok，license已经好了"（继续 Phase 2 验收：XSim 复核 + 综合基线）

## 2. 模型第一版方案

直接跑 `xsim <snapshot> -R` 复核两套核级 tb；综合用 `synth_design → opt/place/route` 全流程出 post-route Fmax/WNS 与资源基线。

## 3. 失败现象（真实偏差）

1. **XSim 首次运行报 license 错误**：`Could not obtain the necessary license for Simulator`。排查：`vivado -version` 正常（版本查询不校验 license），但 `XILINXD_LICENSE_FILE` 为空、用户目录无 `.lic`——属于"BASIC license 尚未生成/加载"的前置缺失，不是环境故障；license 完成后复跑即通过
2. **place_design 报 IO placement infeasible**：`Number of unplaced IO Ports (166) is greater than number of available pins (125)`（Place 30-58）。根因：v0 核 166 个端口全被当作顶层 I/O，CLG400 封装引脚不够；工程本就无板级顶层

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | xsim：`Could not obtain the necessary license` | 2026.1 起无有效 license 文件不启动，仿真引擎需单独取许可 | 用户完成 license 生成/加载后复跑 | ✅ 两套 tb PASS |
| 2 | place：Place 30-58（166 I/O > 125 脚） | 核级模块不应做含 I/O 的整芯片实现 | `synth_design -mode out_of_context`（OOC） | ✅ 综合/opt/place/route 全过 |
| 3 | OOC 报告 `HD.CLK_SRC not set`（时钟偏斜未建模） | OOC 需标注时钟在父级设计中的缓冲位置 | XDC 增 `set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]` 重跑 | ✅ WNS -1.639 → **-1.530 ns** |

## 5. 最终结论

**XSim 复核通过（与 iverilog 对拍一致）**：

- `tb_core_smoke` → `PASS: tohost = 13 (0x0000000d), tohost_exit = 0`
- `tb_core_test` → `PASS: all RV32I tests passed (tohost_exit = 0)`
- BASIC 档 XSim ≤ 50K 实例限制对核级 tb 无影响（设计规模远小于门限）

**v0 核综合基线（Vivado 2026.1，xc7z020clg400-1，post-route，OOC）**：

- WNS = **-1.530 ns**（约束 10 ns）→ **Fmax ≈ 86.8 MHz**，未达 100 MHz 目标——直接作为 Part B（三级流水 + 转发）的优化对照基准
- 最差路径：`u_if_stage/flush_q_reg` 反馈路径，数据路径 11.405 ns（逻辑 3.450 / 布线 7.955），逻辑 17 级，布线占比 ~70%
- 资源：LUT 846 / FF 65 / BRAM 0 / DSP 0（XC7Z020 占用 < 2%）

**资产入库**：`build/build.tcl`、`build/constraints/core_top.xdc`、`build/reports/*.rpt`；指标落 `data/metrics.csv`。
**环境验收状态：完成**（版本确认 → license → XSim 复核对拍 → 综合基线）。

## 6. 经验沉淀

- 触发条件：新装 EDA 工具链的环境验收（仿真 + 构建全链路） #skill候选
- 排查步骤：
  1. `tool -version` 能跑 ≠ license 可用：版本查询可能不校验 license，必须跑一次真实任务（仿真/综合）才算验收通过
  2. 综合/实现报 I/O 超引脚（Place 30-58）时，核级模块改用 `synth_design -mode out_of_context`；OOC 下补 `HD.CLK_SRC` 标注时钟源，使时钟延迟/偏斜可估算
  3. 先测基线（WNS/Fmax/资源）再谈优化：基线不达标本身就是 Part B 的立项依据
- 适用范围（换题目/换板卡/换工具是否成立）：均成立；OOC 基线流程适用于任何"模块级先行、顶层级后到"的 FPGA 工程
