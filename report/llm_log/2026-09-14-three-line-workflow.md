# [2026-09-14] 协作记录：三线并行工作流与分支保护落地——plan.md 重构为派活文档

> 标签：#协作流程 #架构决策 #工具链
> 平台：OpenCode ｜ 模型：opencode-go/deepseek-v4.1-flash
> 相关 commit：`3d944a8`（工作流文档与 plan 分工改写）、`34c8435`（.gitattributes）、`9407c6e`（PR #7 合并）；本文档随本次提交入库

## 1. 任务与初始提示词

从"如何当组长"的讨论开始，逐步落地为可执行的协作机制：

> "我作为整个项目的管理者，该如何 push 我的组员干活，或者安排他们分工呢，之前我只是一个组员，现在这个比赛我是组长"
> "我的 plan 想分成同步的三部分，每个人做一部分，在现在的文件中分出一个 branch 出去，每到一个节点我来进行合并"
> "你把 plan.md 改一下吧，现在这个文档有点乱，我要根据这个给大家分第一阶段的工作，详细一些"

## 2. 模型第一版方案

- 管理建议：组长的杠杆 = 让 plan.md / 例会 / issue 三个既有设施转起来；盯产出不盯工时；把有挑战的任务真正分出去
- 工作流：GitHub 分支保护（PR + 1 approval）+ 三线分支 + 每周日合并日；分支 `dev/rtl` / `dev/verify` / `dev/bench`
- 文档：`docs/git_learning/branch_workflow.md` 人话版教程、`.github/PULL_REQUEST_TEMPLATE.md`、onboarding 与 README 同步
- plan.md：按"第一阶段 = 阶段 0 + Part A 收口"重构，逐人逐周拆分任务与交付物

## 3. 失败现象（真实偏差，如实记录）

1. **"三部分并行"的最初理解有合并风险**：plan.md 的 A/B/C 是串行依赖（B 改的就是 A 的文件），若三人各领一个直接并行开分支，每周 PR 都会解冲突。纠正为**按工种/目录边界切**：RTL / 验证 / 基准三线，RTL 线内部 B→C 仍串行
2. **plan.md 头部编辑不匹配**：Edit 的 oldString 与文件实际文本差一个空格（`＋数据转发 ＋ 轻量分支预测`），首次编辑失败；重读文件后按实际文本修正
3. **`git branch` 多分支语法错误**：`git branch dev/rtl dev/verify dev/bench` 只认第一个参数为分支名，命令报用法错误；改为逐个 `git branch` 创建
4. **领队 PR 自批盲区**：分支保护要求 1 人批准且作者不可自批；组员暂时联系不上，PR #7 卡住。兜底：临时将规则集 `enforcement` 置 `disabled` → 合并 → 立即恢复 `active`，并用 API 复核规则完好（PR 必需 + 1 approval + 禁删/强推全部在）
5. **GitHub 分支保护 UI 已改版为 Rulesets**：按旧版 classic branch protection 的教程找不到入口；改为按 Rulesets 页面逐项指导（Enforcement 必须改 Active、Add target → Include by pattern → main），并提示"Disabled 状态等于没设"

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 用户要按"流水线三优化点"并行分工 | A/B/C 同改一批文件且严格依赖，直接并行=合并地狱 | 改按工种三线切，目录零交集；验证/基准线对 design_v0 契约先行 | ✅ plan.md §2/§3 落地 |
| 2 | Edit 报 oldString not found | 复制时少了一个空格 | 重读 plan.md 头部按实际文本匹配 | ✅ 编辑通过 |
| 3 | `git branch dev/rtl dev/verify dev/bench` 报用法错误 | git branch 不支持一次多建 | 逐条创建 + `-u` 推送上游 | ✅ 三分支在远端可见 |
| 4 | PR #7 `reviewDecision: REVIEW_REQUIRED`，组员联系不上 | 规则正确执行，但领队工作流存在单人盲区 | 临时停用 → 合并 → 立即恢复，并复核规则 | ✅ 保护复验 active |
| 5 | 用户截图 Rulesets 页面求配置 | classic 教程不适用新 UI | 按 Rulesets 逐项配置指导 | ✅ protect-main 生效，直推实测被 GH013 拒绝 |

## 5. 最终结论

- **工作流**：三线并行 + 每周日 PR 合并日 + `protect-main` 规则集（PR 必需 + 1 批准 + 禁删除/强推 + 零绕过）；操作教程与 PR 模板入库（`branch_workflow.md`、`PULL_REQUEST_TEMPLATE.md`）
- **plan.md 重构**：六节结构，新增 §3 第一阶段（9/14–9/27）逐人任务（RTL 吃透+收口 / 验证测试先行 / 基准工具先造）；技术内容与验收标准零改动（遵守"M1 零改动"红线）；修正 9/27 星期笔误、板卡项按 issue #1 标注顺延
- **验证方式**：直推 main 实测被 GH013 拒绝；PR #7 走完整流程合并（`9407c6e`）；规则集 API 复核完好

## 6. 经验沉淀

- 触发条件：多人（含新手）并行开发的 Git 工作流设计；分支保护启用后领队自身 PR 的自批盲区 #skill候选
- 排查步骤：
  1. 并行切分**按目录边界**，不按功能点；有依赖的功能放同一条线串行
  2. 分支保护配置完成后必须做**拒绝测试**（直推一次验证 GH013），并记录兜底程序（disabled → merge → active → 复核）
  3. 领队 PR 需他人批准是刻意设计；兜底仅限联系不上评审人时使用，事后必须复核规则完整性
- 适用范围（换题目/换板卡/换平台是否成立）：均成立；Rulesets 配置适用于任何 GitHub 仓库
