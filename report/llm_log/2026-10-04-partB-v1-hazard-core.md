# [2026-10-04] 协作记录：Part B D2——v1 整核冒险边界验证（tb_core_v1_hazard，转发双档）

> 标签：#riscv #流水线 #验证 #架构决策
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：接续 `36498aa`（v1 双档转发入口）；本记录 + `sim/riscv/tb_core_v1_hazard.v` + `sim/scripts/run_iverilog.sh` 同批提交

## 1. 任务与初始提示词

继模块级转发/冒险 tb 与整核 v1 接入后，新增**整核冒险边界验证**，覆盖转发开关两档：

> 在整核 `core_top` 上验证：x0 不得产生伪 RAW；load-use→branch 先停 1 拍再裁决、停顿拍不得接受/redirect；redirect 恰好一次、恰好冲刷一个年轻槽；目的寄存器恰好写一次；错误路径 store 必须被抑制。同一 tb、同一程序、只切 `ENABLE_FORWARDING`。

（延续 `docs/three-day-plan.md` D2 与古法编程；验证只用仓库内 tb + `bash sim/scripts/run_iverilog.sh`。）

## 2. 模型第一版方案

- **新增 `sim/riscv/tb_core_v1_hazard.v`**：自建 8192 深 IMEM/DMEM 与 store 观测；`ENABLE_FORWARDING` 参数透传 `core_top`；程序含
  `addi x0,x0,7`（伪 RAW 探针）、`add x6,x5,x5`（双源 RAW）、`sw x6,0`、`lw x7,4`、`beq x7,x1`（load-use→branch）、错误路径 `sw x1,8`、目标 `sw x6,12`；
  断言 `branch_stalls==1`、`redirects/flush_checks==1`、`x6_writes==1`、`store0/8/12 = 1/0/1`、`dmem[0]=6 / dmem[2]=0 / dmem[3]=6`。
- **`run_iverilog.sh`**：新增 `v1_hazard_fwd` / `v1_hazard_nofwd`（同一 tb，`-Ptb_core_v1_hazard.ENABLE_FORWARDING=1/0`），并纳入 `all` 顺序执行。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 本轮整核边界 tb **一次通过**，无功能失败。
2. **未决**：Vivado OOC 仍未验证；正式 CPI 未测量（此前 D2.1 的 176→128 微基准周期差不能冒充最终 ≥25%）。
3. 并行跑两档会共写同一 `.vvp`（此前教训），本 tb 两档也要求**顺序**运行。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 伪 RAW（x0/未用端） | 需整核验证 `uses/x0` 门控真的生效 | tb 加 `addi x0,x0,7` 并断言 `data_stall==0` | ✅ 未误停 |
| 2 | load-use→branch | 必须先停 1 拍、停顿拍不得接受/redirect | 断言 `branch_stalls==1` 且停顿拍 `redirect/mem_in_valid=0` | ✅ 通过 |
| 3 | 错误路径 store 泄漏 | redirect 必须冲刷年轻槽 | 断言 `store8==0`、`dmem[2]==0` | ✅ 通过 |
| 4 | 单次写回 | 目的寄存器恰好写一次 | 断言 `x6_writes==1`、`dmem[0]==6` | ✅ 通过 |

## 5. 最终结论

新增整核冒险边界 tb 并**双档验证通过**：`PASS: v1 hazard mode=1 cycles=13`、`PASS: v1 hazard mode=0 cycles=15`；接入 `run_iverilog.sh` 的 `v1_hazard_fwd/nofwd` 并纳入 `all`。这补齐了“转发/冒险接入整核后”的边界证据（伪 RAW、load-use 停顿、redirect 单次冲刷、单次写回、错误路径 store 抑制）。**Vivado OOC 与正式 CPI 仍未测**。

## 6. 经验沉淀

- 触发条件：转发/冒险接入整核后，需要整核级边界验证（模块级 tb 不足以覆盖跨级交互）。
- 排查步骤：
  1. 伪 RAW 用 `x0`/未用寄存器在**整核**上断言 `data_stall==0`；
  2. load-use→branch 验证“先停顿再裁决”，停顿拍不得 `accept`/`redirect`；
  3. `redirect` 恰好一次、恰好冲刷一个年轻槽，错误路径 store 必须被抑制（`store8==0`）；
  4. 单次写回要计数（目的寄存器恰好写一次）；
  5. 转发开/关**同一 tb/程序**只切 `ENABLE_FORWARDING` 对拍；两档顺序运行，避免共写 `.vvp`。
- 适用范围：任何带转发/冒险的流水线整核边界验证；"x0 伪 RAW / load-use→branch / redirect 单次 / 错误路径抑制"可作通用检查清单。 #skill候选

## 7. 古法编程理解门槛（2026-10-05）

### 7.1 问题与用户答案

1. **为什么写 x0 不能使后继 x0 消费者被判 RAW，哪项检查负责抓错？**
   用户回答：x0 永远为 0，写 x0 等价于没有生产新值；RAW 必须包含
   `p_rd != x0`。若错误地产生假相关，后继指令会无谓停顿。整核测试用
   `addi x0,x0,7` 后接读取 x0 的 `addi x1,x0,5`，检查该拍不得出现
   `data_stall`。

2. **load→branch 停顿拍的四个边界信号是什么，为什么原始
   `branch_taken=1` 也不能跳？**
   用户回答：`front_stall=1`、`ex_accept=0`、`redirect=0`、
   `mem_in_valid=0`。load 结果尚未返回，比较使用的是旧值；redirect 必须经过
   `ex_accept` 门控，等下一拍取得正确数据后才能裁决。

3. **为什么既检查错路 store 为零次，又检查合法写回/store 恰好一次？**
   用户回答：前者证明“不该写的绝不能写”，后者证明“该写的恰好一次”。
   只看最终内存值会漏掉随后被覆盖的错路写、同值重复写，以及被其他写入掩盖的
   漏写，因此必须同时统计副作用次数。

### 7.2 判定

三题全部通过。用户已能从 `rd!=x0`、`ex_accept` 门控和副作用次数三个层面解释
整核冒险边界，D2.2a 理解门槛完成。Vivado OOC、正式 CPI 和 arch-test 仍属于
后续步骤，当前不得标记为已验证。
