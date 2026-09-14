# [2026-09-14] 协作记录：理解门槛（understand-gate）流程建立

> 标签：#架构决策 #流程 #文档
> 平台：OpenCode ｜ 模型：opencode-go/glm-5.3-flash
> 相关 commit：本次提交（code_review_checklist、understand-gate skill、README/onboarding/llm_log 规则同步）

## 1. 任务与初始提示词

> "push"（工作区残留一套完整的理解门槛文档改动，需提交推送）

背景：团队全员 Verilog 初学者 + AI 协作开发，先前的改动已确认"能跑"，但缺少"人理解"环节的强制流程。

## 2. 方案

建立"看不懂的代码不许入库"铁律，双轨落地：

- **OpenCode 自动化**：`.opencode/skill/understand-gate`——commit AI 生成代码前强制"逐段讲解 + 3 道理解测试题"，用户答对才允许 commit，讲解与测试全量落盘 `report/llm_log/`
- **跨平台兜底**：`docs/code_review_checklist.md`（作者自查 5 条 + 复核人抽查），供 Kimi Work 等其他 agent 平台手动执行

## 3. 偏差与修正点

1. **README 原第 2/3 条顺延为 3/4**：插入"入库门槛"为新第 2 条后，后续编号顺延，onboarding 的"完成标准"同步加门槛步骤
2. **纯文档 commit 例外**：skill 自身规定纯文档/.gitignore/llm_log 类 commit 不走门槛流程——本次提交即属此类，直接提交

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 工作区状态核查：main == origin/main == 66e22dc，批准的考核备考方案已提交并推送 | "push"的实际对象是未提交的理解门槛文档 | 确认五份文件（README/onboarding/llm_log README/checklist/SKILL.md）互链完整后整体提交 | ✅ 引用闭环（README→checklist→skill→llm_log） |
| 2 | .gitignore 无 .opencode 排除项 | skill 定义应随仓库分发（队友 clone 后同样生效） | 一并入库 | ✅ |

## 5. 最终结论

理解门槛双轨落地：OpenCode 会话内由 skill 强制执行，其他平台走检查单；理解测试与讲解稿全量存 `report/llm_log/`，作为答辩演练与期末复盘素材。验证方式：五份文档交叉引用逐条核对；纯文档 commit 按例外规则直接提交。

## 6. 经验沉淀

- 触发条件：AI 协作团队需要保证"人真正理解 AI 产出"，而非仅功能通过 #skill候选
- 排查步骤：
  1. 门槛卡在 **commit 之前**（不是 review 之后）——成本最低的拦截点
  2. 测试题必须针对本次提交的具体代码问"如果改成 XX 会怎样"，防止背答案
  3. 落盘的讲解稿与测试记录就是决赛上机考核与答辩的备考素材，一鱼两吃
- 适用范围：任何 AI 协作开发仓库均可复用；与 `docs/exam_prep.md` 的考核备考互补（理解过程即备考过程）
