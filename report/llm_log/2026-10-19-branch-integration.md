# 分支 PR 合并与同步记录（2026-10-19）

> 执行顺序：`#79 → #80 → #81 → #82 → #83`；全部使用 merge commit，owner 授权 admin bypass 通过 `protect-main` 的 1-approval 规则。
> 合并后所有开发分支 fast-forward 到 main 并推送远端。

## PR 与合并提交

| PR | head → base | 合并提交 | 说明 |
|:--:|:---|:---|:---|
| #79 | dev/model → main | `6824d69` | 10-15/10-17 证据、M3 卡点、工位概念稿 |
| #80 | chore/repo-cleanup → main | `43fdde6` | 仓库整理 P0–P7 |
| #81 | dev/riscv → main | `b6a537f` | J02/J03/J04 协处理器、固件、控制面与收口证据 |
| #82 | dev/exe → main | `3141351` | EXE 识别范围表改版与 C01 ordering 测试 |
| #83 | chore/refresh-evidence-index-20261019 → main | `8d664b9` | 合并后证据索引刷新 |

## 冲突与解决

- `#81` 与 cleanup 后 main 冲突 3 个文件：`docs/README.md`、`docs/project-overview.md`、`src/coprocessor/README.md`。
- 解决口径：保留 cleanup 的 5 分钟导航、docs/contracts 目录和已校正计数；叠加 dev/riscv 的 J04 状态、10 组 INT8 入口、`plan.md`/交接索引、`mac_lane/dot8` 边界和 venv 复现命令。
- `docs/coprocessor-integration-v0.md` 由 merge 跟随 cleanup 移动到 `docs/contracts/coprocessor-integration-v0.md`。
- 新增 `docs/coprocessor-handoff-v0.md` 移入 `docs/contracts/coprocessor-handoff-v0.md`，并更新 C03/计划/README 链接。
- 新增根 `.gitattributes`：`data/logs/** -text -whitespace`，保留原始证据字节；Markdown 索引仍为 LF 文本。
- 冲突解决提交：`1a687e5`（Merge origin/main into dev/riscv）。

## 合并后验证

- `run_coprocessor_python.sh all`：**10/10 PASS**（含 manifests）。
- `run_coprocessor_iverilog.sh all`：26 个测试日志全部 PASS；无 FAIL/ERROR 日志。
- dev/exe 定向测试：`test_c01_capture_ordering.py`、`test_vision_rounds.py`、`test_vision_live_standin.py` PASS。
- `check_repo_hygiene.py`：PASS，0 error；12 条证据区重复告警保留。
- `index_runs.py --check`：OK。
- 当前所有分支：`main`、`dev/riscv`、`dev/vision`、`dev/model`、`dev/exe`、`chore/repo-cleanup` 均与 main 同步；最终推进记录以 `git log` 为准。

## 回退

- 整体回退到合并前 main：`pre-branch-merge-2026-10-19` → `0cb3d42`。
- 单 PR 回退：GitHub revert 对应 merge commit，不 force push main。
- 冲突解决提交 `1a687e5` 的父亲是 `401ee67` 与 `43fdde6`，可单独审查。
