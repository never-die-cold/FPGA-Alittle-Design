# [2026-10-20] 协作记录：OpenCode 把 9 个本地 J04 提交 rebase 到最新 `origin/dev/riscv`

> 标签：#build #git #协作流程 #冲突解决
> 平台：OpenCode（Windows 主机 + WSL 仓库）｜ 模型：deepseek-flash
> 相关 commit：rebase 后 9 个提交（`dev/riscv`），随 PR #86 合入（`5f8abe2`）

## 1. 任务与初始提示词

用户 push 被拒（非快进），要求：「帮我同步并 rebase，不要新建分支；最后教我 push 到团队
`dev/riscv`；新代码和协作记录一起提交。」

## 2. 模型第一版方案

`git fetch origin` → `git rebase origin/dev/riscv`；冲突按“代码保留双方、文档取权威新版”处理；
完成后跑固件 TB 做冒烟，再让用户用 PAT 执行 `git push origin dev/riscv`，禁止 `--force`。

## 3. 失败现象

1. `git push` 返回 `! [rejected] dev/riscv -> dev/riscv (fetch first)`：origin 在 `401ee67`
   之后又合入仓库清理/文档分类 PR，推进到 `411d9ee`。
2. rebase 在 `f9128b3`（J04-21 文档对齐）冲突：`docs/contracts/coprocessor-handoff-v0.md`、
   `src/coprocessor/README.md`、`src/coprocessor/plan.md`（origin 已把文档迁入 `docs/contracts/`
   并更新状态措辞）。
3. rebase 在 `659a6e2`（J04-28）再次冲突：根 `plan.md` 与 `src/coprocessor/plan.md`；
   HEAD 侧新增了 10/15–10/17 证据与 M3 报备，不能整段丢弃。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | push 非快进拒绝 | 远端已前进，本地未同步 | `fetch` + `rebase` | 开始重放 9 个提交 |
| 2 | `f9128b3` 三处文档冲突 | rebase 中 `--ours` 指上游（origin） | 取 origin 侧，J04-21 旧措辞让位新版 | 继续 rebase |
| 3 | `659a6e2` 根 `plan.md` 冲突 | 两边各有新增，需并集 | 保留 origin 的 10/15–10/17 与 M3 两条 + 采用本地 J04 缺口条（链接改 `docs/archive/`） | 无冲突标记 |
| 4 | `src/coprocessor/plan.md` J04 行冲突 | 本地是 J04-28 收口 ✅，origin 仍 🟡 | 保留 ✅ 并写明“完整验证留队友” | 继续 rebase |
| 5 | 需要确认没动代码 | 本轮只改文档 | `git diff 6be0233 HEAD -- src sim/scripts` 列表无 `.v`/`.c` | RTL/固件内容一致 |
| 6 | 需要冒烟 | 用固件 TB 验证 | `run_coprocessor_iverilog.sh firmware` | C02 goldens + PASS/FAIL/RECHECK PASS |

## 5. 最终结论

9 个提交成功重放到 `origin/dev/riscv` 之上，工作树干净、`ahead 9`；随后用户 push，
PR #86 合入（`5f8abe2`）。`git grep '^<<<<<<< '` 仅命中
`data/logs/2026-10-19-worktree-inventory/preserved/` 的历史快照副本，不是活动冲突。
全程未使用 `--force`。

## 6. 经验沉淀

- 触发条件：rebase/`pull --rebase` 冲突落在“文档状态措辞”和“文档目录迁移”上。
- 排查步骤：先确认 rebase 语义（`--ours`=上游、`--theirs`=被重放提交），再判断哪边是权威
  最新；只有代码冲突才做并集，文档状态以最新版为准；完成后用 `git diff <旧HEAD> HEAD -- src`
  确认没有意外改代码。
- 适用范围：所有共享分支；push 被拒就 `fetch` + `rebase` 重来，禁止 `--force`。
#skill候选
