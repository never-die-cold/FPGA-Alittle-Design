# [2026-09-23] 协作记录：通用固件 tb_core_coremark.v（CoreMark 跑分前置）

> 标签：#riscv #benchmark #工具链 #验证
> 平台：OpenCode ｜ 模型：deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本记录与 `sim/riscv/tb_core_coremark.v` 同批提交（哈希回填）

## 1. 任务与初始提示词

> 先仔细阅读项目库，然后完成：通用 tb_core_coremark.v（等 RTL 8B 改完 run_iverilog.sh 后再加 coremark 模式，避免同文件冲突）；7A/7B/8B 复跑

澄清后确定的边界与顺序（用户拍板）：

- RTL 8B（存储模型统一）由外部（RTL 线）完成；本轮只写通用 tb，不碰 `run_iverilog.sh`
- `coremark` 先只加单独模式，等 `coremark.hex` 入库后再议是否进 `all`
- 7A/7B/8B 复跑需加 arch-test；原始日志归档 `data/logs/`
- 分支流程：PR 全部合入 main 后，三条分支同步后再动代码
- 未提交的 3 个文档改动先提交（已随 PR #31 合并）

## 2. 模型第一版方案

- **新增 `sim/riscv/tb_core_coremark.v`**（124 行，非注释 99 行）：
  - 只依赖 `core_top` 外部接口（design_v0 §5.7）
  - 存储模型按 8A 冻结契约 8192×32、`addr[14:2]`（同步 IMEM / 异步 DMEM + 字节写）
  - 全参数化 plusargs：`+hex`（默认 `../src/riscv_fw/coremark.hex`）、`+exp_tohost`、`+exp_exit`（默认 0）、`+max_cycles`（看门狗）、`+timer_addr`（MMIO 读返回自由运行周期数，默认关）、`+vcd`（默认关）
  - 结束判据：监视写 `tohost_exit`(0x8000_3FF4) 事件；锁存 `tohost`(0x8000_3FF0)
  - 统计并打印 cycles / instrs / bubbles / CPI（CPI 用 64 位防溢出，`instrs` 按 `instr_valid && !stall` 计）
  - 缺 hex 文件、超时、期望不符均 `$fatal(1)`，保证 `run_iverilog.sh` 非零退出
- **分支收口**：PR #31（verify 归档 + AMD 仓库链接）、PR #32（RTL 7A/7B/8A）合并后，`dev/bench`、`dev/verify`、`dev/rtl` 全部 ff 同步至 main `340bcfd`

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **MSYS2 登录 shell 找不到 iverilog**：`bash -lc` 默认 PATH 不含 `/ucrt64/bin`，报 `iverilog: command not found`；显式 `export PATH=/ucrt64/bin:$PATH` 后恢复。
2. **`git add -N` 阻塞分支操作**：给新 tb 做 intent-to-add 后切分支/合并报 `Entry ... not uptodate. Cannot merge`（自动 stash 失败）；`git reset -- <file>` 退回未跟踪后正常。
3. **PR #31 与 #32 冲突（预判命中）**：两者都动 `src/riscv/plan.md`（归档重构 vs 32KB 表述修正）；`git merge-tree` 事先实测确认只有该文件冲突。
4. **未决项**：CoreMark 固件（`coremark.hex`）未移植，`coremark` 模式未接入 `run_iverilog.sh`（等 8B）；`tb_core_coremark.v` 的 `instr_valid/stall` 为 v0 两级核层次引用，Part B 重构后需同步。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `bash -lc` 报 iverilog not found | MSYS2 登录 shell PATH 无 ucrt64 | 命令前 `export PATH=/ucrt64/bin:$PATH` | ✅ 编译/仿真通过 |
| 2 | 切分支报 `Entry ... not uptodate` | intent-to-add 条目挡住 git 自动 stash | `git reset --sim/riscv/tb_core_coremark.v` | ✅ 正常切分支/合并 |
| 3 | PR #31 显示 plan.md 冲突 | 归档重构删除了 RTL 线改的那一行所在段 | `checkout --ours` 保留归档结构；同步修正 3 处过期描述（PR #32 已合、五档回归、勾选 PR） | ✅ push 后 PR #31 MERGEABLE |
| 4 | 正跑通过但 CPI=3.942 偏高 | 短程序 35 条指令含 3 条 32 拍 M 指令，属正常 | 无需改；作为教学点写入理解门槛 | ✅ 正/反例均符合预期 |

## 5. 最终结论

通用 tb 落地并自检通过：`PASS: coremark cycles=138 instrs=35 bubbles=4 cpi=3.942`（hello.hex, `+exp_tohost=142879`）；错值反例 FAIL、缺固件 FATAL，退出码分别正确。已提交至 `dev/bench` 并推送；`coremark` 模式待 8B 合入后再接入（避免同文件冲突）。状态：✅ tb 可复现；⬜ `coremark.hex`、coremark 模式、arch-test 复跑未完成。

## 6. 理解门槛（2026-09-23，用户答 + 判定）

**Q1：为什么结束判据必须盯"写 `tohost_exit` 事件"，不能等它的值变成非 0？**
答：tohost 是 MMIO 地址，要监测写操作捕获退出信号；等值会误判。
判定：✅ 通过（补正：本项目用 design_v0 §8 的 `tohost`/`tohost_exit` 双字约定，不是 riscv-tests 的 tohost bit0 协议；关键是成功退出写 0，与上电初值 0 无法区分）。

**Q2：`instr_count` 去掉 `!dut.stall` 后，32 拍的 `divu` 会被多计几拍？CPI 偏大还是偏小？**
答：多计 32 拍（约 31 次），CPI 偏小。
判定：✅ 通过。

**Q3：哪些写法依赖 8192×32 契约？为什么 coremark 模式要等 8B 之后加？**
答：存储器声明、地址解码等依赖契约；等 8B 改完 `run_iverilog.sh`。
判定：⚠️ 前半通过；后半理由不准——tb 手动 `vvp +plusarg` 现在就能跑，等 8B 是为避免同一文件分叉冲突。补 1 题。

**补 Q：现在就把 coremark 模式写进 `run_iverilog.sh` 会怎样？8B 不碰这个 tb 时它还能跑吗？**
答：8B 就算改了，我的 tb 还能跑（应是）。
判定：✅ 关键点正确（tb 只依赖 `core_top` 接口 + 契约，不依赖脚本模式）；再补一句冲突点：现在写脚本会与 8B 两边分叉，合并时需人工解冲突，所以等。

## 7. 经验沉淀

- 触发条件：给多拍功能单元/长跑程序写通用 tb；或与并行工作流共享仓库文件。
- 排查步骤：
  1. 结束判据用**写事件**而不是读值（成功值为 0 时与初值无法区分）；
  2. 长跑 tb 用 plusarg 参数化，固件不在库时可用现有 hex 冒烟，不阻塞落地；
  3. 与并行分支共享的脚本/文档，先 `git merge-tree` 预判冲突再决定动手顺序；
  4. `git add -N` 会阻塞分支操作，验证完即 `git reset` 解除。
- 适用范围：换固件、换核、换板卡均成立；「通用 tb + plusarg + 写事件判据」可作为后续 benchmark harness 的模板。 #skill候选
