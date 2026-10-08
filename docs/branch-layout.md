# 当前分支与同步规则

2026-10-08 按用户指定保留五个分支。职责以根计划 §2 为准。

| 分支 | 用途 | 迁移来源 |
|:---|:---|:---|
| `main` | 经 PR 合入的集成版本 | 原主干 |
| `dev/riscv` | RISC-V 核与协处理器 RTL | `dev/rtl` 改名 |
| `dev/vision` | 视觉 RTL、板端链路与验证 | 原视觉分支 |
| `dev/model` | 模型训练、导出与黄金参考 | 原模型分支 |
| `dev/exe` | EXE、联调及板务协调 | `dev/bench` 合入后续作 |

`dev/verify` 与 `codex/module1-closure` 已无独有工作，随同步移除。
`dev/bench` 的剩余 Pi/视觉实验与证据经 PR 合入后移除。
历史记录里的旧名称和提交号保持原样，不作为当前开分支指令。

未合入的本地 HDMI 诊断工作以标签 `archive/pi-hdmi-diagnostics-2026-10-08` 保留，指向 `7b79f9b`；这批功能未进入本次主干验收。需要恢复时从标签创建工作分支并单独复核。

合并 PR 后执行 `git fetch --prune origin`，在各开发分支上快进或合并 `origin/main`，核对 ancestry 后再推送。禁止强推或覆盖其他工作区的未提交文件。工作区目录名不随分支自动改名；RTL 工作区仍为 `FPGA-Alittle-Design-rtl`，其中未跟踪日志须保留。

此次收录的模型结果仍是实验产物，不代表真实工位验收；完整训练数据和环境未随仓库归档。可直接复验的局部测试与本轮记录见 `data/logs/2026-10-08-branch-consolidation/`。
