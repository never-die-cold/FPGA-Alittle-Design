# 仓库整理 P0–P3 执行记录（2026-10-19）

> 分支：`chore/repo-cleanup`（从 `dev/model` 切出）。
> 基线 tag：`pre-cleanup-2026-10-19`（`d87c9cc`）。
> 范围：P0 冻结、P1 本地垃圾、P2 索引/导航、P3 退役生成物。**未执行 P4 worktree 删除；未 commit。**

## 1. 改了什么

### P0 冻结

- 新建分支 `chore/repo-cleanup`，未动 `main`。
- 新建 tag `pre-cleanup-2026-10-19`。
- 新增本目录的 `2026-10-19-repo-cleanup-baseline.md`（盘点基线）。

### P1 本地垃圾

删除（均为未跟踪/可重建）：

- 根：`-p` 空目录、`NA/`、`.Xil/`、`clockInfo.txt`、`retry_open_fs.log`、`.zcodeignore`。
- 缓存：102 个 `__pycache__/`、`sim/xsim.dir/`、xsim/xelab/xvlog 日志、`sim/*.vcd`、`sim/*.wdb`。
- 编译产物：`src/riscv_fw/*.elf`、`*.bin`（7 个）。
- 空目录：`data/logs` 下 11 个；`sim/build/arm-localize-package-*` 中 10 个空目录因 ACL 拒绝未删（留给 P4 整目录清理）。

未删除：`sim/build` 主体、`sim/arch_test/suite`、任何 worktree。

### P2 索引与导航

新增：

- `src/README.md`。
- `data/logs/README.md`（110 个运行索引）+ `data/logs/_template/README.md`。
- `data/evidence/README.md`（15 个证据主题索引）+ `data/evidence/_template/README.md`。
- 22 个缺 README 的 `data/logs/*` 目录说明（含 5 个 `cnn-ooc-*`、2 个 `c01-capture-*`）。
- 8 个缺 README 的 `data/evidence/*` 目录说明。
- `docs/project-map.md`、`docs/repo-hygiene.md`。
- `sim/scripts/index_runs.py`、`sim/scripts/check_repo_hygiene.py`。

重写/更新：

- `docs/README.md`：改为 5 分钟导航；file-guide 生成物改为按需生成。
- 根 `README.md`：当前进度指向 `plan.md`；目录树补 `models/`、`results/` 例外。
- `docs/branch-layout.md`：补实际分支与 4 个 worktree。
- `AGENTS.md`、`docs/workflow.md`：加 `docs/repo-hygiene.md` 入口。
- 5 篇历史文档加“历史快照”状态行；5 篇重复/版本文档加来源说明。
- `data/README.md`：补 logs/evidence 索引和 models/results 例外。
- `plan.md`：变更记录加 2026-10-19 一条。

### P3 退役生成物

- 删除 20 个 `docs/file-guide` 生成文件（index.html/files.csv/files.json/validation.json + 16 个 sections），保留 `README.md` 与 `tools/`。
- 删除 9 个跟踪的 `.vvp`（Icarus 编译产物）。
- `docs/file-guide` 生成器改为输出 `build/file-guide/`（忽略），默认 `--scope source`（720 个文件，不再索引 data 日志/证据）。
- `.gitignore` 增加 `*.vvp`、`build/file-guide/`、旧 file-guide 输出、缓存/临时文件。

## 2. 验证

| 检查 | 命令 | 结果 |
|:---|:---|:---|
| 工作区检查 | `git diff --check` / `git diff --cached --check` | 无输出 |
| 跟踪文件数 | `git ls-files \| Measure-Object` | 5,609（整理前 5,638，−29） |
| 卫生检查 | `python sim/scripts/check_repo_hygiene.py` | PASS，0 error，14 条重复告警（留 P5） |
| 索引新鲜度 | `python sim/scripts/index_runs.py --check` | OK |
| file-guide 生成 | `python docs/file-guide/tools/generate.py --scope source --date 2026-10-19` | 720 文件，missing=0，relations=2,776 |
| file-guide 校验 | `python docs/file-guide/tools/verify.py` | PASS |
| 生成物忽略 | `git check-ignore -v build/file-guide/README.md` | 命中 `.gitignore:64` |
| RTL 回归 | 未跑 | 本次未改 RTL/软件行为；删除的 `.vvp` 是编译产物 |

## 3. 决策：没有删的东西

- **重复文档不删**：`docs/方案探索报告.md`、`localization-experiment-results.md`、`localization-dataset-audit.md`、`工作进展汇报.md`、`修订方案-受控流水线.md` 都被 `data/evidence/2026-10-10-fastener-handoff/installed.csv` 的 48/48 校验引用；删了会破坏证据。改为加“副本/版本说明”，保留原文。
- **`models/`、`results/` 不移动**：同上，且被代码默认路径引用；已在 README/地图标注为结构例外。
- **24 个嵌套 `.gitattributes` 不动**：它们在保护证据字节；合并会引入行尾 churn。
- **`data/logs` 的 9 个 `.vvp` 外的原始日志不删**：等 P5 按 manifest 去重。

## 4. 未执行（待确认）

- **P4**：4 个 worktree（其中 `dev-exe-sync` 有未完成 merge、`-rtl` 有 4 个未跟踪日志）与 `sim/build`/`suite` 缓存。需要 owner 确认后按“先保存、再删除”执行。
- **P5**：924 个日志快照去重（834 个有同内容副本）。
- **P6**：`docs/` 分层归档（提交后）。
- **commit**：按 AGENTS，未经你确认理解不 commit；当前改动都在工作区，可用 `pre-cleanup-2026-10-19` 回退。

## 5. 回退方式

- 被删的 29 个跟踪文件：`git show pre-cleanup-2026-10-19:<path>`。
- 未跟踪的本地垃圾不可回退，但都是可重建物。
- 工作区改动：`git diff` / `git status`；未 commit，可直接丢弃或继续 review。
