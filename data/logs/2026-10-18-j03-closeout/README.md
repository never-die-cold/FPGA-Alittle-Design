# J03 离板收口索引（2026-10-18）

分支 `codex/night-2026-10-18`；runner 接入基线 `cb352f8`。本页只汇总可复现入口，
完整夜间命令、两次环境失败与最终退出码见[执行日志](../../../report/llm_log/2026-10-18-night-autonomous.md)。

## 最终复验

| 命令 | 结果 |
| --- | --- |
| `bash sim/scripts/run_iverilog.sh cop_mac_lane` | 退出 0，7 vectors PASS |
| `bash sim/scripts/run_iverilog.sh cop_dot8` | 退出 0，5 vectors PASS |
| `bash sim/scripts/run_coprocessor_iverilog.sh all` | 退出 0，算子、Conv/FC、两组整网逐元素 PASS |
| `bash sim/scripts/run_iverilog.sh all` | 退出 0，核、CNN、视觉 RTL/Python 全量 PASS |
| `git diff --check` | 退出 0 |

Linux 全仓复验用仓库内 venv，并设置 `VISION_PYTHON`、`COPROCESSOR_PYTHON` 指向其解释器；
依赖版本为 OpenCV 4.12.0.88、NumPy 2.2.6、Pillow 12.3.0。构建目录不入 Git。

边界：J03 算术/调度已离板收口；实体 BRAM、`cop_top`、MMIO/CDC、DMA、核接入、
固件、正式模型、完整 SoC 时序和上板均未实现或未验证。

