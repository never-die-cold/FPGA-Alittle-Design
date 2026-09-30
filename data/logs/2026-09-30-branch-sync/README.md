# 2026-09-30 分支同步回归

被测核内容：dev/rtl 的 522e819 合入 main eed5ba8 的工作树。视觉 RTL 为 eed5ba8 中的已提交基线；待合入 dev/vision 0da736d / 58d8140 只改变文档与 OOC 参数脚本，没有视觉 RTL 差异。

环境：Windows + MSYS2 UCRT64、Icarus Verilog 13.0。以下入口在仓库根目录执行，日志为实际输出：

```bash
set -o pipefail
bash sim/scripts/run_iverilog.sh all 2>&1 | tee data/logs/2026-09-30-branch-sync/riscv-all.log
bash sim/scripts/run_vision_iverilog.sh all 2>&1 | tee data/logs/2026-09-30-branch-sync/vision-all.log
```

- 核：退出码 0，15 个 tb + benchmark 额外一跑，共 16 条 PASS。CoreMark CPI=2.105，benchmark CPI=2.859。
- 新模块：forwarding 25 例、hazard 16020 例、MEM+WB 3 次捕获、ID+EX 6 例 PASS。
- 视觉：退出码 0，10 个 tb PASS，scaler/fullchain/top 黄金参考逐像素无错误。
- 保留编译器 timescale、ROM 未填满和 dangling port 等原始警告。CoreMark errors=1 为不足官方运行时间的既有现象，黄金 CRC/退出值仍满足仓库仿真判据，不是正式板上 CoreMark 成绩。

R2–R5 未接入完整三级核，本次不提供 v1 性能提升或完整 SoC 验收结论。视觉未提交 retiming 工作区的 RTL 与 OOC 报告不在此次已提交分支合并范围。
