# Worktree 与大缓存清理前抢救记录（2026-10-19）

> 目的：在删除 4 个额外 worktree 和 `sim/build` 之前，先把**只存在于 worktree/缓存**的内容保存到仓库内可追溯的位置。
> 这不是验收证据；是“删除前抢救清单”。原始 worktree 的完整状态已尽量保留在 `preserved/`。

## 1. 抢救内容

| 来源 | 内容 | 文件数 | 大小 | 位置 |
|:---|:---|---:|---:|:---|
| `FPGA-Alittle-Design-rtl` | 3 个 `d3-repro-*` 日志 + `id_ex_ooc/utilization.rpt`；2 个 `.jou/.dcp` 仅本地 | 4 + 2 | 约 100 KB | [`preserved/rtl-worktree/`](preserved/rtl-worktree/) |
| `FPGA-Alittle-Design-vision` | 7 个顶层 Vivado 日志 + `retry_open_fs.log`；6 个 `.jou` 仅本地 | 7 + 6 | 约 260 KB | [`preserved/vision-worktree-logs/`](preserved/vision-worktree-logs/) |
| `dev-exe-sync` | 9 个与当前 HEAD 不同的文件 + `tight_setup_hold_pins.txt` 重命名目标 + status/diff/conflicts/head | 15 | 4.5 MB | [`preserved/dev-exe-sync/`](preserved/dev-exe-sync/) |
| 入库抢救文件 | SHA256 清单 | 26 行 | — | [`preserved-sha256.txt`](preserved-sha256.txt) |
| 仅本地文件 | `.jou/`.dcp`（生成物，不入库） | 8 行 | — | [`local-only-sha256.txt`](local-only-sha256.txt)；文件在 `build/artifacts/worktree-rescue/` |

> `.jou`、`.dcp` 是 Vivado 生成物，按 `.gitignore` 不入库；本地副本在 `build/artifacts/worktree-rescue/`，哈希见 `local-only-sha256.txt`。克隆仓库不会包含它们；需要时用原 worktree 的构建入口重建。

### dev-exe-sync 需要人工裁决的 9 个文件

1. `sim/vision/test_c01_park_capture.py`
2. `plan.md`
3. `docs/project-closeout-three-person-checklist.md`
4. `src/vision_client/rounds.py`
5. `docs/vision-live-semantics.md`
6. `src/pynq_host/c01_park_capture.py`
7. `sim/scripts/run_vision_python.sh`
8. `src/pynq_host/vision_live_service.py`
9. `docs/c01-ddr-frame-ownership-v0.md`

原始 worktree 处于未完成 merge（4 个 `UU` 冲突）。上面的副本是**工作区当前版本**，不是合并结果；`status.txt`、`diff-unstaged.patch`、`diff-cached.patch`、`conflicts.txt` 保留了当时状态。若这些内容已被后续 commit 覆盖，可丢弃；若有独有改动，先从本目录取回，不要从旧 worktree 直接复制。

## 2. 发布包

`sim/build/nc-offboard-release-20261014.zip`（78,183,698 B）是 NC 离板发布包，包含 `vision_preview.exe`、`docs/`、`replay-example/` 和 `manifest.json`。已移动到：

```text
build/artifacts/nc-offboard-release-20261014.zip
```

SHA256：`AED1205E470C0CAC2B819D758BBB05B2131A0858D439EF53165AB812AB7F0393`
（见 [`release-artifact-sha256.txt`](release-artifact-sha256.txt)）

`build/artifacts/` 已加入 `.gitignore`，不提交；它是本地发布物，不是源码。

## 3. 缓存清单

删除前记录了 `sim/build` 的完整文件清单（路径+字节）：

- [`sim-build-top.txt`](sim-build-top.txt)：顶层目录/文件的大小汇总（19k 文件中的顶层视图）。
- [`sim-build-files.txt`](sim-build-files.txt)：全部 18,938 个文件的路径与大小。

这些是“删掉了什么”的审计线索；缓存本身可由 `sim/scripts/` 的构建/仿真入口重建，不保证逐字节一致。

## 4. 执行结果（2026-10-19）

- 4 个 worktree 已 `git worktree remove --force` 并 `prune`；`git worktree list` 只剩主工作区。
- 本地已合并分支 `dev/bench`、`dev/verify` 已删除；保留 `dev/riscv`、`dev/vision`、`dev/exe`、`dev/model`、`main`。
- `sim/arch_test/suite`（1.29 GB）已删除；`sim/scripts/fetch_arch_test.sh` 可重新 clone。
- `sim/build`（18,938 文件 / 1.86 GB）已删除大部分；剩余 803 文件 / 24.9 MB 因 ACL 拒绝访问，无法删除，已整体移动到仓库外隔离区：
  `E:/Projects/FPGA-Alittle-Design-cleanup-quarantine/sim-build-20261019`
  该目录不属于仓库，不影响 `git status`/`sim/`；有管理员权限后可手动删除。
- 仓库工作区从约 3.81 GB 降到约 **481 MB**（含 `build/artifacts` 的 78 MB 发布包和 `.git` 的 105 MB）。
- `build/artifacts/nc-offboard-release-20261014.zip` 保留，SHA256 见上。

> 如果后续发现某个 worktree 内容其实需要保留：从本目录 `preserved/` 取回，而不是从已删除的 worktree 取。
