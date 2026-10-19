# 仓库整理 P4：worktree 与大缓存清理（2026-10-19）

> 前置：P0–P3 已完成；抢救清单见 [`data/logs/2026-10-19-worktree-inventory/README.md`](../../data/logs/2026-10-19-worktree-inventory/README.md)。
> 本次删除了 4 个额外 worktree、`sim/build` 主体和 `sim/arch_test/suite`；未改源码，未 commit。

## 1. 删除前保存

| 来源 | 保存内容 | 文件数 | 位置 |
|:---|:---|---:|:---|
| `-rtl` worktree | 4 个 `d3-repro-*` 日志/jou + `id_ex_ooc/` 的 rpt/dcp | 6 | `data/logs/2026-10-19-worktree-inventory/preserved/rtl-worktree/` |
| `-vision` worktree | 顶层 Vivado 日志/jou + `retry_open_fs.log` | 13 | `.../preserved/vision-worktree-logs/` |
| `dev-exe-sync` | 9 个与 HEAD 不同的文件 + 重命名目标 + status/diff/conflicts/head | 15 | `.../preserved/dev-exe-sync/` |
| 发布包 | `nc-offboard-release-20261014.zip` | 1 | `build/artifacts/`（ignore） |

- 所有抢救文件都有 SHA256：`preserved-sha256.txt`；逐一与源文件比对 29/29 匹配后才删除 worktree。
- `build/artifacts/nc-offboard-release-20261014.zip` SHA256：`AED1205E470C0CAC2B819D758BBB05B2131A0858D439EF53165AB812AB7F0393`。
- `sim/build` 删除前记录了顶层汇总和完整文件清单：`sim-build-top.txt`、`sim-build-files.txt`（18,938 行）。

## 2. 删除

- Worktree：`-rtl`、`-vision`、`codex/non-algorithm-system`、`sim/build/git-delivery/dev-exe-sync` 全部 `git worktree remove --force`，再 `git worktree prune`。现在只剩主工作区。
- 本地分支：`dev/bench`、`dev/verify`（均 0 ahead）已删除；保留 `dev/riscv`、`dev/vision`、`dev/exe`、`dev/model`、`main`。
- `sim/arch_test/suite`：1.29 GB 已删除；`sim/scripts/fetch_arch_test.sh` 可重新 clone。已用 `git ls-remote` 确认上游 `old-framework-2.x` 可达（当前 `6f7f47b`）。
- `sim/build`：18,938 文件 / 1.86 GB 已删除；剩余 803 文件 / 24.9 MB 因 ACL 拒绝访问，整体移动到仓库外隔离区：
  `E:/Projects/FPGA-Alittle-Design-cleanup-quarantine/sim-build-20261019`
  （不属于仓库，有管理员权限后可删）。

## 3. 结果

| 指标 | 清理前 | P4 后 |
|:---|---:|---:|
| 仓库工作区（不含 .git） | 约 3.8 GB | 约 **376 MB**（含 78 MB 发布包） |
| 仓库总大小（含 .git） | 约 3.9 GB | 约 **481 MB** |
| `sim/` | 3.41 GB | **0.84 MB** |
| 额外 worktree | 4 个 / 约 1.08 GB | **0** |
| 本地分支数 | 7 | 6（删了 2 个，新增 1 个整理分支） |

## 4. 验证

```powershell
git worktree list                 # 只剩主工作区
python sim/scripts/index_runs.py --write
python sim/scripts/check_repo_hygiene.py   # PASS，0 error
git status --porcelain=v1
```

- `git worktree list`：只剩 `E:/Projects/FPGA-Alittle-Design`。
- 跟踪文件数：5,609（P0–P4 共 −29；P5 再做快照去重）。
- `check_repo_hygiene`：PASS，14 条重复告警（P5 处理）。
- `data/logs` 索引已刷新，新增本目录 `2026-10-19-worktree-inventory`。

## 5. 待人工裁决

- `preserved/dev-exe-sync/` 的 9 个文件：工作区版本 vs 当前 HEAD；若确认已被后续 commit 覆盖，可删抢救副本；若有独有改动，从该目录取回，不要从旧 worktree 找。
- `preserved/rtl-worktree/id_ex_ooc/id_ex_stage_synth.dcp`：是否要作为证据入库或只留哈希；目前只在抢救目录，未加入 `data/logs` 索引。
- 隔离区 24.9 MB：有管理员权限后删除。

## 6. 未做

- P5 日志快照去重（924 个快照文件，834 个有同内容副本）。
- P6 docs 分层归档（建议 11/4 后）。
- commit（按 AGENTS 等用户确认）。
