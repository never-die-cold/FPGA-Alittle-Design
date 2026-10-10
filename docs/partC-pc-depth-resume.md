# Part C PC/flush 优化：额度刷新后的续工入口

> **历史续工快照（2026-10-09 整理）**：下文记录优化刚落盘时的状态与失败历史，
> 当时“下一未完成项”和后台进程检查不再是当前执行指令，不要依据旧 PID 重启任务。
> 后续优化复验见[PC 降深度复验](../data/logs/2026-10-07-partC-postopt/README.md)。
> 模块一核＋最小 SoC 已完成收口，见[模块一收口报告](../report/module1-closure.md)
> 与[合并验收记录](../data/logs/2026-10-07-module1-closure/README.md)。
> BHT2 核 OOC 的 11.520 ns 实点通过、40 MHz SoC 与实机证据应引用上述记录；
> 100/125 MHz 不因此视为通过，原 `WNS=-0.334 ns` 失败记录保留。

更新时间：2026-10-07；工作区 `/home/jianglibo/FPGA-Alittle-Design`。
分支 `dev/rtl`，起点 HEAD `3c6b794`；修改尚未 commit/push，禁止新建分支。
用户授权一次写完、理解题放末尾；2026-10-07 理解门槛已 3/3 通过。
尚未 commit/push，完整答案与判定已归档至本轮 llm_log。

## 已落盘

- core_top：互斥 PC/取址候选，预测与恢复选择展开；没有新增流水寄存器。
- id_ex_stage：组合 B 目标和目标后继，绕过通用目标 mux 后再加 4 的链。
- if_stage：flush 只清 valid，移除对指令数据的 NOP mux；stall 保持原拍序。
- 新 tb_core_pc_control、tb_if_stage；扩 tb_id_ex_stage、tb_core_bht_flow。
- run_iverilog.sh 已接独立入口 pc_control / if_stage 和 all。
- design_v1、plan、partB-rtl-handoff、llm_log、完整代码 patch 已更新。
- 代码 patch：`data/evidence/2026-10-06-partC-pc-depth-code.patch`。

## 验证事实（不得混写）

- 首跑 all.log：全部 RISC-V / vision RTL PASS；最后 HTTP socket 被沙箱拒绝，
  总退出 1。四档 cycles/retired/CRC/BHT 计数与原锚点完全相同。
- 独立 HTTP 用例在沙箱外重跑 PASS：vision-http-retry.log。
- 第二次 all-unsandboxed.log：会话中断，无转发档 PASS，没有完整退出码。
- 第三次完整 all：run_all.sh 脱离会话后台运行，开始于 00:17:36 +08:00。
  all-final.log / all-final.exit.txt 保存原始输出和实际退出码：**0，全量 PASS**。
  四档 CoreMark 和 vision 回归已完成；独立 check_results.py 核对 PASS。
  cycles 四档为 19057438 / 17114141 / 16335562 / 16232079，
  retired 均为 10106386、CRC 均为 8799，全部与原锚点一致。不要重复启动。
- standalone `iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v` 无输出；
  `grep -rn '(\.\*)' src/` 无匹配（退出 1 正常）；git diff --check 无输出。
- Vivado 无本地环境；优化后 WNS/Fmax/资源未验证，交验证线。
- 优化前 BHT2 @11.520 ns WNS=-0.334 ns 的实际 FAIL 保留。

## 下次先执行（不要直接重复 all）

```bash
cd /home/jianglibo/FPGA-Alittle-Design
git rev-parse --abbrev-ref HEAD
git log --oneline -3
git status --short
cat data/logs/2026-10-06-partC-pc-depth/all-final.exit.txt
tail -n 25 data/logs/2026-10-06-partC-pc-depth/all-final.log
ps -p "$(cat data/logs/2026-10-06-partC-pc-depth/launcher.pid)" -o pid,etime,args
```

退出码文件不存在：核对进程是否仍在运行；有进程则等待，勿重复启动。
进程消失且没有退出码：本次中断，保留日志，用新文件名重新运行完整 all。
沙箱内 ps 可能看不到沙箱外进程，不能据此断言退出；需从宿主进程视图核实。
后台运行不能保证运行环境被回收后仍继续，但已落盘文件可供恢复。

退出码为 0 后执行：

```bash
python3 data/logs/2026-10-06-partC-pc-depth/check_results.py all-final.log
git diff --check
```

本次 evidence README / results.json / llm_log / 本记录已更新。
**下一未完成项**：交验证线实跑交接单 §5
中的 11.520 ns BHT2 和四档 10 ns。不要把功能 PASS 写成频率通过。
退出码非 0 时先读失败堆栈；禁止删掉或覆盖失败证据。

## 理解题（用户已回答，3/3 通过）

1. 正确预测 taken 时，为什么 IMEM=T、PC=T+4？若 PC=T 会怎样？
2. flush 后仍有 mul/store 编码，哪些 valid 门控防止错误启动/提交？只换 NOP 为何不够？
3. 四档功能数据不变后，为何还不能宣布 86.8 MHz 达标？还需哪些 Vivado 证据？
