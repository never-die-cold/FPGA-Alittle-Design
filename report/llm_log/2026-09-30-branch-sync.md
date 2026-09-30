# 2026-09-30 协作记录：分支合并与同步

> 标签：#git #verify #docs
> 用户授权：各分支同步，未合并的合并；已授权 owner 合并 PR。

## 1. 开工现状与范围

- 主 worktree 在 dev/verify，HEAD 为 94db67c，工作区干净；远端 main 为 eed5ba8。
- dev/rtl 未合入 522e819：R2–R5 四个模块、两套模块 tb、回归入口与记录。
- dev/vision 远端未合入 0da736d，另有本地已提交的 58d8140：时序结论与评审材料。
- dev/bench、dev/verify 无独有未合并提交，只需快进同步。
- 视觉 worktree 有未提交 scaler RTL、三份文档和 retiming 日志；保留现场，不作为此次已提交分支的交付内容。
- 本次合并已有提交，不新增 RTL；文档/日志按古法编程与理解门槛的记录类豁免处理。

## 2. 合并与验证策略

- 先将 main 合入 RTL 分支，在真实合并结果上运行仓库内核回归。
- 视觉已提交内容不修改视觉 RTL；运行现有视觉回归，时序结论与评审建议仍不等于实机验收。
- 通过 PR 合入 main，使用 merge commit 保留历史，再快进同步各分支；不强推、不删除分支、不改保护规则。
- 视觉 worktree 的已跟踪改动和哈希先备份在本仓库 .git 内；同步时暂存并恢复现场，未跟踪日志保留。

## 3. 验证入口与证据

- 核：`bash sim/scripts/run_iverilog.sh all`，原始输出 `data/logs/2026-09-30-branch-sync/riscv-all.log`。
- 视觉：`bash sim/scripts/run_vision_iverilog.sh all`，原始输出 `data/logs/2026-09-30-branch-sync/vision-all.log`。
- 核回归退出码 0：15 个 tb 加 benchmark 额外一跑，共 16 条 PASS；CoreMark CPI=2.105、benchmark CPI=2.859，forwarding 25 例、hazard 16020 例均通过。
- 视觉回归退出码 0：10 个 tb PASS。视觉分支待合入提交未修改视觉 RTL，因此该 RTL 与最终已提交合并基线一致。
- 相对 origin/main 的待合入 RTL 差异 `git diff --check` 通过。合并预览从 main 带入的既有 Vivado 原始报告含尾随空格/末尾空行，保留原始报告，不混作本次新增格式缺陷。

## 4. 未实现 / 未验收

R2–R5 尚未接入完整三级核；v1 转发对照档、预测和整核性能未验收。HDMI 实机闭环、定位、正式模型、协处理器及 EXE 仍待实现/验收。视觉 worktree 的 retiming 修改仍属于未提交现场，不用其结果宣称本次主线已达标。
