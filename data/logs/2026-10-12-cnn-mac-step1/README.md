# CNN MAC 第一步（2026-10-12）

用户调整顺序：综合检测后置，先推进 DDR/CNN；随后明确选择“改为先做 CNN MAC”。本步基线 `dev/model@3e2e1c9`，保留原有暂存/未暂存改动。没有启动板端 DMA、下载位流、提交或推送。

## 交付与范围

- 新增 `src/coprocessor/int8_mac.v`：组合 signed INT8×INT8 + INT32；33 位加法提供 overflow，溢出结果无效，不做饱和。
- 新增 `sim/coprocessor/tb_int8_mac.v`：64 位期望值、全部合法 INT8 两两组合和 INT32 边界；合法输入是 C02 的 [-127,127]。
- `sim/scripts/run_iverilog.sh` 新增 cop_mac，并接入 all。
- 同步 `src/coprocessor/README.md` 与 `design_v0.md` 的实现边界。不改变 C02 数值契约或正式输入范围。
- 新 RTL/tb 的有效代码 57 行，回归入口新增 10 行；满足单步 ≤100 行。

## 可复现验证

在仓库根目录执行 `bash sim/scripts/run_iverilog.sh cop_mac`，使用 `iverilog -g2001 -Wall`：
`PASS: int8_mac 65035 vectors; signed product/addition and overflow`，退出 0。
最终无新 RTL 时间单位警告；[原始输出](mac-test-final.txt)、[退出值](mac-test-final.exit.txt)。

首次主机进程缺少 MSYS dirname/mkdir 路径，工具未正确运行，退出 1；原始 `mac-test.initial-path-failed.*` 保留。随后只补本次进程 PATH，未改全局环境或源码。
第二次自检 PASS 但有继承时间单位警告，保留 `mac-test.*`；给新 RTL 显式 timescale 后再跑，最终结果见上述 final 文件。旧核的既有时间单位警告不在本步改动范围。

主机调用 `C:/msys64/usr/bin/bash.exe`；进程 PATH 前置 MSYS ucrt64/bin、usr/bin 和主机 Python 3.12；VISION_PYTHON 指向该 Python。
`bash sim/scripts/run_iverilog.sh all` 中途运行保存在 rtl-all.txt，退出值 3840；用户随后指定快速模式并继续扩大实现范围，代理核对 MSYS 进程组后终止中途回归，见 rtl-all-scope-change-note.txt。这是未完成记录，不是全量 PASS 或 HDL 功能失败；最终稳定代码将重新全量验证。

## 理解与待办

本步讲解：16 位乘积必须重复符号位扩展；33 位加法用于判断结果是否能精确表示为 INT32，overflow=1 时不允许继续用 result。
已提出两题：① 负乘积扩展时补零会怎样？② INT32_MAX+1 时为什么不能把输出当正常负数或截到最大值？用户明确回复“按快速模式，最后做理解题”，已授权继续后续实现；问题集中到最后，提交前仍须确认理解。

未实现/未接入：128 路 MAC 阵列及其时序/缓存/调度、整网整数黄金与正式权重、卷积/ReLU/requant/GAP/FC 链、DMA/MMIO、核工业固件、custom DDR 安全取帧和真实 LIVE 闭环。首个 MAC 不等于 CNN 完成。
本步未做综合/资源/100MHz 时序验证或上板。N02/N03 完整验收与定位修复按用户要求后置；临时机位/背景/光照不冻结。

Git 工作区/暂存差异检查保存为 diff-check.*、staged-diff-check.*；最终状态以收尾记录为准。
