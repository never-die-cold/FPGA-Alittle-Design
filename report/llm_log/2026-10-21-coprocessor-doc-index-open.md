# [2026-10-21] 协作记录：交接文档双索引、OPEN 登记与下一执行点

> 标签：#docs #coprocessor #索引 #OPEN #收口
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`038f674` `de057ff` `36e0b87`

## 1. 任务与初始提示词

缺陷 3：把 `coprocessor-wc-interface.md`、`coprocessor-storage-plan.md`、
`coprocessor-vivado-checklist.md`、`coprocessor-nc-handoff.md` 加入 `docs/README.md`
（或对应 runbooks 索引），并检查 `docs/contracts/README.md` 是否覆盖新路径，确保无死链。
同时登记 OPEN-FW-1、OPEN-ENV-1、OPEN-DOC-1；把 `src/coprocessor/plan.md` 的下一执行点
指向 Windows Vivado 40 MHz 命令；写断点存档。

## 2. 模型第一版方案

在 `docs/README.md` 与 `docs/contracts/README.md` 同时加入四份文档入口；
把三条 OPEN 写入 NC 交接的“已知限制”，其中 OPEN-DOC-1 标“已修复”；
`src/coprocessor/plan.md` 记录 40 MHz compute/storage 两条命令；
新增 `report/llm_log/2026-10-21-board-gate-checkpoint.md` 七节存档。

## 3. 失败现象

1. 四份交接文档此前是“孤儿”，`docs/README.md` 与 `docs/contracts/README.md` 都搜不到。
2. `cop_job.hex` 曾入库但陈旧、无引用（OPEN-DOC-1）。
3. 裸命令 `all` 依赖系统 Python/NumPy，干净环境会失败（OPEN-ENV-1）。
4. checkpoint 若只写“all PASS”会掩盖裸命令退出 1 的事实。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 四文档无索引 | 交付物不可发现 | 两级 README 同时加入口 | `rg` 4/4 均命中 |
| 2 | `cop_job.hex` 陈旧 | 入库产物无引用 | Makefile 纳管 + E2E 加载 | OPEN-DOC-1 标已修复 |
| 3 | 裸 `all` 退出 1 | 环境依赖未写明 | checkpoint 记录双事实 + OPEN-ENV-1 | 不把环境失败写成 PASS |
| 4 | 下一执行点不明确 | 接手成本高 | plan 指向 Vivado 40 MHz 命令 | 可复制执行 |

## 5. 最终结论

四个文件名在 `docs/README.md` 与 `docs/contracts/README.md` 中均命中（4/4，两级索引）。
OPEN 共 4 条：OPEN-K2-1、OPEN-FW-1、OPEN-ENV-1、OPEN-DOC-1（已修复并留痕）。
checkpoint 固定七节，含“裸命令退出 1 / 显式 venv 退出 0”的双事实、K1–K5 与三缺陷提交、
责任人 TODO 与下一条 Windows Vivado 命令。

## 6. 经验沉淀

- 触发条件：交接文档写完但没有入口，或被修复的遗留问题没有留痕。
- 排查步骤：每个交付文档至少在总索引与领域索引各挂一次；OPEN 编号只增不删，
  修复后标“已修复”并写对应提交；存档区分“裸命令”和“可复现门禁命令”。
- 适用范围：任何多人交接仓库；换目录结构时重新跑索引 grep。
#skill候选
