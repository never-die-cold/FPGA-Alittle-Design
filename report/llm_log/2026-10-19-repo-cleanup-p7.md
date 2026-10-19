# 仓库整理 P7：提交、tag 与最终验收（2026-10-19）

> 前置：P0–P6 已完成；P5/P6 记录见 [`2026-10-19-repo-cleanup-p5-p6.md`](2026-10-19-repo-cleanup-p5-p6.md)。
> 本次只提交整理结果、刷索引和打 tag，不改源码行为。

## 1. 提交与 tag

| 对象 | 值 |
|:---|:---|
| 分支 | `chore/repo-cleanup` |
| 整理提交 | `2f5475b` `chore(repo): tidy generated artifacts, evidence indexes and docs taxonomy` |
| 索引刷新提交 | `ebf739e` `chore(repo): refresh evidence indexes after cleanup` |
| 整理前 tag | `pre-cleanup-2026-10-19` → `d87c9cc` |
| 整理后 tag | `post-cleanup-2026-10-19` → `ebf739e` |
| 工作区 | clean |

## 2. 最终数字

| 指标 | 结果 |
|:---|---:|
| 跟踪文件 | **5,124** |
| 工作区磁盘 | **约 469 MB**（整理前约 3.9 GB） |
| `.git` pack | **94.32 MiB**（gc 前 100.19 MiB） |
| 额外 worktree | **0** |
| `docs/` 根 Markdown | **15 篇**（+1 CSV 例外） |
| 日志输入快照 | 924 → 325 个（588 个去重，均可恢复） |
| 生成物跟踪 | 0（file-guide 输出、`.vvp` 均已退役） |

## 3. 最终验证

```powershell
python sim/scripts/check_repo_hygiene.py   # PASS, 0 error, 12 条证据区重复告警
python sim/scripts/index_runs.py --check   # OK
git diff --check                           # 无输出
git status --porcelain=v1                  # 空
git worktree list                          # 只剩主工作区
git tag -l '*cleanup*'                     # pre/post 两个 tag
```

- 12 条重复告警是**有意保留**的证据区重复（arm-localize 的 input.json、HDMI IP 文档等），继续删会影响 48/48 完整性校验或原始证据可读性。
- 没有跑 RTL 全量回归：本次未改 RTL/软件行为。
- 发布包：`build/artifacts/nc-offboard-release-20261014.zip`（本地、忽略，78,183,698 B）。

## 4. 仍需人工处理

1. `data/logs/2026-10-19-worktree-inventory/preserved/dev-exe-sync/` 的 9 个文件需要裁决：旧 merge worktree 的工作区版本可能已被后续 commit 覆盖；若有独有改动，从这里取回。
2. `build/artifacts/worktree-rescue/` 有 8 个本地保留的 `.jou/.dcp`（不入库）；确认不需要后可删。
3. 隔离区 `E:/Projects/FPGA-Alittle-Design-cleanup-quarantine/sim-build-20261019`（24.9 MB，ACL 拒绝访问）有管理员权限后可删。
4. 12 条证据区重复告警：如需继续，按 P5 的 manifest 流程另开一步，不要直接删。

## 5. 回退

- 整体回退：`git checkout pre-cleanup-2026-10-19`（或从 tag 建分支）。
- 单文件：`git show pre-cleanup-2026-10-19:<path>`。
- 快照：`python sim/scripts/restore_snapshot.py --run <run> --restore`。
- P6 前 docs 备份：`E:/Projects/FPGA-Alittle-Design-cleanup-quarantine/docs-before-p6-20261019.zip`。
