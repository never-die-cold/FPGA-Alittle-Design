# DeepSeek Harness 工作结果独立审查（2026-10-19）

> 平台：Codex desktop；方式：静态审查、现有证据核对和文件指纹复算。
> 对象：[PR #86](https://github.com/never-die-cold/FPGA-Alittle-Design/pull/86)，head `faf7ca9196c14080b3c0fdf26645f214a0585b24`。
> 主要范围：`7d6355b..faf7ca9` 的 9 个 DeepSeek 提交；按需回看依赖实现，不代表完整复审 PR 全部 18 个提交。
> 来源：`session-665b4004-cb22-4a11-8297-27a66adf70ee`，turn 3 已记录 completed。

## 1. 任务、约束与结论

用户要求审查 DeepSeek 已完成的结果并出报告，明确限制重跑仿真和验证的时间成本。
本次没有修改 RTL、固件、既有测试或计划，没有 commit、push、merge，也没有发布 GitHub 评论。
**建议先处理以下 5 项 P2 问题，再合入；J04a 冒烟成果可以保留，J04b 不能据此验收。**
静态发现没有新增反例 TB 的仿真确认；下文给出确定的代码路径和契约依据，不能将其称为板端实测。

## 2. 审查发现

### R1 · P2：启动保护只屏蔽旧 done，旧 error 仍能误杀重试任务

位置：[`cop_task_ctrl.v:46`](../../src/coprocessor/cop_task_ctrl.v#L46)，关联 `cnn_sequencer.v:103–106`。
超时或算子错误后，sequencer 的 `error` 保持为 1，直到下一次 START 或 reset/abort 才清零。
软件 W1C 清终止状态后重试：LAUNCH 发出寄存的 `engine_start_o=1`；下一拍进入 WAIT_ENGINE，
任务控制器仍读到旧 `engine_error_i=1`，将新任务终止；同一拍 sequencer 才采到 START 并清错启动。
结果是任务层已空闲报错，引擎却刚开始运行。新增保护只用于 done 分支，没有覆盖这个对称情况。
这是依赖路径已有的恢复缺口，本轮 done 修复尚未覆盖；先 SOFT_RESET 可避开，但契约没有要求每次 W1C 重试都先 reset。
`tb_cop_task_ctrl.v:10` 把 error/timeout 绑为 0，现有单元 PASS 不能证明该路径。
建议：启动采样保护同时覆盖遗留 error，并补“上一笔失败→W1C→重试”的短用例。

### R2 · P2：有效空场景的工单判定路径仍未实现

位置：[`cop_job.c:59`](../../src/riscv_fw/cop_job.c#L59)。
当前 `count==0` 直接发布 `RECHECK + CONFIG`；C03 §8 第 234 行要求有效空场景对非零工单为
`CHECK_FAIL`，actual 三类均为 0。规则函数 `cop_judge(...,0,order)` 能表达该结果，固件却提前绕过。
同时配置寄存器只接受 1–16 个 ROI，因此需明确有效空场景的旁路/任务有效性传递，不能简单把未配置的 0 当作有效帧。
建议：冻结并实现“确认有效空帧→跳过 CNN→零计数 CHECK_FAIL”分支，与未配置、无视频分开。
现有 firmware 入口只构建 ELF 并测试 `cop_work_order.h`，没有运行 `cop_job.c` 的 MMIO 流程。

### R3 · P2：证据一键重跑脚本吞掉被测命令的失败退出码

位置：[`windows-rerun.sh:10`](../../data/logs/2026-10-19-j04-closeout/windows-rerun.sh#L10)。
`run()` 在被测命令后把 `$?` 写入文件，最后执行成功的 printf；函数返回该 printf 的 0。
脚本仅 `set -u`，没有累计失败或最终非零退出，因此即使某项失败，整个一键入口仍可能返回 0。
这不推翻现有逐项 `.exit_code=0` 的记录，但会使以后只判断入口退出码的调用方误报通过。
建议：保存被测退出码、继续留存日志，并在任一项失败时让总入口非零退出。

### R4 · P2：反汇编的换行修复引入工具失败被管道掩盖的问题

位置：[`Makefile:74`](../../src/riscv_fw/Makefile#L74)。
规则由单独执行 objdump 改为 `objdump ... | tr ... > $@`；当前 Makefile 未启用 pipefail。
当 objdump 不存在或无法解析 ELF，而 tr 正常结束时，make 会把空的 `.dis` 当作成功产物。
建议：显式传播 objdump 失败，再规范换行；失败产物不能被当作可用证据。

### R5 · P2：交接单的“24 个文件匹配”在当前 head 不成立

位置：[`coprocessor-j04-handoff.md:49`](../../docs/runbooks/coprocessor-j04-handoff.md#L49)。
实际复算为 **23/24 匹配**。Makefile 记录 `0e7708050fb5d5b1651594314c31311dbb5824eeb1bf277c97db6ed5b92dd042`，
实际为 `665656d9a753b333fc978b22276f83bcf23d81cd11ef2d779cd1f7191d3f1498`。
建议：更新该项指纹并复核状态说明；不要再次笼统引用“24/24 一致”。hex/dis 的 SHA256 本轮匹配。

## 3. 已有成果与证据边界

- done 保护拍与实际引擎握手时序相符；集成 TB 有第二次 START 后仍 busy 的断言。
- CFG_SEQ 改变后撤销 CFG_VALID、ABORT 清旧 DONE/RESULT_VALID、LF 固定和 Windows 入口适配有实际改动。
- 原证据共 7 份现存退出码文件（Linux 2 份、Windows 5 份）均为 0；相应日志有 PASS。
- CoreMark/v1 变体未重跑，原作者明确保留 partial 记录；本次也不将其改称完整核回归。
- firmware PASS 仅证明构建/规则函数；不证明 READY、序号、超时及结果窗口的固件行为。
- OPEN-3 声称 CFG_SEQ 不等即撤销 MODEL/ROI；RTL 和 TB 实际保留到 COMMIT，应修正文档。
- OPEN-4 声称固件“稳定两次且以序号变化为提交点”；实际仅读结果前后比较相等，未校验相对 START 前序号变化。

## 4. 本轮轻量核查与原始结果

原始记录及命令见 [核查目录 README](../../data/logs/2026-10-19-deepseek-independent-review/README.md)。
文件指纹：`FILES=24 MISMATCHES=1`；`git diff --check 7d6355b..HEAD`：退出 0、无输出。
仅尝试 task_ctrl/config_regs 两个短用例；MSYS2 bash 启动失败 `0xC0000022`，退出 `-1073741502`；
随后原生 Icarus 在首个 TB 编译阶段退出 `-1073741819`，未进入仿真。未获得本轮独立仿真 PASS。
两次尝试记录约 0.375 s / 8.929 s；不继续排查工具环境，不跑整网、CoreMark、视觉全量或 Vivado。

## 5. 待办与未实现清单

先补 R1/R2 的短反例、修 R3/R4 的退出码，再更新 R5 指纹；本报告不实施修复。
待办表 B05（CDC/AXI TB）和 B06（综合/实现）被归为“需要板卡”不准确，可离板推进；本轮不执行这些长检查。
物理 bank/结果 DMA、有效空场景固件路径、完整返回 CDC、正式模型、SoC/视频集成及板验仍未实现或未验收。
理解门槛未执行：本次只写审查与证据文档，没有代码提交；未替用户确认代码理解。
