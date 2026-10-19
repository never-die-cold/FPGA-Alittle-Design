# 当前分支、worktree 与同步规则

2026-10-08 按用户指定保留五个开发分支；2026-10-19 仓库整理新增 `chore/repo-cleanup`。职责以根计划 §2 为准。

## 分支

| 分支 | 用途 | 当前状态（2026-10-19） |
|:---|:---|:---|
| `main` | 经 PR 合入的集成版本 | 与原主干一致 |
| `dev/riscv` | RISC-V 核与协处理器 RTL | 与 main 同步（0 ahead） |
| `dev/vision` | 视觉 RTL、板端链路与验证 | 与 main 同步（0 ahead） |
| `dev/model` | 模型训练、导出与黄金参考 | 领先 main 5 个提交；整理分支从它切出 |
| `dev/exe` | EXE、联调及板务协调 | 与 main 同步（0 ahead） |
| `chore/repo-cleanup` | 仓库整理专用；不直接进 main | 从 `dev/model` 切出，待 review |

`dev/bench`、`dev/verify` 已于 2026-10-19 删除（0 ahead）；历史记录里的旧名称和提交号保持原样，不作为当前开分支指令。

## Worktree

| 路径 | 用途 | 状态 |
|:---|:---|:---|
| `E:/Projects/FPGA-Alittle-Design` | 主工作区 | 当前分支 `chore/repo-cleanup` |

2026-10-19 已回收 4 个额外 worktree（`-rtl`、`-vision`、codex 旧工作区、`dev-exe-sync`）。删除前的未跟踪/冲突文件、Vivado 日志和 `sim/build` 清单保存在 [`data/logs/2026-10-19-worktree-inventory/README.md`](../data/logs/2026-10-19-worktree-inventory/README.md)；其中 `dev-exe-sync` 的 9 个差异文件需人工裁决，worktree 本身不再恢复。

规则：需要并行工作区时重新 `git worktree add`；删除前先保存未跟踪/未提交文件，不使用 `--force` 跳过检查。

## 同步规则

合并 PR 后执行 `git fetch --prune origin`，在各开发分支上快进或合并 `origin/main`，核对 ancestry 后再推送。禁止强推或覆盖其他工作区的未提交文件。RTL/视觉并行工作区已回收；需要时从对应分支重新 `git worktree add`，不要复用旧的未提交目录。

未合入的本地 HDMI 诊断工作以标签 `archive/pi-hdmi-diagnostics-2026-10-08` 保留，指向 `7b79f9b`；这批功能未进入本次主干验收。需要恢复时从标签创建工作分支并单独复核。

模型结果仍是实验产物，不代表真实工位验收；完整训练数据和环境未随仓库归档。可直接复验的局部测试与记录见 `data/logs/2026-10-08-branch-consolidation/`。
