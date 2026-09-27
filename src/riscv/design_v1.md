# v1 接口设计：RV32IM 三级流水核

> 状态：草案，Part B 契约编写中；完成全部章节并经用户确认后冻结。
> 依据：`plan.md` Part B/C、`design_v0.md` 与 2026-09-20 CPI 口径重定义。
> 权威范围：定稿后，本文件是 Part B/C 的流水、转发、冒险与模块接口唯一权威；
> v0 的冻结接口仍以 `design_v0.md` 为准。

---

## 1. 目标、边界与优先级

### 1.1 Part B 目标

- 将 v0 的两级 `IF / ID+EX+MEM+WB` 重构为三级 `IF / ID+EX / MEM+WB`；
- 加入可配置的数据转发与冒险处理，保持 RV32IM 指令语义不变；
- 用同一套固件、arch-test 和专项测试证明“优化不改语义”；
- 形成 `v1+转发` 与 `v1无转发` 两个可一键复现的同核对照档；
- 记录 CPI、Fmax、WNS 与资源，作为 Part C 分支预测的共同起点。

### 1.2 开发优先级

本阶段优先级固定为：

1. 三级流水与转发功能正确；
2. 转发覆盖完整，并产出可复现的 CPI 对比；
3. 提高主频。

125 MHz 是非阻塞加分项，不得因追频拖慢 M1 收口。若收尾时间盒结束时
仍未在 125 MHz 下取得 WNS≥0，则保留实际最高通过频率，并启用
“两级 + 完整转发”L3 预案。

### 1.3 本阶段不做

- 不在 Part B 引入 BHT；仍使用静态不跳预测和 taken 冲刷；
- 不改变 RV32IM 指令语义、异常模型或地址空间；
- 不改变 IMEM/DMEM 容量、时序语义和 `core_top` 对外存储器接口；
- 不把 PS DDR 引入纯 PL 核；
- 不把 125 MHz 板载时钟未经时序收敛直接接入当前核。

## 2. 版本基线与保留方式

| 对象 | 固定方式 | 用途 |
|:---|:---|:---|
| v0 两级基线 | commit `962a4f5`；契约定稿时创建 tag `partA-v0` | 功能、CPI、Fmax 参考锚点 |
| v1 无转发 | `core_top` 顶层参数关闭转发，hazard 对 RAW 执行停顿 | 主 CPI 对照档 |
| v1 + 转发 | 同一份 RTL、同一顶层参数打开转发 | Part B 主交付档 |

禁止复制并长期维护第二份 v0 `core_top`，也禁止手改 RTL 生成性能对照档。
两条 v1 运行命令必须在验证入口确定后写入本文件，并由仓库脚本一键复现。

`core_top` 文件名和现有外部端口保持不变；内部实现从 v0 演进为 v1。
SoC、IMEM、DMEM 与现有固件不因流水线重构改变接口。

## 3. 三级流水术语

| 级 | 名称 | 主要职责 |
|:---:|:---|:---|
| 1 | IF | 选择 PC，访问同步 IMEM，维护取指 valid/hold/flush 状态 |
| 2 | ID+EX | 译码、读 regfile、选择转发操作数、ALU、分支裁决、muldiv 控制 |
| 3 | MEM+WB | 数据访存、load 扩展、最终写回及 store 副作用提交 |

“EX→EX、MEM→EX、WB→EX”在本文表示结果的**逻辑来源类别**，不表示额外增加
三个独立流水级。三级合并结构允许多个逻辑来源共享物理总线和 mux；契约必须
分别给出来源有效条件、匹配条件和“最新生产者优先”的选择规则。

流水槽以显式 `valid` 为副作用依据；NOP 仅用于波形可读性。任何寄存器写、
内存写、跳转或 muldiv 启动都必须同时满足所属流水槽 `valid=1`。

## 4. 已冻结的总体原则

- 转发开关使用顶层 parameter（必要时由脚本映射 define），禁止手改源码；
- load-use 固定停顿 1 拍，不建立 DMEM→ALU 的零拍长组合旁路；
- 转发后的 rs1/rs2 同时服务 ALU、branch、JALR、store data 与 muldiv；
- decode 明确输出 `uses_rs1/uses_rs2`，避免伪 RAW；
- taken branch、JAL、JALR 固定冲刷 1 个年轻槽；not-taken 不产生气泡；
- M 指令在 ID+EX 等待，旧 MEM+WB 允许排空，结果经 MEM+WB 统一写回；
- regfile 不整体复位，x0 恒 0；流水 valid 复位阻止无效数据产生副作用；
- 核复位不清 DMEM，软复位后的程序结果允许依赖旧内存内容。

## 5. 三级拍序与流水边界

### 5.1 稳态拍序

同步 IMEM 的输出寄存器计入 IF 级，不在其后再串普通路径指令寄存器。
稳态下每拍最多取一条、执行一条、提交一条：

| 周期 | IF | ID+EX | MEM+WB |
|:---:|:---|:---|:---|
| k | 给出指令 N 的地址 | 执行 N-1 | 提交 N-2 |
| k+1 | 给出 N+1 的地址 | 执行 N | 提交 N-1 |
| k+2 | 给出 N+2 的地址 | 执行 N+1 | 提交 N |

正常指令从给出取指地址到提交跨两个边界，流水充满后吞吐率为每拍一条。 stall、flush 与多拍指令只改变槽位的 `valid` 和边界动作，不改变三级定义。

### 5.2 两个边界

```text
PC / 同步 IMEM
    │
    ├─ IF/ID：if_valid + if_pc + if_instr
    │
译码 / regfile / 转发 / ALU / 分支 / muldiv
    │
    ├─ ID+EX/MEM+WB：mem_valid + 执行结果 + 提交控制
    │
DMEM / load 扩展 / regfile 写回 / store 提交
```

`if_stage` 拥有 IF/ID 状态。正常推进时 `if_instr` 直接采用同步 IMEM 输出； 只有 hold 时才保存指令、PC 与 valid，避免正常路径额外增加一级寄存器。

`mem_wb_stage` 拥有 ID+EX/MEM+WB 边界寄存器。ID+EX 只在槽位被接受时 写入该边界；被暂停的消费者不能覆盖正在提交的旧槽。

## 6. 流水字段与裁剪规则

### 6.1 IF/ID 逻辑字段

| 字段 | 位宽 | 复位值 | 用途 |
|:---|:---:|:---:|:---|
| `if_valid` | 1 | 0 | 当前指令能否进入 ID+EX |
| `if_pc` | 32 | `0x8000_0000` | 分支目标、JAL/JALR 链接值和调试 |
| `if_instr` | 32 | NOP | decode 输入；正常路径来自 IMEM 输出 |
| `if_hold` | 1 | 0 | load-use 或 muldiv 等待时保持当前槽 |
| `if_flush` | 1 | 0 | redirect 后把错误顺序指令标为无效 |

`if_hold/if_flush` 是边界动作，不作为指令字段继续传入 MEM+WB。

### 6.2 ID+EX/MEM+WB 字段

| 字段 | 位宽 | 来源 | MEM+WB 用途 |
|:---|:---:|:---|:---|
| `mem_valid` | 1 | `if_valid && ex_accept` | 所有提交副作用总门控 |
| `mem_instr` | 32 | `if_instr` | retire 跟踪和波形调试 |
| `mem_pc` | 32 | `if_pc` | retire 跟踪；功能路径不再重算目标 |
| `mem_rd` | 5 | decode `rd` | regfile 写地址和转发匹配 |
| `mem_result` | 32 | ALU、PC+4 或 muldiv 结果 | 非 load 写回候选值 |
| `mem_addr` | 32 | ALU 地址结果 | DMEM 地址及 byte/half lane 选择 |
| `mem_store_data` | 32 | 转发后的 rs2 原值 | store 写数据生成 |
| `mem_reg_write` | 1 | decode | regfile 写使能候选 |
| `mem_mem_read` | 1 | decode | load 与 load-use 生产者标识 |
| `mem_mem_write` | 1 | decode | store 写使能候选 |
| `mem_wb_sel` | 2 | decode | result / load 的最终写回选择 |
| `mem_mask_sel` | 2 | decode | byte / half / word |
| `mem_sign_ext` | 1 | decode | load 符号或零扩展 |

`dmem_we = mem_valid && mem_mem_write`；regfile 写使能也必须包含 `mem_valid && mem_reg_write && mem_rd!=0`。控制位残留不能绕过 valid。

### 6.3 在 ID+EX 后裁剪的字段

| 字段 | 裁剪原因 |
|:---|:---|
| `rs1/rs2` 地址、`uses_rs1/uses_rs2` | hazard 与转发匹配已完成 |
| `imm`、`imm_type`、`alu_op` | ALU和目标地址计算已完成 |
| `alu_a_sel/alu_b_sel` | 操作数选择已完成 |
| `branch_type/jump_type` | redirect 已在 ID+EX 裁决 |
| `muldiv_op`、`muldiv_pending` | done 后只传最终结果 |

### 6.4 WB 提交记录

MEM+WB 另产生 `{wb_valid, wb_we, wb_rd, wb_data}` 一拍提交记录，供 WB→EX 逻辑来源和 CPI/retire 统计使用。它是旁路与观测记录，不构成第四级； 写回仍发生在 MEM+WB，记录本身不得再次触发 regfile 或 DMEM 写入。

## 7. 边界动作与复位

| 情况 | PC / IF/ID | ID+EX/MEM+WB |
|:---|:---|:---|
| 正常推进 | PC+4，接受下一条 | 捕获当前 ID+EX 槽 |
| load-use 停顿 | PC和IF/ID保持 | 写入 `mem_valid=0` 气泡；旧MEM+WB照常提交 |
| muldiv 等待 | PC和IF/ID保持 | 旧槽排空后持续写入无效槽；done 时捕获M结果 |
| redirect | PC取目标，杀死顺序IF槽 | 分支/跳转本身正常进入MEM+WB |
| 无效输入 | 可继续取指 | 捕获 `mem_valid=0`，所有payload均为无关项 |

低有效 `rst_n` 异步拉起时，必须清除 `if_valid`、`mem_valid`、WB提交 记录 valid 和 `muldiv_pending`。宽payload可清零以改善波形，也可保持无关值； 功能正确性只能依赖 valid，禁止依赖无效槽的数据恰好为0或NOP。

边界不允许“冻结旧MEM+WB并重复提交”。任何 stall 都必须让旧槽提交一次后排空；被暂停的是PC和当前消费者，而不是已经到达提交级的生产者。

## 8. 数据转发契约

### 8.1 来源记录与三级物理映射

`forwarding.v` 接收三类逻辑来源记录；记录只描述值从哪里变为可用，不增加流水级：

| 来源 | 记录 | `ready` 条件 | 当前三级中的含义 |
|:---|:---|:---|:---|
| EX→EX | `ex_valid/ex_we/ex_rd/ex_data/ex_ready` | 非 load 结果已完成 | 较老指令在 ID+EX 形成的 ALU、PC+4 或 M 结果 |
| MEM→EX | `mem_valid/mem_we/mem_rd/mem_data/mem_ready` | MEM 数据已最终确定 | load 扩展值等 MEM 端结果 |
| WB→EX | `wb_valid/wb_we/wb_rd/wb_data` | 本拍允许提交 | MEM+WB 的最终写回总线 |

合并实现可让多个逻辑记录映射到同一个 MEM+WB 物理槽，但不得因此复制提交动作。
若同一指令同时形成多个 ready 视图，各视图的数据必须一致。WB 记录仍是本拍组合
提交信息，不保存历史指令，也不构成第四级。

### 8.2 单个源操作数的匹配条件

对每个源操作数独立输入 `src_used`、`src_addr[4:0]` 和 `rf_data[31:0]`。
候选来源 `S` 的命中条件统一为：

```text
hit_S = src_used && S_valid && S_we && S_ready
        && (S_rd != 0) && (S_rd == src_addr)
```

WB 天然 ready，因此没有单独的 `wb_ready`。`src_used=0` 用来排除立即数指令等
伪 RAW；`src_addr=0` 必须固定返回 0，任何来源都不得向 x0 转发。

| 条件 | 选择 |
|:---|:---|
| `src_used=0` | RF；该端口不参与冒险 |
| `src_addr=0` | 常数 0 |
| `hit_EX=1` | EX 数据 |
| `hit_EX=0 && hit_MEM=1` | MEM 数据 |
| `hit_EX=0 && hit_MEM=0 && hit_WB=1` | WB 数据 |
| 三者均不命中 | RF 数据 |

### 8.3 mux 优先级与 load-use 例外

优先级固定为 `EX > MEM > WB > RF`。多个在途生产者写同一个 rd 时，消费者必须
取得程序顺序上最近的生产者；低优先级的旧值不得覆盖高优先级的新值。
`rs1` 与 `rs2` 使用相同规则但分别比较，允许一条指令两个操作数来自不同来源。

load-use 的 1 拍 interlock 优先于 mux 结果。立即相邻 load 尚处于 MEM+WB 时，
即使异步 DMEM 已形成 `mem_data`，消费者本拍也不得被接受；旧 load 提交、
插入一拍气泡后，消费者从已更新的 regfile 继续。禁止建立 DMEM→ALU 零拍路径。

### 8.4 转发值覆盖范围

转发先生成 `rs1_fwd` 与 `rs2_fwd`，再供以下使用者选择：

- ALU 的寄存器操作数；PC 或立即数选择不被转发覆盖；
- branch 比较器与 JALR 基址；
- store 原始 rs2 数据，之后才按 byte/half/word 复制到写总线；
- muldiv 的 `a/b` 启动操作数。

地址匹配只看真正读取的源：decode 必须输出 `uses_rs1/uses_rs2`。LUI、AUIPC、
JAL 等未使用端不得因指令位域恰好等于某个 rd 而停顿或转发。

### 8.5 同一 RTL 的开关与复现入口

`core_top` 顶层参数固定命名为 `ENABLE_FORWARDING`，默认 `1'b1`。

- 为 1：按本节真值表选择旁路，仅 load-use 和多拍/控制冒险停顿；
- 为 0：两个操作数强制来自 regfile，hazard 必须对所有真实 RAW 停顿到生产者提交；
- 两档仅允许脚本传参，禁止修改 RTL 源码生成对照档。

验证入口名称现在冻结，后续实现必须提供：

```bash
bash sim/scripts/run_iverilog.sh v1_fwd
bash sim/scripts/run_iverilog.sh v1_nofwd
```

脚本分别向同一 `core_top` 传入 `ENABLE_FORWARDING=1/0`；`all` 必须包含两档功能
回归。CPI 对比必须使用同一程序、同一三级核和同一计数起止条件。

### 8.6 转发专项验收点

- 单元级覆盖无命中、x0、`src_used=0`、三个单命中及多重命中优先级；
- 整核覆盖 ALU→ALU、ALU→branch、ALU→JALR、ALU→store、ALU→muldiv；
- 连续 R-type RAW 结果正确且零数据气泡；load-use 结果正确且恰好 1 拍气泡；
- 关闭转发后结果保持一致，并能观察到由 RAW interlock 增加的气泡。

转发网络不得从当前消费者的 ALU 输出组合反馈到自身输入；所有候选来源必须来自
较老指令的边界/提交记录，以避免组合环路。

## 9. 冒险、停顿与控制冲刷

### 9.1 RAW 比较基础

当前 ID+EX 消费者定义：`c_valid/c_rs1/c_rs2/c_uses_rs1/c_uses_rs2`；当前
MEM+WB 生产者定义：`p_valid/p_we/p_is_load/p_rd`。公共相关条件为：

```text
raw_rs1 = c_uses_rs1 && (c_rs1 == p_rd)
raw_rs2 = c_uses_rs2 && (c_rs2 == p_rd)
raw_dep = c_valid && p_valid && p_we && (p_rd != 0)
          && (raw_rs1 || raw_rs2)
```

`uses_rs*` 必须来自 decode 的指令语义，不能仅根据指令位域猜测。写 x0、无效槽、
不写寄存器的生产者均不构成 RAW。

### 9.2 转发开启与关闭时的停顿方程

| 模式 | `data_stall` | 含义 |
|:---|:---|:---|
| `ENABLE_FORWARDING=1` | `raw_dep && p_is_load` | 仅立即相邻 load-use 停 1 拍 |
| `ENABLE_FORWARDING=0` | `raw_dep` | 所有真实 RAW 等到生产者提交 |

转发开启时，非 load 生产者由 §8 的旁路解决；load 不走 DMEM→ALU 零拍旁路。
转发关闭时，不能因 ALU 结果已经算出就提前放行，消费者必须在 regfile 更新后重读。
store data、branch 比较、JALR 基址和 muldiv 操作数都属于 `uses_rs*` 覆盖范围。

### 9.3 一拍数据停顿的具体拍序

| 周期 | MEM+WB 生产者 P | ID+EX 消费者 C | PC / IF | 边界动作 |
|:---:|:---|:---|:---|:---|
| k | P 有效并在拍末提交 | `raw_dep=1`，本拍不接受 | 保持 C 与下一 PC | 向 MEM+WB 写 `valid=0` 气泡 |
| k+1 | P 已离开，regfile 已更新 | C 重读新值并接受 | 恢复推进 | 捕获 C 的结果与控制 |
| k+2 | C 在拍末提交 | 后续指令正常执行 | 正常推进 | 正常捕获 |

因此 load-use 恰好增加 1 个无效槽。若 k+1 仍有另一个未解决的生产者或 muldiv 等待，
可继续停顿，但每一拍都必须重新由真实条件判定，禁止用固定计数猜测。

停顿时绝不能保持 `p_valid=1` 让 P 重复提交。PC 和当前消费者保持，MEM+WB 在 P
提交后变成无效槽；这也保证 store 不会重复写 DMEM。

### 9.4 控制裁决与 redirect

branch、JAL、JALR 均在 ID+EX 裁决。控制转移只有在当前槽有效且能够被接受时成立：

```text
ex_accept = c_valid && !data_stall && !muldiv_wait
redirect  = ex_accept && (branch_taken || jump_taken)
```

branch 条件和 JALR 基址必须使用 §8 的转发值。若 branch 正因 RAW 停顿，
`ex_accept=0` 会抑制旧操作数算出的伪 redirect；数据就绪后再重新裁决。

| 周期 | ID+EX | IF 年轻槽 | PC | 结果 |
|:---:|:---|:---|:---|:---|
| k | B 裁决 taken 并正常前进 | 顺序指令 S 作废 | 拍末改为 target | B 不被冲刷 |
| k+1 | `valid=0` 气泡 | 取得 target 路径 | 正常推进 | 唯一控制气泡 |
| k+2 | target 指令执行 | 继续顺序取指 | 正常推进 | 恢复稳态 |

taken branch、JAL、JALR 固定冲刷 1 个年轻槽；not-taken branch 不冲刷、零控制气泡。
架构没有 delay slot，S 的寄存器写、DMEM 写和 muldiv 启动都必须被 `valid=0` 禁止。

### 9.5 边界控制优先级

每个时钟沿的控制优先级固定为：

1. `!rst_n`：清除所有流水 valid 和跨拍握手状态；
2. `redirect`：目标 PC 生效，杀死年轻顺序槽，当前控制指令正常进入 MEM+WB；
3. `front_stall`：保持 PC/IF 消费者，向下游注入无效槽；
4. normal：PC+4，两个边界正常推进。

`front_stall = data_stall || muldiv_wait`。由于 redirect 含 `ex_accept` 门控，合法设计中
`redirect` 与 `front_stall` 不会同时为 1；专项 tb 必须检查这一互斥条件。
flush 必须清 `valid`，NOP 只用于波形阅读，不能代替副作用门控。

### 9.6 hazard 专项验收点

- 转发开启：ALU RAW 不停，load-use 对 rs1、rs2 各恰好停 1 拍；
- 转发关闭：ALU/load 对所有真实 RAW 停到提交，伪 RAW 与 x0 不停；
- taken branch/JAL/JALR 各冲刷 1 个年轻槽，not-taken 不冲刷；
- branch 遇到 RAW 时先停顿再裁决，不得用旧值产生 redirect；
- stall 期间生产者只提交一次，气泡不得写 regfile、DMEM 或启动 muldiv。

## 10. RV32M 多拍流控

### 10.1 单元接口与状态归属

`muldiv.v` 的端口、3 位 `op` 编码和内部 32 次迭代保持 v0 §6.6 不变。
`op/a/b/start` 为输入，`result/busy/done` 为输出；单元只在 `start && !busy` 时锁存任务。

`muldiv_pending` 属于 `core_top` 的 ID+EX 流控状态，不放入 MEM+WB，也不由
`muldiv.v` 维护。它表示“当前被保持的 M 指令已经启动，尚未把完成结果送入下游”。
复位清零；接受 start 时置 1；done 结果被 MEM+WB 接受的时钟沿清零。

### 10.2 启动与等待方程

令 `m_valid = c_valid && muldiv_valid`，启动和等待定义为：

```text
muldiv_start  = m_valid && !data_stall
                && !muldiv_pending && !muldiv_busy
muldiv_wait   = m_valid && !muldiv_done
m_done_accept = m_valid && muldiv_pending && muldiv_done
```

`muldiv_start` 必须是单拍脉冲。`data_stall` 未解除时不得启动，否则会锁存旧的
rs1/rs2；真正启动时传入 §8 的 `rs1_fwd/rs2_fwd` 和当前 `muldiv_op`。

`muldiv_wait` 不依赖 busy 才拉高：start 后 busy 要到时钟沿才更新，因此从 M 指令
首次有效的启动拍就必须冻结前端。pending 在 done 拍仍为 1，防止 busy 已降为 0
时同一条 M 指令再次产生 start。

### 10.3 三级暂停范围

| 对象 | start/busy 等待期间的动作 |
|:---|:---|
| PC | 保持，不接受 PC+4 或 redirect |
| IF/ID | 保持同一条 M 指令、PC、rd 和控制字段 |
| ID+EX 组合逻辑 | 不反复产生副作用；只有首次 start 被接受 |
| muldiv | 独立迭代，不受前端 hold 干扰 |
| MEM+WB | 较老槽先提交一次，之后持续接收 `valid=0` 气泡 |

禁止冻结有效 MEM+WB 槽等待 muldiv，否则较老指令可能重复写 regfile 或 DMEM。
M 指令本身在 done 前不得进入 MEM+WB，等待期间也不得直接写 regfile。

### 10.4 start→busy→done→writeback 拍序

| 阶段 | M 指令 / muldiv | PC / IF | MEM+WB |
|:---|:---|:---|:---|
| start 拍 | 锁存 op 和转发后的 a/b，置 pending | 保持 M | 较老槽正常提交 |
| busy 拍 | 执行 32 次迭代，忽略新的 start | 持续保持 M | 写入无效槽 |
| done 拍 | `done=1`，`result` 有效；M 被 `ex_accept` 接受 | 拍末解除保持 | 捕获 M 的 rd/result，清 pending |
| 写回拍 | 下一条可在 ID+EX 执行 | 正常推进 | M 以 `mem_valid && mem_reg_write` 写回一次 |

done 拍不直接写 regfile。它只允许 M 指令携带 `muldiv_result` 进入 MEM+WB；统一
写回发生在下一拍 MEM+WB。这样 M 与 ALU/load 使用同一提交门控和 retire 口径。
`done` 下一拍必须回到 0，`result` 保持稳定，直到下一任务完成。

done 后紧随的消费者可从 M 的 MEM+WB 结果执行 EX→EX 转发，不再增加数据气泡。
关闭转发时，该消费者按 §9 的真实 RAW 规则再停到 M 提交。

### 10.5 与其他控制事件的关系

- M 指令若依赖当前 load，先由 `data_stall` 等待，解除后才发 start；
- M 等待期间 `muldiv_wait=1`，所以 `ex_accept=0`，不能产生 redirect 或普通提交；
- M 不是控制转移指令，合法译码下不会同时请求 redirect；
- 复位可随时取消任务：清 pending，并由 `muldiv.v` 清 busy/done 和内部状态；
- done 结果进入 MEM+WB 的拍优先于普通前端推进，但不得覆盖未提交的较老有效槽。

### 10.6 RV32M 结果与边界

八种操作的 `muldiv_op` 继续直接等于 `funct3`，结果语义完全沿用 v0：

- `mul/mulh/mulhsu/mulhu` 分别选择规定符号组合的低位或高位；
- `div/divu` 商向零截断，`rem/remu` 余数符号跟随被除数；
- 除数为 0：商为 `32'hFFFF_FFFF`，余数等于被除数；
- `32'h8000_0000 / 32'hFFFF_FFFF`：商为 `32'h8000_0000`，余数为 0。

v1 必须复用现有 `tb_muldiv` 证明单元未回归，并在整核 tb 检查：start 仅一次、等待期
无提交、done 结果进入正确 rd、紧随消费者开/关转发结果一致。

## 99. 契约编写状态

- [x] 三级拍序、流水寄存器字段及裁剪规则；
- [x] 转发真值表、mux 优先级与关闭转发模式；
- [x] load-use、flush、stall 的逐拍行为；
- [x] RV32M 多拍流控；
- [ ] 存储器与 regfile 三级语义；
- [ ] 新增模块端口和位宽；
- [ ] CPI、回归、Vivado 与板级验收；
- [ ] 待拍板决策、v0/plan 交叉引用及决策记录。

