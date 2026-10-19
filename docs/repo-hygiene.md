# 仓库卫生规则（Repo Hygiene）

> 目的：防止仓库再次膨胀成“需要逐文件索引才能看懂”。
> 适用：所有新增/移动/删除文件；与 [`AGENTS.md`](../AGENTS.md)、[`docs/workflow.md`](workflow.md) 一起执行。
> 检查入口：`python sim/scripts/check_repo_hygiene.py`。

## 1. 十条规则

1. **根目录白名单**：只允许 `README.md`、`plan.md`、`AGENTS.md`、`LICENSE`、`.gitignore`、`.gitattributes`；目录只允许 `src/`、`sim/`、`build/`、`board/`、`data/`、`docs/`、`report/`、`skill/`、`models/`、`results/`、`.github/`。`models/`、`results/` 是已记录的例外。
2. **每个顶层目录有 README**：说清是什么、入口、不做什么。
3. **每次运行一个目录**：`data/logs/YYYY-MM-DD-topic/`，必须有 `README.md`；缺说明标记 `PROVENANCE GAP`。
4. **运行 README 六要素**：日期、commit、命令、结果、产物、边界/未完成项。
5. **快照有 manifest**：`inputs/` 必须有 `INPUTS.md` + `manifest.json`（路径、sha256、来源 commit/包）；能由 commit 恢复的不存整棵源码树。
6. **二进制有理由**：入库的 `.xsa`/`.hwh`/`.bit`/`.png`/`.pt` 等要写用途、sha256、来源/重建方式；>5 MB 走 allowlist。
7. **生成物不入库**：file-guide 输出、`.vvp`、`__pycache__`、Vivado/XSim 中间产物、PyInstaller dist/venv 一律 ignore。
8. **命名**：新目录 `YYYY-MM-DD-kebab-topic`；新路径不含空格/中文（外包原文除外）；不建 hash-only 目录。
9. **单一事实源**：状态只在 `plan.md` §3；指标只在 `metrics.csv`；接口只在 `design_*.md`；其他地方链接，不复制。
10. **删除可回退**：删除前有 tag/commit + 清单；删除后在本目录或 `report/llm_log/` 留一条记录。

## 2. 预算

| 项 | 预算 | 超限处理 |
|:---|---:|:---|
| 跟踪文件数 | ≤4,800 | 新增大批日志前先归档/去重 |
| 跟踪工作区 | ≤175 MB | 新增大图/模型先评审 |
| `data/logs` 单目录文件数 | ≤600 | 超了拆子目录或归档 |
| 单个入库文件 | ≤8 MB（allowlist 例外） | 写理由 + sha256 |
| 根目录条目 | ≤17 | 新目录先问 |

## 3. 生成物与输出位置

- file-guide：`python docs/file-guide/tools/generate.py --scope source --date YYYY-MM-DD` → `build/file-guide/`（ignore）。
- Icarus：`sim/build/`（ignore）；`.vvp` 不再入库。
- XSim：`sim/xsim.dir/`、`*.log`、`*.jou`、`*.wdb`（ignore）。
- Vivado：`build/run/`、`build/reports/fmax/`、*.dcp、*.bit（ignore）。
- Python：`__pycache__/`、`.pytest_cache/`、`.venv/`（ignore）。

## 4. 检查命令

```bash
python sim/scripts/check_repo_hygiene.py          # 全量只读检查
python sim/scripts/check_repo_hygiene.py --json   # 机器可读
python sim/scripts/index_runs.py --check          # 检查 data 索引是否过期
python sim/scripts/snapshot_manifest.py --json    # 快照去重概览
python sim/scripts/restore_snapshot.py --run <run> --check   # 验证快照恢复源
```

检查项：根目录白名单、跟踪生成物、README 覆盖、索引新鲜度、`metrics.csv` 证据路径、当前文档相对链接、大文件/重复文件告警。

## 5. 例外流程

1. 在 `docs/repo-hygiene.md` 或对应 README 写理由。
2. 加 allowlist（脚本内集中维护，不分散）。
3. PR 说明“为什么这次必须例外、何时回收”。
