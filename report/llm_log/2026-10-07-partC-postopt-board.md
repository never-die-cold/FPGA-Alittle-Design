# Part C 优化后复验、上板与 core_top 声明补丁入库（2026-10-07）

> 执行：never-die-cold（agent 驱动，板前读数由本人完成）。
> 证据主档：`data/logs/2026-10-07-partC-postopt/README.md`。本文只记决策、问答与边界。

## 本次做了什么

1. **采纳验证线 core_top_fix.diff**（`bp_predict_taken`、`redirect_target` 声明前移，纯声明位置）：`build_fmax.tcl` 用 `read_verilog -sv`，IEEE 1800 先声明后引用，不采纳则 OOC 流程起不来。
2. **iverilog 全量回归**（`run_iverilog.sh all`，退出码 0）：功能 tb 20 项 PASS；CoreMark 四档 cycles/BHT 统计与 2026-10-06 锚点逐位一致（nofwd 19057438 / fwd 17114141 / bht1 16335562 / bht2 16232079，retired 恒 10106386）→ 证实声明补丁功能零改动。
3. **核 OOC 门禁复测**：bht2 @11.520 ns（86.8 MHz）**WNS +0.538 通过**（优化前 −0.334 失败保留）；最差路径 `stall_q_reg → pc_reg[30]`，12 级 / 10.920 ns（优化前 17 级 / 11.860 ns）。
4. **四档 @10 ns 记录档**：nofwd +0.051（100 MHz 实点过）；fwd −0.587、bht1 −0.419、bht2 −0.586（失败，记录；BHT 档较优化前改善 1.3–1.5 ns）。
5. **SoC 40 MHz bht2 构建**：WNS +3.618、DRC 0 错、LUT 6768；位流 SHA256 `B06F0828…EC93`。
6. **上板**：`PROGRAM PASSED`；LED=`1101` 静止、BTN0 `0000`→松开 `0001`，与 Part A / Part B / 前次 v1 完全一致（本人板前读数）。

## 关键决策

- **不改 `board/scripts/program_soc.bat`**：其硬编码 `D:\Vivado\2026.1` 已失效（实际 `D:\Vivado_downloads\2026.1`），但 board/ 超出预授权目录；改经 `program_soc.tcl` 直调，README 留记录，待板务/RTL 线修路径。
- **优化后 XSim 四档未复跑**：10-06 已在优化前 RTL 做过双工具对拍，本次 iverilog 锚点逐位一致，增量价值低；如材料收口需要可补。
- **门禁口径不变**：约束点通过/失败才算实测，外推 Fmax（91.1 MHz 等）仅参考；核 OOC 与 SoC 频率分开表述。

## 理解门槛问答（commit 前过闸，2/2 通过）

**Q1 为什么 iverilog 能过而 `read_verilog -sv` 不行（同一份声明后置代码）？**

答（用户）：同一 module 内标识符"先用在表达式中、声明在后面"，两种工具容忍度不同。iverilog（Verilog-2001 模式）是经典两遍处理——第一遍收集整个 module 的全部 wire/reg 声明进符号表，第二遍才展开 assign，声明在 179 行还是 34 行无所谓；这是 1364 时代生态长出来的事实宽容。`read_verilog -sv` 按 IEEE 1800 收紧为先声明后引用，因为 SV 里声明位置真正影响语义（net/变量区分、default_nettype、包与接口的确定性解析），工具必须单遍确定性 elaboration，所以 xvlog -sv 报 used before its declaration，`build_fmax.tcl`（显式 -sv）在未修时就起不来。

**Q2 11.520 ns 门禁从哪来、对应什么条款、过了能/不能宣称什么？**

答（用户）：11.520 ns 是 v0 基线外推频率的倒数——v0（两级流水）在 10 ns 约束下 post-route 实测 WNS = −1.530，需 11.53 ns 才能过，外推 Fmax = 1000/(10+1.530) ≈ 86.8 MHz（tag partA-v0，同法 OOC），1/86.8 ≈ 11.52 ns，即"v0 能力对应的约束周期"。对应 `src/riscv/plan.md` §4.3：本轮 PC/flush 优化最低目标 = 保持三级、BHT2 核 OOC 在 11.520 ns 实跑 WNS ≥ 0（已达成，+0.538）；10 ns（100 MHz）为继续提升目标（未达）；SoC 另测不混用。通过后**能**宣称"三级流水在 v0 同能力点上保住并越过时序"，**不能**宣称 BHT2 已达 100 MHz、不能把外推 91.1 MHz 当实测、不能用核 OOC 结论代替 SoC/上板频率结论。

## 边界与遗留

- 本次 commit：`src/riscv/core_top.v`（声明顺序）+ `data/logs/2026-10-07-partC-postopt/` + 本文。工作区其余 Pi 相关改动（`docs/pi-dev-roles.md` 等）非本次范围，未触碰。
- 遗留：program_soc.bat 路径修正；125 MHz SoC 维持 FAIL 留档；"主频提升或持平"条款结论待 RTL 线写入 `design_v1.md` §14（注意仓库同时存在 v0 的 86.8（09-14）与 83.8（09-28 重综合）两个历史数，§14 行文需指明采用 tag partA-v0 口径）。
- 工具备忘：Git Bash 调 Vivado 用 `cmd //c`，**勿加 `MSYS_NO_PATHCONV=1`**（会挡住 `//c`→`/c` 转换致 cmd 进交互模式）。
