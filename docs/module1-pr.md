# 模块一收口 PR 发布记录
状态：[PR #60](https://github.com/never-die-cold/FPGA-Alittle-Design/pull/60)已合并至main；目标仓库：https://github.com/never-die-cold/FPGA-Alittle-Design。
标题：`chore(riscv): 完成模块一四档验证、时序与证据收口`。
base=`main`，head=`codex/module1-closure`；原工作分支=`dev/bench`。草稿#59转换接口故障，关闭保留记录后以相同head创建非草稿#60，合并提交f3668f7。
独立分支基于`c2bb910`，引入核声明修正、40MHz板级报告归档与本轮收口。核RTL/tb/hex与本轮被测输入一致；Pi/视觉WIP仍在原工作分支。

以下正文按仓库PR模板发布，技术证据链接固定到独立收口提交`ad6db8292c468171b009819a32376087fa83f79e`；本文件随后回填执行状态。

## 1. 变动概述
模块一的优化后结果已有零散日志，但缺少统一的四档arch、benchmark、XSim入口及完整时序交叉核对。本PR补齐这些入口，归档11条I/M子集×4档签名、八组工作负载、四档XSim及OOC审计，统一报告、指标与核契约。
包含前置核声明顺序修正及40MHz SoC归档；源RTL功能和容量不变。arch链接容量由16KB对齐已有32KB核/tb契约。
对应核计划Part B/C；#20/#21与M1技术里程碑已关闭。技术证据与理解门槛完成；备考条目仍缺证据，移交#61保持待办。

## 2. 涉及目录
`src/riscv/`、`sim/scripts/`、`sim/arch_test/target/`、`data/logs/`、`data/metrics.csv`、`report/`、`docs/`、根README/plan/.gitattributes，以及前置提交的`build/reports/soc_40mhz_bht2/`与引脚报告。
共享目录改动已在本会话说明，按用户跨目录预先授权执行。群聊同步未由本助手执行。
生成工具报告定向关闭空白格式检查；本轮原始日志与签名关闭行尾转换，保留字节。代码和文档继续检查空白。

## 3. 自测证据
- `bash sim/scripts/run_iverilog.sh all`：完整退出码0，benchmark/CoreMark各四档通过。
- `bash sim/scripts/run_arch_test_matrix.sh`：11 tests × 4 modes，44次官方golden匹配，档间签名一致。
- `./sim/scripts/run_module1_xsim.ps1`：四档周期、退休、气泡、BHT与Icarus逐位匹配，CRC golden通过。
- `vivado -mode batch -source sim/scripts/audit_module1_ooc.tcl -tclargs <新目录>`：五个原约束点hold/严重DRC审计，BHT2@11.520ns setup=+0.538ns、hold=+0.167ns；fwd/BHT1固定布线STA补证通过。
- `python sim/scripts/summarize_module1.py data/logs/2026-10-07-module1-closure`：44签名、8工作负载、4对拍、5审计、2固定布线门禁PASS；独立checkout复核通过。
- `iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v`：退出0。完整暂存及PR差异空白检查通过。

证据：[收口报告](../report/module1-closure.md)、[原始日志](../data/logs/2026-10-07-module1-closure/README.md)、[复现清单](module1-reproduction.md)。
转发收益10.20%，当前nofwd→BHT2收益14.83%；25%组合尽力目标未达。100/125MHz仍未通过；86.806MHz是核OOC通过约束点，真实SoC上板为40MHz。
CoreMark短仿真非官方长测；arch为声明子集。PS/CNN接口、工业固件及CSR/特权异常未实现/未接入。

## 4. 理解门槛
- [x] 本轮AI代码已完成逐段讲解、3题及1题补测；用户补测通过。
- [x] 完整讲解、题目、用户原文答案与判定已存`report/llm_log/2026-10-07-module1-closure.md`。

## 5. 复核人
用户在本会话通过理解补测并明确要求合并；按protect-main已配置的用户管理员例外执行。非作者署名未代填，不能把用户授权记录改写成第三人审查。实际合并与关闭记录已回填。
