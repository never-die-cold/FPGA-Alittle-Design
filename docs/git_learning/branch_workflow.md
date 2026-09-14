# 分支工作流（三线并行版）

> 2026-09-14 起，M1 主线改为**三线并行 + 每周 PR 合并**。本文是给 Git 新手的人话版操作手册；
> 单人基础四命令见 [docs/onboarding.md](../onboarding.md) 第一步，本文接着它讲"多人同时干活"。

## 为什么要分支

三条线同步开发，如果所有人都在 `main` 上直接改，改动会互相覆盖，谁也说不清哪行是谁的。
分支 = 每人一条独立的平行时间线，干完一周的活再统一合并（PR），由组长在合并时把关。

## 三条线

| 线 | 分支名 | 主责 | 只动这些目录 |
|:---|:---|:---|:---|
| RTL 线 | `dev/rtl` | 逻辑开发主力 | `src/riscv/` |
| 验证线 | `dev/verify` | 组长 | `sim/` |
| 基准线 | `dev/bench` | 文档与答辩 | `src/riscv_fw/`、`data/` |

> 跨目录改动（如改 README、plan.md、llm_log）先在群里说一句，避免撞车。

## 每周循环（照着敲）

### 第一次：把分支拉到本地（只做一次）

```bash
git fetch origin              # 同步远端分支列表
git checkout dev/rtl          # 切到自己的分支；验证线/基准线换成 dev/verify / dev/bench
```

### ① 每周开工前：同步 main 最新

```bash
git checkout dev/rtl          # 确认自己在自己分支上
git pull origin main          # 把 main 上一周合并的内容并进来
```

### ② 干活：小步 commit、随时 push

```bash
git add .                     # 或 git add 具体文件
git commit -m "feat: 转发单元三条旁路"
git push                      # 推到自己的远端分支，组长在 GitHub 上能看到进度
```

小步 commit 与理解门槛要求见 [docs/code_review_checklist.md](../code_review_checklist.md)：看不懂的代码不 commit，AI 生成的代码先过理解门槛。

### ③ 每周日：去 GitHub 发 PR

仓库页 → **Pull requests** → **New pull request** → base 选 `main`，compare 选自己的分支 → 按模板填写 → 提交。
（PR = Pull Request，直译"拉取请求"，就是"请组长把我的分支合并到 main"）

### ④ 组长合并后：同步最新 main

```bash
git checkout dev/rtl
git pull origin main
```

## 撞车了怎么办

- **push 被拒绝**：先 `git pull` 再 `git push`；出现冲突提示，截图发群，不要强行覆盖
- **提示文件冲突**：停手，群里说"我在 xxx 文件冲突了"，由组长决定谁来解决
- 红线：**任何人（含组长）不直接 push `main`**；`main` 只接受 PR 合并

## 卡点上报

任何一步卡住超过 30 分钟：群里发"我卡在 xxx 命令，报错是 xxx"，不要自己死磕。
