# 快照输入清单（cnn-ooc-106904d01e0045089b9d1688ddce6e85）

> 本目录的 `inputs/`/`final-inputs/` 等源码/输入副本已按 `SNAPSHOT-MANIFEST.json` 去重。
> 这不是删除证据：可由 Git blob 恢复的副本已删除；唯一内容仍保留；恢复入口如下。

## 汇总

- 快照根：inputs/
- 文件：11
- 可恢复（Git blob）：8
- 保留（canonical/unique）：3
- 删除的重复副本：0

## 恢复

```powershell
python sim/scripts/restore_snapshot.py --run cnn-ooc-106904d01e0045089b9d1688ddce6e85 --check
python sim/scripts/restore_snapshot.py --run cnn-ooc-106904d01e0045089b9d1688ddce6e85 --restore
```

`--check` 只检查当前文件和恢复源是否存在；`--restore` 把缺失的副本写回原路径并校验 sha256。
清单里的每条记录包含 `path`、`sha256`、`git_blob`、`action`、`canonical`。
