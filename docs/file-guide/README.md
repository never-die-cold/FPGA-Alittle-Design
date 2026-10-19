# 逐文件说明（按需生成）

> 这是一个**按需生成**的索引，不是验收报告，也不再入库。
> 当前导航：[docs/README.md](../README.md)、[docs/project-map.md](../project-map.md)。
> 历史生成物（2026-10-13）保留在 Git 历史里；工作区不再维护快照。

## 用途

查“这个文件是干什么的、和谁有关”时，生成一份完整索引。源码/核心脚本用人工角色说明；其余文件按标题、字段、格式和同目录关系生成。

## 生成

```powershell
python docs/file-guide/tools/generate.py --scope source --date 2026-10-19
python docs/file-guide/tools/verify.py
```

- 默认 `--scope source`：源码、测试、构建、文档、报告、skill；不含 `data/logs`、`data/evidence`、`data/golden`。
- `--scope all`：连 data 日志/证据一起索引；文件多、易过期，只在需要时用。
- 输出目录：`build/file-guide/`（被 `.gitignore` 忽略）。

## 输出

```text
build/file-guide/
├── README.md          # 导航与目录索引
├── index.html         # 离线搜索页
├── files.csv          # 表格筛选
├── files.json         # 完整关系
├── validation.json    # 覆盖/关系/说明检查
└── sections/          # 按目录拆分的 Markdown
```

## 边界

- 生成器只读仓库文件，不执行项目代码。
- 关系是静态扫描结果，不保证实际调用；不能据此判断“已接入/已验收”。
- 索引过期不影响源码；需要最新说明时重新生成，不提交生成物。
