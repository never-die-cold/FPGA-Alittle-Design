# v1 接口设计：RV32IM 三级流水核

> 状态：📌 接口契约已冻结（2026-09-28）；阶段 2 RTL 必须遵守本文，偏差须先回写决策。
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
| v0 两级基线 | commit `962a4f5`，tag `partA-v0` | 功能、CPI、Fmax 参考锚点 |
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

`muldiv.v` 的端口和 3 位 `op` 编码保持 v0 §6.6 不变。乘法采用 Radix-4，
每拍处理 2 位、固定迭代 16 次；除法仍采用 Radix-2，固定迭代 32 次。
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
| busy 拍 | 乘法迭代 16 次、除法迭代 32 次，忽略新的 start | 持续保持 M | 写入无效槽 |
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

## 11. 存储器与寄存器堆时序

### 11.1 对外接口与容量保持不变

v1 保持 v0 §3 的哈佛接口、地址空间和容量，不修改 `imem.v/dmem.v` 端口：

| 对象 | 容量/索引 | 读时序 | 写时序 |
|:---|:---|:---|:---|
| IMEM | 8192×32，`addr[14:2]` | 同步读，地址后下一拍数据有效 | 固件预载，无运行时写口 |
| DMEM | 8192×32，`addr[14:2]` | 异步读，同拍数据有效 | 上升沿按 `we` 与 `be[3:0]` 字节写 |

地址范围继续为 `0x8000_0000–0x8000_7FFF`；`tohost=0x8000_3FF0`、
`tohost_exit=0x8000_3FF4` 不变。不增加缓存、总线等待或非对齐异常。

同步 IMEM 的输出寄存器属于 IF。hold 时保持当前 IF/ID 槽，redirect 时将顺序输出
标成 `valid=0`；正常路径不得再增加指令寄存器。

### 11.2 load 的 MEM+WB 动作

load 在 ID+EX 计算有效地址，并把地址、mask、符号扩展和 rd 写入 MEM+WB。
下一拍由 `mem_addr` 驱动异步 DMEM，按 `mem_addr[1:0]` 选择 byte/half lane：

```text
load_data = extend(dmem_rdata lane, mem_mask_sel, mem_sign_ext)
wb_data   = mem_mem_read ? load_data : mem_result
rf_we     = mem_valid && mem_reg_write && (mem_rd != 0)
```

`load_data` 与写回选择在 MEM+WB 同拍组合完成，拍末写 regfile。非相关后续指令
无需等待；立即 load-use 按 §9 固定停 1 拍，禁止把该组合读路径继续串入消费者 ALU。

### 11.3 store 的 MEM+WB 动作

store 在 ID+EX 计算地址，并把转发后的原始 rs2 数据捕获为 `mem_store_data`。
MEM+WB 根据地址低位生成 byte enable，并在写入前复制低字节或低半字：

```text
dmem_wdata = byte ? {4{mem_store_data[7:0]}}
           : half ? {2{mem_store_data[15:0]}}
           : mem_store_data
dmem_we    = mem_valid && mem_mem_write
dmem_be    = dmem_we ? lane_mask(mem_mask_sel, mem_addr[1:0]) : 4'b0000
```

store 只在 MEM+WB 的一个上升沿产生副作用。stall 不得冻结有效 store 槽；气泡、
flush 和复位后的无效槽即使 payload 残留，也因 `mem_valid=0` 不能写内存。

ALU→store 的 rs2 可直接转发后捕获；load→store 仍属于 load-use，固定停 1 拍。
地址基址 rs1 与 store data rs2 分别进行 uses、hazard 和 forwarding 判断。

### 11.4 regfile 读写与同沿可见性

`regfile.v` 继续为 32×32、双组合读、单上升沿写，模块不增加复位端口：

- `raddr1/raddr2==0` 时组合返回 0；
- 只有 `rf_we && mem_rd!=0` 才写，任何指令都不能改变 x0；
- MEM+WB 在上升沿写入后，组合读端在该沿后的同一周期看到新值；
- load-use/关闭转发 RAW 停顿正是利用下一周期重读已更新 regfile。

regfile 不要求整体清零。复位只清流水 `valid` 和握手状态，未初始化的非 x0 内容
在被软件写入前不得作为有效程序状态；功能安全来自 valid/控制门控。

### 11.5 提交与复位边界

MEM+WB 是唯一架构副作用级：

- ALU、JAL/JALR、完成的 M 指令用 `mem_result` 写回；load 用 `load_data` 写回；
- `mem_mem_read` 与 `mem_mem_write` 对有效指令必须互斥；
- 每个 `mem_valid` 槽至多产生一次 regfile 写或 DMEM 写；
- 核复位不清 IMEM 固件，也不清 DMEM；SoC 上电初始化和软复位语义沿用 v0。

因此软复位后 DMEM 可保留旧值，程序若读取旧 `tohost` 或旧数据，结果可受其影响；
这不是流水错误。tb 若要求干净数据环境，必须显式重新初始化存储器模型。

### 11.6 存储器专项验收点

- load byte/half/word 的 lane 与符号/零扩展均使用寄存后的 `mem_addr`；
- store byte/half/word 检查地址 lane、复制数据、be 及恰好一次写入；
- 气泡、flush、stall、复位期间不得产生 regfile/DMEM 副作用；
- 紧邻 load-use 恰好 1 拍，非相关 load 不造成全局停顿；
- v0 与 v1 使用同一 IMEM/DMEM 模型、固件镜像和 tohost 判据。

## 12. `id_ex_stage.v` 与 `mem_wb_stage.v` 接口

### 12.1 模块边界原则

`if_stage` 的输出寄存器提供 IF/ID 边界；`mem_wb_stage` 提供 ID+EX/MEM+WB
边界。`id_ex_stage` 是中间组合级外壳，不再保存整条指令，因此不会增加第四级。

`id_ex_stage` 复用现有 `decode.v` 与 `alu.v`，接收已经过 forwarding 的两个
寄存器值。`core_top` 负责 regfile、forwarding、hazard、muldiv 与级间总控；
`mem_wb_stage` 只保存提交所需 payload，不自行访问存储器或写 regfile。

### 12.2 `id_ex_stage.v` 输入端口

| 端口 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `in_valid` | in | 1 | 当前 IF/ID 槽有效；所有输出控制的语义前提 |
| `in_pc` | in | 32 | 当前指令 PC，用于 PC+4、branch/JAL 目标 |
| `in_instr` | in | 32 | 当前指令，送 decode |
| `rs1_value` | in | 32 | forwarding 后的 rs1；未使用时忽略 |
| `rs2_value` | in | 32 | forwarding 后的 rs2；未使用时忽略 |
| `muldiv_result` | in | 32 | M 单元结果；仅 M done 被接受时进入下游 |

`id_ex_stage` 不设 `clk/rst_n`，也不拥有 pending。组合输出可随输入变化，只有
`core_top` 产生 `ex_accept=1` 时才允许其 payload 在时钟沿进入 `mem_wb_stage`。

### 12.3 `id_ex_stage.v` 译码与冒险输出

| 端口 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `rs1_addr/rs2_addr/rd_addr` | out | 5 | regfile、RAW 比较与目的寄存器 |
| `uses_rs1/uses_rs2` | out | 1 | 指令是否真正读取对应源 |
| `muldiv_valid` | out | 1 | 当前指令是合法 RV32M |
| `muldiv_op` | out | 3 | M 指令 `funct3` |
| `branch_taken` | out | 1 | branch 条件原始裁决，尚未经过 `ex_accept` |
| `jump_taken` | out | 1 | JAL/JALR 原始裁决，尚未经过 `ex_accept` |
| `redirect_target` | out | 32 | branch/JAL 目标或清 bit0 后的 JALR 目标 |

`branch_taken/jump_taken` 即使组合为 1，也不能直接改 PC；`core_top` 必须按 §9
用 `in_valid && ex_accept` 门控 redirect。

### 12.4 `id_ex_stage.v` 下游 payload 输出

| 端口 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `ex_result` | out | 32 | ALU、PC+4 或 `muldiv_result` 的非 load 写回值 |
| `ex_addr` | out | 32 | load/store 有效地址；其它指令可忽略 |
| `ex_store_data` | out | 32 | 未复制的 forwarding 后 rs2 |
| `ex_reg_write` | out | 1 | regfile 写候选 |
| `ex_mem_read/ex_mem_write` | out | 1 | load/store 控制，合法译码下互斥 |
| `ex_wb_sel` | out | 2 | 沿用 v0：ALU/load/PC+4/M；下游只据此选最终值 |
| `ex_mask_sel` | out | 2 | byte/half/word |
| `ex_sign_ext` | out | 1 | load 符号扩展控制 |

所有 payload 在 `in_valid=0` 时均可为无关值；安全性由写入下游的 `in_valid` 保证。
store data 必须直接等于 `rs2_value`，不能从 ALU B 端或实时 regfile 重新取得。

### 12.5 `mem_wb_stage.v` 端口

| 端口组 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `clk/rst_n` | in | 1 | 上升沿捕获；低有效异步复位只强制清 valid |
| `in_valid` | in | 1 | 上游 `if_valid && ex_accept` 形成的有效提交槽 |
| `in_instr/in_pc` | in | 32/32 | retire、CPI 与波形定位 |
| `in_rd` | in | 5 | 目的寄存器 |
| `in_result/in_addr/in_store_data` | in | 32/32/32 | 非 load 结果、访存地址、store 原始数据 |
| `in_reg_write/in_mem_read/in_mem_write` | in | 1/1/1 | 提交控制 |
| `in_wb_sel/in_mask_sel/in_sign_ext` | in | 2/2/1 | 写回、宽度和扩展控制 |
| 同名 `mem_*` 端口 | out | 同输入 | 上述字段的寄存输出，命名与 §6.2 一致 |

`mem_wb_stage` 每个上升沿都捕获一组输入，不提供 hold/enable 端口。上游停顿时必须
显式送 `in_valid=0`，让旧有效槽提交一次后排空；若加 hold 会造成重复提交风险。

复位分支必须令 `mem_valid=0`；其余 payload 可清零改善波形，但功能不得依赖清零。
输出在整拍内稳定，直接驱动 DMEM 地址/写口、load 扩展、regfile 写回和转发记录。

### 12.6 接口验收点

- lint/编译证明端口宽度与 §6.2 完全一致，无隐式网络或截断；
- 单元 tb 检查正常捕获、气泡覆盖旧槽、复位清 valid，且不存在 hold；
- `id_ex_stage` 输入变化只产生组合变化，不额外延迟一拍；
- `mem_wb_stage` 的一个有效输入只允许形成一次提交；
- debug 字段 `instr/pc` 不参与功能控制，删除其观测用途不应改变结果。

## 13. `forwarding.v`、`hazard.v` 与 `core_top.v` 接口

### 13.1 `forwarding.v`

`forwarding` 为纯组合模块，无 `clk/rst_n`。端口固定如下：

| 端口组 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `enable` | in | 1 | 顶层 `ENABLE_FORWARDING` 常量 |
| `uses_rs1/uses_rs2` | in | 1/1 | 两个源是否真实使用 |
| `rs1_addr/rs2_addr` | in | 5/5 | 消费者源地址 |
| `rs1_data/rs2_data` | in | 32/32 | regfile 原始读值 |
| `ex_valid/ex_we/ex_ready` | in | 1/1/1 | EX 来源状态 |
| `ex_rd/ex_data` | in | 5/32 | EX 来源目的和值 |
| `mem_valid/mem_we/mem_ready` | in | 1/1/1 | MEM 来源状态 |
| `mem_rd/mem_data` | in | 5/32 | MEM 来源目的和值 |
| `wb_valid/wb_we` | in | 1/1 | WB 来源状态 |
| `wb_rd/wb_data` | in | 5/32 | WB 来源目的和值 |
| `rs1_fwd/rs2_fwd` | out | 32/32 | 按 §8 优先级选择后的值 |
| `rs1_sel/rs2_sel` | out | 2/2 | 波形与覆盖使用的来源编码 |

选择编码固定为 `00=RF、01=WB、10=MEM、11=EX`。`enable=0` 时两个 sel 均为
`00`；地址为 x0 时输出固定为 0。两个操作数的选择逻辑完全独立。

### 13.2 `hazard.v`

`hazard` 同样为纯组合模块，只产生控制决策，不保存 stall 计数：

| 端口组 | 方向 | 位宽 | 语义 |
|:---|:---:|:---:|:---|
| `enable_forwarding` | in | 1 | 与顶层参数相同 |
| `c_valid/c_uses_rs1/c_uses_rs2` | in | 1/1/1 | ID+EX 消费者状态 |
| `c_rs1/c_rs2` | in | 5/5 | 消费者源地址 |
| `p_valid/p_we/p_is_load` | in | 1/1/1 | MEM+WB 生产者状态 |
| `p_rd` | in | 5 | 生产者目的寄存器 |
| `muldiv_wait` | in | 1 | §10 定义的 M 等待 |
| `branch_taken/jump_taken` | in | 1/1 | ID+EX 原始控制裁决 |
| `data_stall` | out | 1 | §9.2 的 RAW 停顿 |
| `front_stall` | out | 1 | `data_stall || muldiv_wait` |
| `ex_accept` | out | 1 | `c_valid && !front_stall` |
| `redirect/if_flush` | out | 1/1 | 接受的 taken 控制转移；二者同值 |
| `mem_in_valid` | out | 1 | 等于 `ex_accept`，送 MEM+WB 输入 valid |

`hazard` 不计算 redirect 地址；`core_top` 在 `redirect=1` 时采用
`id_ex_stage.redirect_target`。合法输出必须满足 `redirect && front_stall == 0`。

### 13.3 v1 `core_top.v` 对外接口

模块声明增加一个顶层参数，端口列表保持 v0 完全不变：

```verilog
module core_top #(
    parameter ENABLE_FORWARDING = 1'b1
) (
    input wire clk, input wire rst_n,
    output wire [31:0] imem_addr, input wire [31:0] imem_rdata,
    output wire [31:0] dmem_addr, output wire [31:0] dmem_wdata,
    output wire [3:0] dmem_be, output wire dmem_we,
    input wire [31:0] dmem_rdata
);
```

因此现有 `soc_top` 无参数覆盖时自动使用转发档，不需要改变 SoC 外部接口。
无转发 tb 用 elaboration 参数覆盖为 0，禁止复制或编辑 `core_top.v`。

### 13.4 `core_top` 实例与状态归属

| 对象 | 实例/状态 | 归属 |
|:---|:---|:---|
| 取指 | `pc`、`if_stage` | PC、同步 IMEM 接口、hold/flush |
| 执行 | `id_ex_stage` | decode、ALU、原始控制裁决 |
| 数据相关 | `regfile`、`forwarding`、`hazard` | 操作数、旁路和 stall |
| 多拍执行 | `muldiv`、`muldiv_pending` | 单元实例与 core 内 1 位状态 |
| 提交 | `mem_wb_stage` | 唯一新增边界寄存器 |
| MEM/WB 组合 | core 内连线 | DMEM、load 扩展、写回与提交记录 |

`decode` 和 `alu` 由 `id_ex_stage` 例化，其余模块由 `core_top` 例化。
`ENABLE_FORWARDING` 同时连接 forwarding.enable 与 hazard.enable_forwarding。

### 13.5 三类来源在合并三级中的映射

- EX 视图：MEM+WB 中 `wb_sel=ALU` 的 `mem_result`，表示上一拍 EX 形成的值；
- MEM 视图：MEM+WB 中 `wb_sel=load` 的扩展后 `load_data`；load-use 时值可形成但消费者不接受；
- WB 视图：MEM+WB 中 `wb_sel=PC+4/M` 的最终 `wb_data`；
- 三类均携带当前槽的 valid、we、rd，且不得绕过 `mem_valid`。

该映射只是来源分类；三个视图共享一个 MEM+WB 物理槽，不增加寄存器级。
forwarding 的通用优先级仍按 §8 固定，单元 tb 必须独立覆盖多重命中。

### 13.6 顶层接口验收点

- v1 默认参数下现有 `soc_top` 与所有存储器 tb 无端口改动即可编译；
- 参数 0/1 两档均来自同一文件列表，仅 elaboration 参数不同；
- `redirect/front_stall` 互斥，`mem_in_valid` 在每种 stall/done 情况符合逐拍表；
- 所有 regfile/DMEM 写使能最终包含 `mem_valid`，x0 写入被抑制；
- Verilog 编译不得出现隐式 wire、位宽截断或组合环路警告。

## 14. 指标、验证与证据契约

### 14.1 功能回归门禁

v1 必须与 v0 跑相同 RV32IM 功能集合，并增加三级专项：

| 门禁 | 一键入口/判据 |
|:---|:---|
| v1+转发 | `bash sim/scripts/run_iverilog.sh v1_fwd` 全 PASS |
| v1无转发 | `bash sim/scripts/run_iverilog.sh v1_nofwd` 全 PASS |
| 全量 | `bash sim/scripts/run_iverilog.sh all` 包含上述两档及现有模块/SoC 测试 |
| arch-test | 对同一用例清单逐项运行 `run_arch_test.sh <name> <ext>`，两档签名一致 |
| RV32IM | 八种 M、除零、溢出及整核 `tohost=142879` |
| 冒险专项 | R-type 零气泡；load-use 1 气泡；taken 控制转移 1 气泡 |

任何 PASS 必须来自仓库内 tb 和脚本；命令、工具版本、commit、参数与原始输出归档。
v0 在 tag `partA-v0` 上复现，v1 两档在同一 commit 上复现。

### 14.2 CPI 统计口径

主指标固定为同一三级核的 v1+转发相对 v1无转发，v0 两级只作参考锚点：

```text
cycles  = rst_n 释放后到首次终止 tohost 写入之间的核时钟拍数
retired = 同一窗口内 wb_valid=1 的指令数；气泡不计，M 指令只计一次
CPI     = cycles / retired
gain    = (CPI_nofwd - CPI_fwd) / CPI_nofwd * 100%
```

两档必须使用同一 hex、初始内存、终止条件、最大周期和计数代码。连续相关 R-type
在流水填充后数据气泡为 0、局部 CPI≈1；load-use、muldiv 与 taken 分支的等待拍均
计入 cycles，禁止从数据中删除。

原冻结目标为仅转发 `gain >= 25%`。2026-10-05 首次严格按上述口径完成 CoreMark
2K/32 iterations 双档实测，原门禁结果必须保留为 **FAIL**：

| 档位 | cycles | retired | bubbles | CPI |
|:---|---:|---:|---:|---:|
| v1+转发 | 21,926,509 | 10,106,386 | 11,820,123 | 2.169570 |
| v1无转发 | 23,869,806 | 10,106,386 | 13,763,420 | 2.361854 |

两档 CRC、签名与 retired 一致，转发消除 1,943,297 拍等待，CPI 降幅为 8.14%。
即使乐观地消除两档全部共同气泡，固定的 RAW 周期差相对
`retired + RAW差 = 12,049,683` 拍的 nofwd 下界也只有约 16.13%，因此 25% 不能继续
作为“仅开关转发”的硬门禁。旧 Radix-2 工作点分类实测乘法等待 9,925,509 拍，
占转发档总周期 45.27%。Radix-4 后乘法等待降至 5,113,141 拍，占当前转发档
17,114,141 拍的 29.88%；除法、load-use、控制与 other 类别保持不变。

Radix-4 当前双档 CPI 为 `1.885683 → 1.693399`，固定新乘法器的转发收益 10.20%；
固定转发的新旧乘法器周期降幅 21.95%；新转发+Radix-4 相对原始无转发组合周期
降幅 28.30%。三者分母不同，单项百分比不得直接相加；原始数据见
`data/logs/2026-10-05-partB-radix4-cycle-breakdown/`。

自 2026-10-05 起，Part B 验收拆为：

- **转发功能硬门禁**：同一 RTL 只切 `ENABLE_FORWARDING`；arch-test 同集合通过；两档
  签名、retired、CRC 与最终结果一致；R-type/load-use/M 后继专项满足 §8–§10；
- **CoreMark 转发性能回归门禁**：上述固定镜像和口径下 `gain >= 8.0%`；8.14% 是实测
  基线，8.0% 是防回归下限，不表述为新的设计收益预测；
- 原 25% 仅保留为后续“转发 + 快速乘除 + 分支预测”组合优化的尽力目标。各项收益
  必须分档单独记录，不得把快速乘除或 BHT 的收益归因给转发。

原始日志写入 `data/logs/`，波形/覆盖证据写入 `data/evidence/`，汇总数值写入
`data/metrics.csv`；表格必须链接原始日志，禁止只留手抄结果。

### 14.3 Vivado 与频率门禁

- 使用同器件 `xc7z020clg400-1`、同 Vivado 版本和同报告口径比较 v0/v1；
- 每个报告点必须满足 WNS≥0、无未约束内部端点、无 Error/Critical Warning DRC；
- Part B 基本验收：v1 功能通过，实际最高通过频率相对 v0 提升或持平；
- 125 MHz 是非阻塞加分目标，未经 WNS≥0 不得直接把板载 125 MHz 接入核；
- 到收尾时间盒仍未通过 125 MHz：保留实测最高通过频率，停止追频并启动 L3；
- L3 固定为“两级 + 完整转发”，不得因追频拖慢 M1 功能与 CPI 收口。

报告保存于 `build/reports/`，至少包含 utilization、timing summary、worst paths、
clock utilization、check_timing、DRC 和 Vivado 版本。bitstream 只能在门禁后生成。

### 14.4 板级表述与证据

生成 bitstream 或 `PROGRAM PASSED` 均不能单独记为“已上板通过”。只有实际下载
PYNQ-Z2，并观察到约定 LED/tohost 现象，才可追加 board 日志；报告须记录 bitstream
对应 commit、核时钟、Vivado 版本、连接方式和观察结果。当前已验证 40 MHz 属 v0；
v1 未重新下载和观察前必须标为“待上板”，不得借用 v0 证据。

## 15. 已确认决策 D1–D15

| ID | 已选方案 | 未选方案 | 核心理由 |
|:---:|:---|:---|:---|
| D1 | IF / ID+EX / MEM+WB 三级 | 增加独立 EX/MEM/WB 级 | 控制规模与提频收益平衡 |
| D2 | 同步 IMEM 计入 IF，仅两个边界 | IMEM 后再固定打一拍 | 避免实际变四级 |
| D3 | 同 RTL + 顶层参数切转发 | 复制或手改源码 | 公平、可复现的单变量对比 |
| D4 | `962a4f5` 标记 `partA-v0` | 用移动分支名作基线 | v0 锚点不可漂移 |
| D5 | 显式 valid 门控所有副作用 | 只把 instr 改 NOP | 控制残留不能误提交 |
| D6 | `EX > MEM > WB > RF` | 固定选旧来源 | 最近生产者优先 |
| D7 | decode 输出 uses_rs1/uses_rs2 | 只比较指令位域 | 排除伪 RAW |
| D8 | load-use 固定停 1 拍 | DMEM→ALU 零拍旁路 | 缩短关键组合路径 |
| D9 | 转发覆盖 ALU/branch/JALR/store/M | 只覆盖 ALU | 所有真实消费者语义一致 |
| D10 | ID+EX 裁决、taken 冲刷 1 槽 | Part B 引入 BHT | 先保证静态语义，预测留 Part C |
| D11 | M 留在 ID+EX，MEM+WB 排空 | 冻结全部流水 | 防止较老指令重复提交 |
| D12 | M done 经 MEM+WB 统一写回 | done 直接写 regfile | 单一提交与转发口径 |
| D13 | core_top 原位演进，v0 用 tag 留存 | 长期维护两份 core | 避免接口和修复分叉 |
| D14 | CPI 主比 v1开/关转发 | 相对 v0 宣称降 25% | v0 CPI≈1，不是有效降幅基线 |
| D15 | 125 MHz 非阻塞时间盒 + L3 | 无限追频 | 功能正确和 CPI 优先 |
| D16 | 转发功能硬门禁 + CoreMark gain≥8.0% 回归门禁；25% 改为组合尽力目标 | 继续以 25% 验收仅转发 | 8.14% 实测与 16.13% 乐观上界证明原目标不可达 |

D1–D15 已由用户全部确认；D16 由 2026-10-05 实测证据触发并经用户确认。D4 标签与
交叉引用已在 1B-10 完成；若实现证据推翻假设，必须先回到文档提出新决策，不得静默改 RTL。

## 99. 契约编写状态

- [x] 三级拍序、流水寄存器字段及裁剪规则；
- [x] 转发真值表、mux 优先级与关闭转发模式；
- [x] load-use、flush、stall 的逐拍行为；
- [x] RV32M 多拍流控；
- [x] 存储器与 regfile 三级语义；
- [x] forwarding/hazard/core 端口和位宽；
- [x] CPI、回归、Vivado 与板级验收；
- [x] D1–D16 已确认决策；
- [x] v0/plan 交叉引用及决策记录定稿。
