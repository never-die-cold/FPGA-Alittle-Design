---
name: sim-board-consistency
description: Use when comparing simulation results against on-board behavior, when computing CPI/retired-instruction counters, when a long simulation silently passes or times out, when porting a third-party test suite (riscv-arch-test, CoreMark), or when declaring "PASS" from partially-interrupted runs. 仿真-上板一致性踩坑清单：唯一退休点口径、终止窗口竞态、配置档联合判据（CRC 对≠参数档对）、跨工具对拍、中断回归不拼接、历史 FAIL 不倒填。Trigger on 退休指令 / CPI / 仿真 PASS / arch-test / CoreMark / 逐位一致 / 上板复验.
---

# 仿真-上板一致性踩坑清单（sim-board-consistency）

一句话规则：**"功能 PASS ≠ 时序 PASS ≠ 已上板"是三层独立门禁；统计口径先于数字——没有唯一退休点和关窗规则的计数，一个都不能信。**

## 踩坑清单

### 1. 唯一退休点口径

- **触发**：CPI/IPC 统计用 `instr_valid && !stall` 之类"流水线看见过"的信号。
- **症状**：32 拍乘除对同一条指令重复计数 → 分母灌大 → CPI 虚小 → 收益被高估。
- **规则**：全核只认一个提交点（本项目为 `mem_valid`：实际写回/提交的拍）；分类口径互斥（每个气泡只进一个桶，优先级固定）并用**闭合校验**（Σ分类 = 总周期差）自证。

### 2. 终止窗口竞态

- **触发**：测试线程与计数线程同在时钟沿活动；退出后自旋指令可能多计/少计 1 条。
- **规则**：计数器**自身**用 `!exit_seen` 关窗，不依赖线程唤醒先后；不变量"同程序 retired 必须相同"写进 tb 断言（实测曾抓到 1206 vs 1205）。

### 3. 长跑与官方基准的隐含规则要写成显式禁令

- XSim 默认 `max_cycles=10M` 跑不到实际 16–19M 周期 → **假 PASS/短窗数据**；GUI 默认 runtime 1000 ns 同理。
- CoreMark 对 <10s 运行自动 `total_errors++`——"程序没报错"必然误判，判据必须是 CRC 三常数 + golden 对比；`errors_raw=1` 的短测必须披露、不得写成官方分数。
- 契约写法：把"看什么、不看什么"写成显式禁令（如"errors_raw 只作证据，判据看 CRC"），防止下一个照直觉写判据。

### 4. CRC/结果对 ≠ 参数档对

- **触发**：参数化 tb（BHT 档位、转发开关）只断言结果。
- **症状**：配置传错档，退休指令与 CRC 仍可能全对（预测器只改周期/冲刷）。
- **规则**：判据 = 配置回读行（tb 落盘配置快照）+ 计数器行（cycles/retired/bubbles）+ 结果行三者联合；同名参数（`mode`）在开关与档位两个维度语义不同，命名要区分。

### 5. 跨工具对拍：工具宽容度差异是"功能等价假象"

- iverilog 容忍同 module 先用后声明（Verilog-2001 两遍处理），`xvlog -sv`（IEEE1800 单遍）拒绝——**两工具都过 = 伪安全，换综合入口就炸**；RTL 收口前用另一工具编译一遍作为门禁。
- Icarus 无 Xilinx 原语 → tb 内建 MMCM/BUFG 桩并断言行为（分频比/VCO）。
- `.bat`/PowerShell 中转会把带 `=` 的 generic/testplusarg 拆参 → 值保留引号；GUI 相对路径按 behav/xsim 目录解析。
- **BRAM 推断失败只在顶层真实参数综合时暴露**（iverilog/XSim 干净≠综合干净）：mux 阵列写存储重构为每阵列独立 1W1R always；顶层综合是唯一能抓存储推断失败/多驱动的闸门。
- **模块未接入顶层 = 回归盲区**：只有 /tmp 临时 tb 的模块被环境清理后不可复现，改坏也全绿——模块级 tb 落库 + 单独模式 + `all` 全量档；iverilog 通配编译必须 `-s <top>`（未例化模块的 initial 也会执行）。

### 6. 第三方套件移植（riscv-arch-test）

- Windows 检出符号链接退化为文本 → 选自带参考签名的套件版本并把 **commit 入档**；
- 哈佛核只预载 imem 会让读初值类测试大面积 FAIL → 同一镜像双预载 imem/dmem；
- 签名地址/长度用 `nm` 从 ELF 取，不硬编码；"固定周期 + 失配"= 响亮的失败。

### 7. PASS 判定的三条硬规则

- **中断的回归不能拼接为通过**：exit 143 / 部分用例 PASS → 保留旧日志，从头重跑完整一轮。
- **历史 FAIL 不被新收益倒填**：旧工作点的 FAIL 永远是 FAIL，后来组合收益不能覆盖改写历史结论；原始 FAIL 日志永久保留。
- 门禁三条件同时满足：退出码 0 + 日志 `^PASS:` + 无 FAIL/FATAL/ERROR 文本（grep 到 PASS 不算数，FAIL 行也能让 grep 成功）。

## 已验证效果

- 四档配置 XSim 与 Icarus 周期/退休/BHT/CRC **逐位一致**；arch-test 44/44 签名逐字匹配、四档签名 SHA 相同；
- 周期分类闭合校验（raw 差值恰等于分类和）；窗口竞态被不变量断言当场抓住；
- CoreMark RTL/host/多优化档三方 CRC 一致（crcfinal=0x8799）。
- 来源（`report/llm_log/`）：`2026-10-05-partB-v1-cpi.md`、`2026-10-06-partC-verify.md`、`2026-09-23-coremark-port.md`、`2026-09-23-coremark-tb.md`、`2026-09-23-coremark-tb-contract.md`、`2026-09-21-partA-decode-and-muldiv-tb.md`、`2026-10-01-vision-m2-sprint.md`、`2026-09-26-partA-soc-onboard-verify.md`、`2026-10-07-module1-closure.md`、`2026-10-09-module1-2-closeout.md`、`2026-10-09-riscv-closeout-collaboration.md`、`2026-10-06-partB-t2-onboard-verify.md`

## 失效条件

- 纯软件模拟器（无时序概念）不适用退休点/窗口条目；
- 形式验证可替代部分对拍，但"已上板"仍需实机证据；
- 换 ISA/换基准套件时，具体判据（CRC 常数、签名格式）重写，条目 1/2/7 保留。
