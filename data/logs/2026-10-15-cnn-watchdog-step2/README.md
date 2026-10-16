# CNN watchdog 最后周期锁存（2026-10-15）

基线 `dev/model@891cba2`，承接尺寸优化第 1 步，未提交。启动时将 `cycle_limit-1`
锁存为 `limit_last`，消除每拍减法；sequencer 仍向卷积传递原预算。零预算立即拒绝，
CE 暂停仍累计墙钟周期，最后允许周期关闭存储和输出写使能。没有更改超时含义。

## 验证

入口：`bash sim/scripts/run_iverilog.sh coprocessor watchdog`。
`watchdog-before.txt` 与 `watchdog-after.txt` 均退出 0：两个控制器各 18 个精确周期用例，
覆盖预算 0…8、连续运行/CE 恒停、启动后修改外部预算、终止拍禁止读写和恢复。
`before/`、`after/` 与两个 manifest 保存这一中间步骤的精确源码，增删共 88 行。
后续快速批次将预算覆盖扩至 0…40，每控制器 82 例，见后一批次日志。

`ooc-wrapper.txt` / `.exit.txt`：100 MHz OOC 退出 0，WNS +0.416 ns、WHS +0.050 ns、
DSP 192、严重 DRC 0。精确综合输入和报告位于
`../cnn-ooc-4065cdcc415b43fbbc713dbeeceddbfb/`。此时仍未完成 DSP 余量目标。

用户随后明确要求“启用快速模式，少回答，多做，最后统一回答”，依据古法编程技能的
快速模式豁免继续参数缓存、requant 复用及调度优化。本中间状态未单独提交；
最终全量回归、diff 检查和状态清单见[快速批次证据](../2026-10-15-improvements-fast/README.md)。
