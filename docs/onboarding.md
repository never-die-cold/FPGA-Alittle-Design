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

## 完成标准

当你能独立完成：`git pull` → 读懂 README → 用 agent 写个小模块 → commit & push → 按模板写一条协作记录，就算上手完成🎉
