# [2026-10-19] 协作记录：远端 `dev/riscv` 的 J04 审查与离板收口修复

> 标签：#coprocessor #审查 #收口 #时序
> 平台：DeepSeek Harness（Web，Windows/MSYS2）｜ 模型：deepseek-flash
> 相关 commit：`dev/riscv` @ `7d6355b` 之上的本地修复（见当日 git log）；总记录见 `2026-10-18-j04-closeout.md`

## 1. 任务与初始提示词

"你现在看一眼远端，riscv 线有新的提交，你审查一下，然后重新做一个计划"——先审别人推上来的
9 个提交，再据此重排收口计划；约束是**没有板卡、没有真实数据**，只做离板可交付部分，
未验证项诚实冻结。

## 2. 模型第一版方案

1. 拉 `dev/riscv`，重算交接单 §2 的 24 个文件 SHA256（24/24 匹配），核对锚点提交是否存在。
2. 按"状态是否虚高、锚点是否失效、入口是否可复现、契约是否被违反"四条审。
3. 发现的问题按"改文档 / 改 RTL / 改 TB / 改脚本"分类修，每类都要有仓库内 tb 复现。

## 3. 失败现象（真实偏差）

1. **状态虚高**：模块计划把 J04 标成 ✅，交接单自己却写着"未完整验证、未综合、未上板、不代签"。
2. **锚点失效**：交接单写 `9fdd035`，远端不存在（那是 rebase 前的本地哈希）。
3. **交接单成孤儿**：放在 `docs/` 根下，没有任何入口链接到它。
4. **Windows 不可复现**：runner 硬编码 `riscv64-unknown-elf-`，本机只有 `riscv32-`；
   `all` 首次退出 4（Icarus 13 报 `load_kind`/`loader_crc32` "declared after use"）。
5. **配置失效门禁缺失**：`CFG_SEQ` 变化后 `CFG_VALID` 不会撤销，旧配置仍能启动新任务。
6. **固件不设门禁**：`cop_job.c` 不轮询 `READY`、不校验 `RESULT_SEQ`、无轮询超时。
7. **连续两笔任务的 stale-done 竞态**（最隐蔽的一条）：引擎 `done` 保持到下一次 `start`
   才清零，而 `cop_task_ctrl` 在进入 `WAIT_ENGINE` 的第一拍就采样 `engine_done_i`，
   于是第二笔任务用上一笔的 `done` 瞬间"完成"并回写旧结果。最初表现为"给 PS 空闲 ABORT
   加 busy 门禁后 `bresp=10`"——门禁本身没错，是任务根本没在跑。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 交接单自述未验证、计划却是 ✅ | 状态虚高 | J04 拆 J04a ✅ / J04b 🟡，docs/contracts/README/overview 同步 | 文档一致 |
| 2 | `9fdd035` 在远端不存在 | rebase 前本地哈希 | 锚点改 `7d6355b`，日志里旧哈希标注为历史记录 | 文档一致 |
| 3 | 交接单无入口 | 孤儿文档 | `git mv` 到 `docs/runbooks/` 并挂 4 处导航 | 链接可达 |
| 4 | Windows `all` 退出 4 | 声明顺序违反 Verilog-2001 | `model_crc_error` 先声明后 `assign`；CROSS/Python 可覆盖加回退 | `all` / `cop_top` 退出 0 |
| 5 | `CFG_SEQ` 变化后旧配置仍可启动 | 缺撤销门禁 | `CFG_VALID=(APPLIED==SEQ && fields_valid)`，`CFG_COMMIT` 清 MODEL/ROI，ABORT 清 DONE/RESULT_VALID | 两个 TB 加撤销用例 PASS |
| 6 | 固件不校验就取结果 | 缺 READY/RESULT_SEQ/超时 | `cop_job.c` 加轮询门禁与稳定序列校验 | `firmware` PASS |
| 7 | busy 门禁使 `bresp=10` | **先怀疑门禁，回滚后发现任务确实没在跑** | 加"启动当拍不消费 done"，TB 加遗留 done 用例 + 第二次 START 后 20 拍仍 busy 断言 | 正向 PASS；去掉保护拍负向对照立即 FAIL（`busy=0 state=0 seq=2`） |

## 5. 最终结论

- 修复后：`run_coprocessor_iverilog.sh all` 退出 0、`cop_top`/`task_ctrl` 退出 0、
  `run_iverilog.sh soc` 退出 0；Windows 原始日志与退出码在
  `data/logs/2026-10-19-j04-closeout/`。
- 未完成：物理 bank/结果 DMA、真实 payload CRC、CDC/AXI 深测、`VERSION/CAPABILITY/ERROR_CODE`
  读回（OPEN-9）、PS 空闲 ABORT 口径（OPEN-10）、综合与板验。J04 仍为 J04a ✅ / J04b 🟡。

## 6. 经验沉淀

- **触发条件**：done / valid 这类"保持到下一次启动才清零"的握手信号，被下游在启动当拍采样。
- **排查步骤**：先确认"任务真的在跑吗"（看 busy/state/seq），再去怀疑门禁与仲裁；
  给门禁加一条"必须在跑"的前置断言，比读波形快。
- **通用修法**：发射当拍不消费对方的完成信号；或用"启动后一拍"的显式保护拍，并在 TB 里
  预置遗留电平做回归——**没有负向对照的修复等于没测**。
- **适用范围**：换成 AXI-Stream 的 `tlast`、DMA 的 `done`、中断的 `irq` 同样成立。
  #skill候选


## 7. 第二轮：独立审查（Codex desktop）与 R1–R5

同一天另一位 reviewer 对 PR #86 做了静态审查，提出 5 条 P2。逐条核实后**全部成立**，修复如下：

| 编号 | 问题 | 我的判断 | 处理 |
|:---|:---|:---|:---|
| R1 | 启动保护只挡遗留 `done`，没挡遗留 `error`：上一笔失败后 `engine.error` 保持，W1C 重试在第一拍被误杀 | 成立。这是 done 修复的对称缺口，我上一轮只想了 done | `WAIT_ENGINE` 的 error 分支同样加 `!engine_start_o`；TB 加“遗留 error 后重试”和“启动后真出错”两段；负向对照去掉保护即 `$fatal` |
| R2 | `count==0` 直接 RECHECK+CONFIG，与 C03 §8“有效空场景 → CHECK_FAIL”冲突 | 成立，但 v0 没有“本帧有效且零目标”的表达，硬实现等于臆造契约 | 记 OPEN-11，并在 `cop_job.c` 就地注释，避免下一个人“顺手修错” |
| R3 | `windows-rerun.sh` 吞掉被测命令的退出码 | 成立，是我写脚本时的疏忽 | `run()` 保存 rc 并累计 `failed`，末尾非零退出；从错误 cwd 跑实测退出 1 |
| R4 | `%.dis` 把 objdump 输出直接接给 tr，无 pipefail 时 objdump 失败会被掩成空文件 | 成立，我为修 CRLF 引入了新风险 | 改成写临时文件再 tr 再删；新增 `sim/scripts/test_firmware_rules.sh`（`OBJDUMP=false` 必须让 make 失败且不改写产物），并接进 `firmware` 入口 |
| R5 | 交接单“24 个文件匹配”实际是 23/24，Makefile 指纹漏更新 | 成立，我改完 Makefile 没有重算 | 重算 4 项（含 Makefile）并复核 24/24 |

reviewer 还指出两处**文档说过头**：OPEN-3 写成“CFG_SEQ 不等立即撤销 MODEL/ROI”（实际是 COMMIT 时才清，
`CFG_VALID` 才是立即为 0），OPEN-4 写成固件“以序号变化为提交点”（实际只比较读前读后相等）。
两处都按 RTL 实际行为改写了。这提醒我：**给未完成项写「已实现」比给完成项写「未完成」更容易出错**。
- 另一条工具链经验：Windows 下用 `pwsh` 包 `bash.exe` 且把 stderr 并到 stdout 时，
  PowerShell 会把 iverilog 的 `-Wall` 告警记成 `NativeCommandError`，让外层退出码变 1。
  **判据以脚本自身退出码为准**（把 `2>&1` 放进 bash 内部，或另写 `.exit_code` 文件）。 #skill候选
