# 快照输入清单（2026-10-11-c01-probe-evidence）

> 本目录的 `inputs/`/`final-inputs/` 等源码/输入副本已按 `SNAPSHOT-MANIFEST.json` 去重。
> 这不是删除证据：可由 Git blob 恢复的副本已删除；唯一内容仍保留；恢复入口如下。

## 汇总

- 快照根：settled-script-archive/
- 文件：1
- 可恢复（Git blob）：0
- 保留（canonical/unique）：1
- 删除的重复副本：0

## 恢复

```powershell
python sim/scripts/restore_snapshot.py --run 2026-10-11-c01-probe-evidence --check
python sim/scripts/restore_snapshot.py --run 2026-10-11-c01-probe-evidence --restore
```

`--check` 只检查当前文件和恢复源是否存在；`--restore` 把缺失的副本写回原路径并校验 sha256。
清单里的每条记录包含 `path`、`sha256`、`git_blob`、`action`、`canonical`。
