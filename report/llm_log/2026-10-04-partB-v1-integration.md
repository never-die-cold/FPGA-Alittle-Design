# [2026-10-04] 协作记录：Part B D1.3——v1 三级流水接入 core_top（ID+EX/转发/冒险联调）

> 标签：#riscv #流水线 #架构决策 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本地 `5499c2d`（ID+EX Verilog-2001 可综）、`81293aa`（回归归档）、`cae4755`（v1 red-light flow）、`e6f5d93`（v1 commit/hazard 路径接入）；本文档与 core_top 剩余的 D1.3b ID+EX 替换同批提交

## 1. 任务与初始提示词

按 `docs/three-day-plan.md` 的 D1/D2/D3 顺序推进 Part B，本轮为 **D1.3b**：把 v1 三级流水真正接进 `core_top`：

> 改 `core_top.v` 先接 regfile→forwarding→`id_ex_stage` 数据面，再接 `hazard` 的 `front_stall/ex_accept/redirect/mem_in_valid` 控制面；对外存储器端口保持不变。单步 ≤100 行、先设计后写码，每步 2–3 道理解题记入文档待答区。验证只用仓库内 tb + `bash sim/scripts/run_iverilog.sh all`，禁止 `/tmp`。

授权范围：可改 `src/riscv/`、`sim/riscv/`、`sim/scripts/`、`data/logs/`、`report/llm_log/`、`docs/`、根 `AGENTS.md`；**禁止直推 main、禁止强推、禁止新建/保留分支**，交付目标为 `dev/rtl`。

## 2. 模型第一版方案

- **ID+EX 可综合性修复（5499c2d）**：`id_ex_stage.v` 去掉隐式端口/`.*`，改为 Verilog-2001 显式端口与显式位宽；同步修 `tb_id_ex_stage.v`，新增 `sim/scripts/synth_id_ex_ooc.tcl` 做 OOC 综合探测；`grep -rn "(\.\*)" src/` 保持无匹配。
- **v1 red-light flow（cae4755）**：新增 `sim/riscv/tb_core_v1_flow.v`（v1 流水冒烟/红灯流程），接入 `run_iverilog.sh`。
- **v1 接入 core_top（e6f5d93 + 本轮未提交部分）**：`core_top` 顶层参数 `ENABLE_FORWARDING`；数据面改为 regfile→`forwarding`→`id_ex_stage`（例化替换原先内联的 decode/ALU/分支裁决）；控制面用 `hazard` 产生 `data_stall/front_stall/ex_accept/redirect/if_flush/mem_in_valid`；`pc_target = redirect_target`；MEM+WB 边界与 `muldiv_pending` 保留；对外存储器端口（`imem_*`/`dmem_*`）不变。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. **ID+EX 缺可综合性**：早期 `id_ex_stage.v` 使用隐式网络/`.*`，`iverilog -g2001` 报隐式端口问题；5499c2d 改为显式端口后零 error（Vivado OOC 仍未验证）。
2. **本地 `dev/rtl` 与 `origin/dev/rtl` 分叉**：修复曾提交到临时分支 `codex/fix-implicit-ports`（283aaa2）；用户决定**本轮改为本地继续、暂不推送**，并要求推送前必须先 `git pull --rebase origin dev/rtl`，**禁止强推**。
3. **CoreMark 长回归**：约 2100 万周期、跑数分钟，需等 golden 判据，不能中断。
4. **Vivado OOC 仍未验证**：`synth_id_ex_ooc.tcl` 只是探测脚本，未实际综合，不得声称已综合/时序已过。
5. **D1.3b 理解题待答**：为何组合 `id_ex_stage` 不加第四级 / 为何 `branch_taken/jump_taken` 仍须经 `ex_accept` / 为何 store data 要用转发后的 rs2 并捕获进 MEM+WB。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `iverilog -g2001` 隐式端口告警 | `id_ex_stage` 用了隐式网络/`.*` | 改显式 Verilog-2001 端口与位宽 | ✅ `grep "(.*)" src/` 无匹配；编译零 error |
| 2 | 临时分支工作未落主分支 | 需并回 `dev/rtl` 且不保留分支 | 本地 dev/rtl 继续，回写 `three-day-plan` 待办：推送前先 rebase | ✅ 本地 4 笔提交，未强推 |
| 3 | v1 是否真接入（性能是否变） | 未接入时 CPI 不变；接入后应改变 | core_top 例化 `id_ex_stage`/`forwarding`/`hazard` | ✅ CoreMark CPI 由 2.105 → **2.169**（已改变，证明接入生效） |
| 4 | 控制面互斥 | `redirect` 必须经 `ex_accept` 门控 | hazard 输出 `ex_accept` 门控 redirect | ✅ 回归/hazard 互斥断言 PASS |

## 5. 最终结论

v1 三级流水已接入 `core_top`（D1.3a/b 实现并验证）：`regfile→forwarding→id_ex_stage` 数据面 + `hazard` 控制面，`ENABLE_FORWARDING` 参数保留对照档，对外存储器端口不变。全量回归 `exit_code=0`：**CoreMark `cycles=21926510 instrs=10106387 bubbles=1243810 CPI=2.169`（golden 匹配）、bench_v0_1 `CPI=2.859`、SoC/soc_check PASS、视觉回归 PASS**（`tb_vision_*` 全部 PASS）。本地 `dev/rtl` 相对 `origin/dev/rtl` **ahead 4 且已分叉**：推送前必须先 `git pull --rebase origin dev/rtl`，严禁强推；Vivado OOC 未跑，D1.3b 理解题待答。

## 6. 经验沉淀

- 触发条件：把三级流水从“孤立模块”接进顶层核，并要保持对外接口不变。
- 排查步骤：
  1. 数据面/控制面分开接：`forwarding` 在 `id_ex_stage` 之前，`hazard` 统一产生停顿/接受/重定向；
  2. 组合级 `id_ex_stage` 不引入第四级，提交只发生在 MEM+WB 边界；
  3. 一切跳转/分支必须经 `ex_accept` 门控，陈旧分支不得 redirect；
  4. 可综合性从第一天抓：Verilog-2001 显式端口、杜绝隐式网络/`.*`；
  5. 性能数据只有在**真正接入顶层后才可信**（接入前 CPI 不变属正常，不能冒充提速）；
  6. 分叉的本地分支推送前必须 `rebase`，绝不强推。
- 适用范围：任何“先写积木、后接顶层”的流水线重构；"数据面/控制面分离 + 显式端口 + rebase 不强推"可复用。 #skill候选

## 7. D1.2b 访存宽度专项与理解门槛

新增 `tb_core_v1_mem.v`，以整核程序覆盖 `sb` offset 0/3、`sh` offset 0/2、`sw`，以及
`lb/lbu/lh/lhu/lw` 的车道选择和符号/零扩展；复位期要求零写入，程序全程要求恰好 11 次写入。
定向结果为 `PASS: v1 byte/half/word memory path, writes=11`；全量回归退出码 0，原始日志见
`data/logs/2026-10-04-partB-v1/d1-2b-v1-mem.log` 与 `d1-2b-all.log`。

1. **题目**：`0x11223344` 经 offset 0/3 两次 `sb 0x5a` 后为何是 `0x5a22335a`？
   - **首答**：认为第二次写打开“第一次写入值之后的 `dmem_be`”。
   - **补讲**：`dmem_be` 是本次操作的车道使能，不属于数据；offset 0/3 分别为 `0001/1000`。
   - **补测答案**：`0xAABBCCDD` 在 offset 2 写 `0x66` 得 `0xAA66CCDD`；补充确认 `be=0100`。
   - **判定**：通过。
2. **题目**：同一原始字节为什么 `lb 0x80=0xFFFFFF80`、`lbu 0x80=0x00000080`？
   - **答案**：`lb` 复制 bit7 到高 24 位做符号扩展，`lbu` 高 24 位补零。
   - **判定**：通过。
3. **题目**：为什么同时检查复位期零写和全程恰好 11 次写？10/12 次分别意味着什么？
   - **答案**：复位/气泡不能误写；11 表示不多不少；10 表示 store 漏提交，12 表示气泡、停顿或旧
     MEM+WB 指令重复提交。
   - **判定**：通过。

D1.2b 理解门槛全部通过；本步未修改 RTL，未执行 Vivado OOC，未 push。

## 8. D1.4a RV32M 启动与等待流控理解门槛

新增 `tb_core_v1_muldiv_flow.v`，用 `addi x1`、`addi x2`、`mul x3,x1,x2` 和年轻
`addi x4` 逐拍检查：start 当拍立即停顿、start 单拍、busy 32 拍、done 单拍、PC 保持、
MEM+WB 排空气泡，以及较老 x2 恰好提交一次。定向和全量回归均通过；本步无需修改 RTL。

1. **题目**：为什么不能等 `busy=1` 才停前端？
   - **答案**：busy 是寄存器输出，start 后下一个时钟沿才拉高；若等待 busy，启动拍 PC 已前进，
     M 指令可能被下一条覆盖。必须从 start 拍组合地冻结 PC 和当前 M 指令。
   - **判定**：通过。
2. **题目**：为什么等待期 `mem_valid=0`，但较老 x2 要提交一次？冻结 MEM+WB 会怎样？
   - **答案**：只冻前端并向下游送气泡；旧 MEM+WB 正常提交一次后排空，冻结会让它重复提交。
   - **判定**：通过。
3. **题目**：done 被接受前为什么 pending 必须保持为 1？
   - **首答**：防止指令在到达 MEM+WB 前重复使用。
   - **补讲**：busy 已降为 0而 M 仍在 ID+EX 时，提前清 pending 会让启动条件再次成立。
   - **补测答案**：done 拍 pending 应为 1，在结果被 MEM+WB 接受的该拍时钟沿清零。
   - **判定**：通过。

D1.4a 理解门槛全部通过；Vivado OOC 未验证，未 push。

## 9. D1.4b RV32M 统一写回与后继转发理解门槛

扩展 `tb_core_v1_muldiv_flow.v`，将年轻指令改为 `addi x4,x3,1`，检查 done 拍不直接
写 x3、MEM+WB 下一拍以 21 写 x3、后继通过旁路算得并写回 x4=22，二者各写一次且
`data_stall=0`。定向、RV32IM 和全量回归均通过；本步无需修改 RTL。

1. **题目**：为什么 done 拍只能捕获结果，不能直接写 x3？
   - **答案**：每条指令只能从 MEM+WB 唯一提交一次；done 与 MEM+WB 都写会产生双写、竞争，
     延迟的第二次写还可能用旧结果覆盖下一条指令的新值。
   - **判定**：通过。
2. **题目**：`addi x4,x3,1` 从哪里取得 21，为什么不需停顿？
   - **答案**：直接从 MEM+WB 取得结果，经 forwarding 送到 `rs1_fwd`，不必等待寄存器堆写后再读。
   - **判定**：通过。
3. **题目**：为什么既检查终值，也检查 x3/x4 各写一次？
   - **答案**：先写错再写对会让最终值看似正确；计数 1/2/0 分别区分正常、重复写和漏写。
   - **判定**：通过。

D1.4b 理解门槛全部通过；Part B D1 功能集成小步完成，Vivado OOC 未验证，未 push。
