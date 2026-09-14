# 上手指南（Onboarding）

> 这份指南带你在 **1 天内** 完成环境上手，之后就能跟上项目节奏。
> 遇到任何一步卡住，直接在群里问，不要自己死磕超过 30 分钟。

---

## 第一步：学会 Git 和项目管理（约 1 小时）

我们的所有代码和文档都在 GitHub 仓库：[never-die-cold/FPGA-Alittle-Design](https://github.com/never-die-cold/FPGA-Alittle-Design)

**你只需要先会 4 个命令**（其他用到再学）：

```bash
git clone https://github.com/never-die-cold/FPGA-Alittle-Design.git   # ① 把仓库拉到本地（只做一次）
git pull                  # ② 每次开工前：拉取别人的最新改动
git add . && git commit -m "我做了什么"   # ③ 保存自己的改动
git push                  # ④ 上传到仓库，队友才能看到
```

**三条纪律**：

1. 开工前先 `git pull`，下班前记得 `git push`
2. commit message 写清楚做了什么；如果是 AI 生成的代码，加一句 prompt 要点，例如：`feat: 灰度转换模块 (prompt: RGB888转灰度流水线, 一级寄存)`
3. 推送失败/提示冲突，不要强行覆盖，截图发群里

> 💡 不习惯命令行可以装 [GitHub Desktop](https://desktop.github.com/)，按钮操作，效果一样。
> 推荐教程：B 站搜"Git 一小时入门"，边看边跟着敲一遍。

---

## 第二步：学会阅读 Markdown 文档（约 10 分钟）

项目所有文档都是 `.md` 格式（带标记符号的纯文本，GitHub 会自动渲染成漂亮排版）。三种看法任选：

- **最简单**：直接在 GitHub 仓库网页上点文件看
- **本地看**：把 `.md` 文件拖进 **Notion**（导入 Markdown），或用 VS Code 打开按 `Ctrl+Shift+V` 预览
- 看到 `#` 是标题、`[]` 是待办框、表格就是表格，不用管符号本身

---

## 第三步：学会使用 AI Agent（约 1 小时）

Agent = 能帮你**实际干活**的 AI（写代码、改文件、跑命令），不只是聊天。我们项目会用到 Kimi Work、OpenCode、Codex、Pi agent 等，用法相通：

**入门三原则**：

1. **给上下文，不给一句话**——❌"帮我写个模块" → ✅"在 src/vision/ 下写一个 RGB888 转灰度的 Verilog 模块，一级流水，接口用 valid/ready 握手"
2. **产出必须验证**——AI 写的代码一定先仿真/跑通再用，看不懂就问它"逐行解释这段代码"
3. **干了活要留痕**——agent 改完代码立刻 git commit（message 注明 prompt 要点）；解决了一个难题，收尾时让 agent 按模板写协作记录（见第四步第 ③ 篇）

> 💡 第一次体验：随便开个 agent，让它"写一个 4 位计数器并解释每一行"，感受完整流程。

### 入库门槛：先读懂，再 commit

**看不懂的代码不许入库**——不管它是 AI 写的还是队友写的。"能跑"不算过门，"讲得清"才算。

- 每次让 agent 提交代码前，它会先给你**逐段讲解** + **3 道理解测试题**，你答对了它才会 commit（按 [`skill/understand-gate/SKILL.md`](../skill/understand-gate/SKILL.md) 执行；用其他 agent 时手动走 [docs/code_review_checklist.md](code_review_checklist.md) 检查单）
- 读不懂的地方就是你的知识缺口清单，逐条问 agent 直到能讲出来——这个过程同时就是决赛 Verilog 上机考核的备考
- 讲解稿和测试题会全量存进 `report/llm_log/`，期末复盘和答辩演练直接用

---

## 第四步：阅读项目文档（约 1 小时）

`git pull` 下来之后，**按这个顺序**读：

| 顺序 | 文档 | 你要读懂什么 |
|:---|:---|:---|
| ① | `README.md`（仓库首页） | 我们要做什么作品、三个模块怎么配合、时间节点、分工 |
| ② | `docs/prep_checklist.md` | 开工前准备任务 |
| ③ | `report/llm_log/README.md` + `template.md` | 大模型协作记录的规矩：什么时候记、怎么记 |
| ④ | `report/llm_log/2026-09-04-project-kickoff.md` | 看一条真实记录长什么样 |
| ⑤ | `docs/resources.md` | 学习资源清单，后续学习要用 |

> ⚠️ 注意：src/、sim/、build/ 等目录现在大部分是**空壳占位**（只有说明 README），这是正常的——下周开工后往里填代码。

---

## 第五步：用 Issue 跟踪 bug 与卡点（M1 起执行）

> 一句话原则：**能用 commit 直接闭环的计划内任务不建 issue**（计划看 `src/riscv/plan.md`）；需要别人知道、需要跟踪状态的才建——bug、卡点、待办提问。

1. **建 issue**：仓库页 → Issues → New issue，选模板：
   - **Bug 报告**：仿真 / 上板 / 工具链问题，填现象、复现步骤、期望与实际结果、日志
   - **任务 / 待办**：需要跟踪的任务或提问，填验收标准、负责人、截止时间
2. **标签**（负责人建一次，共 5 个）：`bug` / `rtl` / `verify` / `docs` / `hardware`
3. **里程碑**：先只建 `M1`，M2 / M3 到对应阶段再建
4. **关闭规矩**：修复的 commit message 写 `fixes #12`（或 `closes #12`），推送后自动关闭；修复过程顺手记入 `report/llm_log/`
5. **与排期的边界**：M1 每天的计划任务看 `src/riscv/plan.md`，不为每天的排期重复建 issue

---

## 完成标准

当你能独立完成：`git pull` → 读懂 README → 用 agent 写个小模块 → 通过理解门槛（先讲清再 commit）→ commit & push → 按模板写一条协作记录，就算上手完成🎉
