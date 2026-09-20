# [2026-09-20] 协作记录：检查点体系落地——M1 验收拆三个 gate issue，M2–M4 里程碑一次建齐

> 标签：#协作流程 #工具链
> 平台：OpenCode ｜ 模型：deepseek/deepseek-flash
> 相关 commit：本文档随本次提交入库（分支 `docs/m1-gate-issues`）

## 1. 任务与初始提示词

从"看还有什么 issue 可做"开始，收敛为检查点体系建设：

> "看看我的项目还有什么issue可以做的，我想把issue作为我们项目的一个检查点"

背景：M1 里程碑已建（due 10/4），但挂账的 4 个 issue 全是已关闭的环境项（板卡 / Vivado / 工具链 / 野火板），Part A/B/C 关键路径 **0 个 open issue**；#5（L3.5 stretch）/#6（L4 采购）要到 10/25 窗口才动。既有约定（onboarding §5）是"能用 commit 闭环的计划内任务不建 issue"。

## 2. 模型第一版方案

- 盘点现状：4 closed / 2 open（均非当前关键路径）/ M1 open=0
- 粒度选择：**里程碑 = 检查点，gate issue = 验收单**，不建任务级 issue（不重复 plan.md 派活）
- 落地：M1 三个 gate issue——#19 Part A（9/27）/ #20 Part B（10/1）/ #21 Part C + M1 收口（10/4）；M2–M4 里程碑一次建齐（due 10/18 / 10/25 / 11/4）
- 回链：README 开发计划、`src/riscv/plan.md` §3.5/§4.2/§4.3、`docs/onboarding.md` §5

## 3. 失败现象（真实偏差，如实记录）

1. **API 创建里程碑 `due_on` 被减一天**：入参 `2026-10-18T00:00:00Z`，存储为 `10-17`（M3/M4 同样 −1 天）；同源 M1（UI 创建）无此现象
2. **PowerShell 下 jq 表达式引号被吞**：`--jq` 表达式报解析错误，但创建请求已发出并生效（报错发生在响应过滤阶段）——靠复查 `gh api .../milestones` 才确认 M2/M3/M4 均已创建，避免重复建
3. **控制台回显中文乱码**（GBK 终端解码 UTF-8 输出），一度怀疑 issue 正文入库损坏；改用 `cmd` 重定向保存原始 JSON + `Get-Content -Encoding UTF8` 复核，确认入库为正确 UTF-8

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 创建 M2 后 due_on 回读为 10-17 | API 写入路径对日期做时区折算，产生 −1 天偏移 | 用 PATCH 逐个重写 due_on | ✅ M2 10/18、M3 10/25、M4 11/04 |
| 2 | jq 表达式解析错误，但疑似资源已建 | gh 先发请求、后过滤响应，jq 报错不代表请求失败 | 复查里程碑列表 | ✅ M2/M3/M4 均在，未重复创建 |
| 3 | issue 正文在终端显示乱码 | 终端 GBK 解码所致，非入库问题 | `cmd /c "gh api ... > file"` + UTF-8 读取原始 JSON | ✅ `任务描述` 等中文完整 |

## 5. 最终结论

- **检查点体系**：里程碑承载阶段节点（检查点），gate issue 承载验收清单（引用 plan.md 对应章节，全勾关闭）
- 三个 gate issue 已建并挂 M1：#19（task/rtl/verify）、#20（task/rtl/verify）、#21（task/rtl/verify/docs）；#5/#6 stretch 未动
- 回链已入库：README 开发计划表下方新增检查点说明；plan.md §3.5/§4.2/§4.3 挂 issue 链接；onboarding §5 第 3 条从"到阶段再建"更新为"M1–M4 一次建齐 + gate issue 惯例"
- 验证方式：`gh issue view ... --json milestone` 均为 M1；里程碑 due 回读复核；issue 正文用原始 JSON 复核

## 6. 经验沉淀

- 触发条件：需要把"阶段验收"变成可追踪检查点，而既有 issue/里程碑与关键路径脱节 #skill候选
- 排查步骤：
  1. 建检查点前先盘点 issue 状态与里程碑挂账，确认粒度为 gate 级而不是任务级
  2. GitHub API 写 `due_on` 后必须回读复核（时区会改日期）；批量写操作遇到报错先查资源是否已创建
  3. Windows 下中文正文入库后，用原始 JSON / UTF-8 方式复核，不要信控制台回显
- 适用范围（换题目/换板卡/换平台是否成立）：成立；里程碑与 issue API 用法、中文编码复核方法对任何 GitHub 项目通用
