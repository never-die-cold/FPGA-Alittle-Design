# [2026-10-05] 协作记录：pynq_z2_top 模块——板级双时钟档（40/125 MHz）交接

> 标签：#soc #build #架构决策 #工具链
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`3a6ad00`（本模块改动）；交接单见 `docs/partB-rtl-handoff.md`

## 1. 任务与初始提示词

板级顶层要能同时支撑两档核时钟：**40 MHz 安全基准档**与 **125 MHz 非阻塞目标档**，两档都必须经 MMCM，**125 MHz 不直连核**。仿真的核心功能验证与 Vivado/上板验收由验证线在 Windows 侧复验。

## 2. 模型第一版方案

- `pynq_z2_top` 新增参数 `CORE_CLK_DIVIDE`：MMCM VCO 固定 `125×8=1000 MHz`，`40 MHz=÷25`、`125 MHz=÷8`；`btn0|~mmcm_locked` 异步复位、核时钟域两拍同步释放（不变）。
- `build/build_soc.tcl` 支持 `-tclargs 40|125`：按档设 `CORE_CLK_DIVIDE`、时钟名/周期与 `synth_design -generic`；run/report 分目录 `soc_40mhz/`、`soc_125mhz/`；位流 `pynq_z2_soc_40mhz.bit` / `pynq_z2_soc_125mhz.bit`。
- `build/constraints/pynq_z2_soc.xdc` 随档约束；新增 `sim/riscv/tb_pynq_z2_clock_config.v`（内建 Icarus 原语桩）断言两档参数确实落到 MMCM。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **Icarus 无 Xilinx 原语**：`MMCME2_BASE`/`BUFG` 需在 tb 内建桩模型才能仿真板级参数。
2. **WSL 无 Vivado/XSim**：40/125 两档的 WNS、DRC、资源均**未实测**；125 MHz 若失败必须保留原始 FAIL 与实际最高通过频率，**不得生成或冒用 125 MHz 位流**。
3. **上板未做**：生成位流≠已上板，必须实际下载并观察 `LED=1101` 才能记上板。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 仿真报找不到 MMCM/BUFG | Icarus 无 Xilinx 原语 | tb 内建 MMCME2_BASE/BUFG 桩 | ✅ `PASS: board clock profiles 40 MHz=/25, 125 MHz=/8, VCO=1000 MHz` |
| 2 | 两档不能混用同一产物 | 需按档分目录与命名 | `build_soc.tcl` 参数化 run/report/bitstream | ✅ 命令固定、互不覆盖 |
| 3 | 125 不达标不得冒用 | 保留 FAIL 与最高通过频率 | 交接单明确门禁与禁止项 | ✅ 文档一致 |

## 5. 最终结论

`pynq_z2_top` 板级双时钟档交接完成：`tb_pynq_z2_clock_config` 验证默认 40 MHz=÷25、125 MHz=÷8、VCO=1000 MHz，且不直连 125 MHz。`build_soc.tcl -tclargs 40|125` 分档产出独立报告与位流，下载脚本按对应档位流路径执行。**Vivado 两档时序/DRC/资源与 PYNQ-Z2 实机下载均待验证**，不得记“v1 已上板”。

## 6. 经验沉淀

- 板级多档时钟用**顶层参数 + 脚本 tclargs** 切换，report/位流**分目录命名**，避免互相覆盖。
- Icarus 验证 Xilinx 板级顶层要**内建原语桩**（MMCM/BUFG），断言参数确实传入。
- 门禁铁律：功能仿真 ≠ 时序通过 ≠ 已上板；125 MHz 未过就保留 FAIL 与实际最高通过频率，**不生成也不冒用**该档位流。
- #skill候选
