# 仓库整理 P5–P6：快照去重与文档分层（2026-10-19）

> 前置：P0–P4 已完成；P4 记录见 [`2026-10-19-repo-cleanup-p4.md`](2026-10-19-repo-cleanup-p4.md)。
> 本次未改 RTL/软件行为；P7 已提交，见 [P7 记录](2026-10-19-repo-cleanup-p7.md)。

## P5 日志输入快照去重

### 结果

- 扫描 16 个运行目录，命中 924 个 `inputs/final-inputs/handoff-inputs/exe-*` 快照文件。
- 先做 1 个 run 试点（`cnn-ooc-a96...`，11 个文件）：删除 → `--check` → `--restore` 11/11 → 再删除，全部通过。
- 全量处理：待删 **599**（564 个可由 Git blob 恢复 + 35 个保留一份 canonical 后删其余）；本次实际删除 **588**，另 11 个已在试点删除。
- 保留 **325** 个文件（89 个 canonical + 236 个唯一内容），约 7 MB 重复内容被移除。
- 每个涉及的运行目录新增：
  - `SNAPSHOT-MANIFEST.json`：每条记录含 path/sha256/git_blob/action/canonical；
  - `SNAPSHOT.md`：汇总、恢复命令、边界说明。
- 恢复入口：`python sim/scripts/restore_snapshot.py --run <目录> --check` / `--restore`。
- 16/16 个 run 的 `--check` 通过（缺失文件都能由 Git blob 或 canonical 副本恢复）。

### 为什么不是把所有 924 个都删掉

- 236 个是唯一内容，删了无法从 Git 恢复；
- 89 个是“没有外部同内容副本”的 canonical 副本，必须留一份；
- 564 个虽然能恢复，但保留 manifest 才能知道“原来这里有什么”。

### 剩余重复告警

`check_repo_hygiene.py` 还有 12 条 >100 KB 的重复告警，主要是：

- `data/evidence/2026-10-03-arm-localize-baseline` 的 4 份 `input.json`；
- `data/evidence/2026-10-12-c01-exact-build-inputs` 与两个 `c01-capture-*` 的 HDMI IP 文档/PDF/XCI；
- 少量日志/PNG。

这些属于证据区，且部分被 README/manifest 直接引用；本次不继续删，避免破坏 48/48 完整性校验或原始证据可读性。若后续要做，按 P5 同样的 manifest 流程另开一步。

## P6 文档分层

### 结果

- `docs/` 根从 75 篇 Markdown 降到 **15 篇**（另 1 个 CSV 模板；5 篇中文/英文重复文档因 `installed.csv` 48/48 校验保留在根）。
- 新建并迁入 4 个目录：
  - `docs/contracts/`：8 篇（C01/C03/C04、检查、同步、CoreMark 等）；
  - `docs/runbooks/`：25 篇（上板、NC、训练、复现、数据采集等）；
  - `docs/research/`：6 篇（赛题、资源、方案对比、数据集审计）；
  - `docs/archive/`：17 篇（历史快照）。
- 每个子目录新增 `README.md`（职责、索引、边界）。
- 自动重写当前文档中的相对链接：**63 个文件 / 240 条链接**；历史 `data/logs`、`data/evidence`、`report/llm_log` 不改写。
- `docs/README.md`、`docs/project-map.md` 已更新目录表与入口；根 `README.md`、`plan.md`、`src/*`、`report/module1-closure.md` 的链接已同步。

### 保留在 docs 根的例外

- `localization-dataset-audit.md`、`localization-experiment-results.md`、`方案探索报告.md`、`工作进展汇报.md`、`修订方案-受控流水线.md`：被 `data/evidence/2026-10-10-fastener-handoff/installed.csv` 引用，移动会破坏 48/48 校验。
- `branch-layout.md`、`non-algorithm-plan.md`、`onboarding.md`、`project-closeout-three-person-checklist.md`、`project-map.md`、`project-overview.md`、`README.md`、`repo-hygiene.md`、`workflow.md`：当前入口/状态。

## 验证

| 检查 | 结果 |
|:---|:---|
| `python sim/scripts/check_repo_hygiene.py` | **PASS**，0 error，12 条重复告警（证据区，见上） |
| `python sim/scripts/index_runs.py --check` | OK |
| 16 个 run 的 `restore_snapshot.py --check` | 16/16 PASS |
| 试点 `--restore` 后 sha256 | 11/11 匹配 |
| `python docs/file-guide/tools/generate.py --scope source --date 2026-10-19` + `verify.py` | 729 文件，PASS |
| `git diff --check` / `git diff --cached --check` | 无输出 |
| 仓库工作区 | 约 **469 MB**（P4 后 481 MB；P5/P6 后 469 MB） |
| `docs/` 根 | 16 个文件（15 md + 1 csv） |
| 最终跟踪文件 | **5,125**（已提交；未达到原计划 4,800，见下） |

> 未达到 4,800 的原因：P5 只删“可恢复/重复”的快照，保留了 236 个唯一文件和 89 个 canonical 副本；剩余大部分是 `data/logs`/`data/evidence` 的原始证据。继续压到 4,800 需要归档证据目录，可能影响可读性和 48/48 校验，本次不做。

## 未做

- P7 已 commit + tag：`2f5475b`（整理）、`ebf739e`（索引刷新）；tag `post-cleanup-2026-10-19`，见 [P7 记录](2026-10-19-repo-cleanup-p7.md)。
- 没有跑 RTL 全量回归：未改 RTL/软件。
- 没有删除证据区的剩余重复（12 条告警），原因见上。
- 没有把 `docs/archive/` 再按月份细分；当前 17 篇已能按 README 索引找到。

## 回退

- 文档移动是 `git mv`，可 `git restore` / 从 `pre-cleanup-2026-10-19` 取回。
- 快照删除有 `SNAPSHOT-MANIFEST.json`；`restore_snapshot.py --restore` 可逐文件恢复。
- P6 前 `docs/` 备份：`E:/Projects/FPGA-Alittle-Design-cleanup-quarantine/docs-before-p6-20261019.zip`。
