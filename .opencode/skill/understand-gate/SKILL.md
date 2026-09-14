---
name: understand-gate
description: Use BEFORE any git commit of code generated or modified by the AI agent in this session. Trigger whenever the user asks to commit, 提交, 合入, or push changes. The gate forces the user to demonstrate understanding of the AI-written code (segmented walkthrough + 3 comprehension questions) before committing. Do not use for documentation-only commits, .gitignore, or llm_log/metrics file additions.
---

# Understand Gate（理解门槛）

本仓库铁律：**看不懂的代码不许入库**。团队全部成员为 Verilog 初学者，
AI 生成的代码若不经过"人理解"环节，会在答辩、决赛上机、debug 时全部反噬。
你的职责是在 commit 前强制执行理解验证流程，**未经用户确认理解，禁止执行 git commit**。

## 流程

当用户要求 commit/提交/合入本会话中 AI 生成或修改的代码时，按顺序执行：

### 第 1 步：逐段讲解（不落盘的部分）

对本此待提交的改动生成逐段讲解：

- 按 always 块 / 模块 / 函数分组，讲**设计意图**（为什么这样写），不是逐行复述语法
- 重点标注：每个寄存器为什么存在、时序/组合逻辑边界、握手或流水线语义、与 `design_v0.md` 等设计文档的对应章节
- 初学者视角：术语首次出现时给一句人话解释（如 stall=流水线暂停一拍）

### 第 2 步：3 道理解测试题

面向从零水平出题，题目必须针对本次提交的具体代码，例如：

- "信号 X 为什么打一拍？不寄存直接用会怎样？"
- "如果去掉这段里的 stall/flush/某个分支，仿真里会出现什么现象？"
- "把 XX 改成 YY，这条流水线的哪一拍会出错？"

### 第 3 步：等待用户回答（硬性卡点）

- 明确要求用户先回答 3 道题，**用户确认理解前不得执行 git commit**
- 用户答错或答不上 → 针对缺口再讲解，然后补 1 道新题再测，直到通过
- 禁止：替用户作答、降低题目难度糊弄、跳过本流程直接 commit
- 例外：纯文档/.gitignore/llm_log 记录类 commit 无需走本流程

### 第 4 步：全量落盘 llm_log

用户通过测试后，将以下内容**全量**写入 `report/llm_log/`（用户要求保留全量记录用于期末复盘）：

1. 逐段讲解稿（完整保存）
2. 理解测试题 + 用户答案 + 你的判定（通过/补课后的再测记录）

- 当日已有 llm_log 记录文件 → 追加"理解门槛"章节
- 没有 → 新建 `YYYY-MM-DD-<英文主题>.md`，按 `report/llm_log/template.md` 结构，理解门槛内容放"经验沉淀"之前
- 文件名规范：日期 + 英文主题，小写连字符（见 `report/llm_log/README.md`）

### 第 5 步：正常提交

- commit message 遵守仓库现有规范：说明做了什么；AI 生成的代码注明 prompt 要点
- 用户曾用其他 agent（Kimi Work 等）生成的代码要求 commit → 按本 skill 完整流程走一遍（代码不在本会话生成不影响理解验证的必要性）
