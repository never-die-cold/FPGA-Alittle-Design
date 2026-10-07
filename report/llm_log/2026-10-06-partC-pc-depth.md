# 2026-10-06 Part C：保持三级的 PC/flush 降深度

> 标签：#riscv #时序优化；平台：Codex；起点：dev/rtl@3c6b794；本轮未提交。

## 任务与授权

用户提供验证线 BHT2 核 OOC @11.520 ns 实点 WNS=-0.334 ns，关键路径为
`u_if_stage/instr_hold_reg[5] -> u_pc/pc_reg[27]`，17 级，Data Path 11.860 ns，
logic/route=33.4%/66.6%。保留原 FAIL；这些数字为用户转述，本轮未执行 Vivado。
要求保持三级、不改误预测一个年轻槽/正确预测零气泡、不改变四档统计语义。
用户随后明确授权“直接给我生成全部代码，问题最后写出”，本次豁免逐步等待，
代码按以下小块顺序落盘、自检；实现时 commit 理解门槛尚未通过，不 commit、不 push。

## 实施顺序

| 块 | 设计与文件 | 自检 |
|:---|:---|:---|
| P0 | design_v1 §16.4：地址真值表、valid-only flush、三级与复测目标 | 对照实际 RTL |
| P1 | tb_core_pc_control + 脚本：先用旧公式保存 PC/flush 判据 | 原实现 768 例 PASS |
| P2 | core_top：按互斥条件展开地址选择，正确 taken 不再反向依赖 mispredict | 768 例 PASS、bht_flow PASS |
| P3 | id_ex_stage/core_top：组合 B 目标/后继端口，直接拼接立即数，独立计算 | B 偏移全覆盖；ID+EX 12304 例 PASS |
| P4 | if_stage + tb_if_stage + tb_core_bht_flow：flush 只改有效位，复核副作用门控 | IF 12 例、BHT 三档 PASS |
| P5 | plan/交接/日志：用户实点 FAIL、源码指纹、复测命令 | 全量回归结果见原始日志 |

## 逐段讲解

core_top 的 branch_fetch_taken、branch_recover_taken、branch_recover_fall 与
predicted_redirect 表示四种分支方向组合。它们均从 branch_resolve（含 ex_accept）
形成。jump_redirect 只属于跳转；合法译码不会 branch+jump 同时有效。
地址数据按互斥条件掩码后相或，避免多次经过恢复、预测、目标的优先选择链。
recover_valid 仍生成 redirect/flush；PC 地址选择独立从原始互斥条件产生。
recover_pc 是组合观察值，没有增加恢复寄存器或流水级。

id_ex_stage 直接拼接符号扩展 B 立即数，branch_target=in_pc+branch_imm。
branch_target_next=in_pc+(branch_imm+4) 使用独立 PC 加法，不从已选择的
redirect_target 再加 4。完整 32 位运算保留负偏移、bit1 和回绕；只有有效条件分支
才选择这些组合值。新的加法可能增加 LUT，须以 Vivado 确认收益与代价。

if_stage 的 flush_q 只进入 instr_valid，instr 数据只受 stall_q 选择保持/直通。
无效槽允许含 store/M/JAL 编码，ex_accept、muldiv_start、BHT 更新/统计均含 valid；
MEM+WB 仍是唯一提交点。测试先查无效 EX 槽无启动/改向，再查下一拍无提交。
保持寄存器仍只在 stall 首拍保存，结束 stall 的采样边沿仍看到原指令。

## 验证与证据

原始命令、输出及退出码：`data/logs/2026-10-06-partC-pc-depth/`。
`source_manifest.json` 包含起点 HEAD、实际修改源码（含新 tb）逐文件 SHA256；
不能只用起点 HEAD 标记尚未提交的运行版本。首跑全量退出 1：RISC-V 和 vision RTL
均 PASS，vision Python 本地 HTTP socket 被沙箱拒绝。独立 HTTP 用例在沙箱外重跑
PASS；第二次沙箱外 all 随聊天中断终止，日志保留无转发档 PASS，无完整退出码。
2026-10-07 用户要求继续后检查无后台仿真进程；第三次用仓库内 run_all.sh 脱离会话
执行相同完整 all，最终退出码 0，全量 PASS，源码保持不变。保留前两次日志，
以 all-final.exit.txt 和 README.md 为准；check_results.py 独立核对同样 PASS。
四档 cycles 为 19057438 / 17114141 / 16335562 / 16232079，retired 均为 10106386，
CRC 均为 8799，lookup/hit/miss 和分类气泡数同原锚点。
无 /tmp，新增 tb 均有独立入口并进入 all。
用户要求额度耗尽有备用记录，已新增 docs/partC-pc-depth-resume.md：代码位置、
三次执行状态、后台启动方式、核对/恢复命令、待用户理解题；实际退出码优先于文档状态。
Verilog-2001 core_top 编译无输出、无隐式 .*、git diff --check 无输出。
本机无 Vivado；优化后 WNS/Fmax/资源未验证，交验证线实跑 11.520 ns 和四档 10 ns。
不保证综合后的逻辑级数，布线占比与新增扇出也可能影响结果。

## 理解门槛（2026-10-07，3/3 通过）

1. 预测跳且实际跳时，为什么 IMEM 要取 T、拍末 PC 要存 T+4？改成 PC=T 会怎样？
2. flush 后 instr 中仍是 mul/store 编码，哪些 valid 门控防止错误启动或提交？只清 NOP 为什么不够？
3. 768 例等价、四档 CRC/retired/cycles 一致后，为什么还不能宣布 86.8 MHz 达标？验证线还要检查什么？

### 用户第 1 题完整答案

正确预测跳转时，为什么 IMEM 取 T、PC 保存 T+4？保存 T 会怎样？

因为同步 IMEM 是“这拍给地址、下拍才出数据”：

- 这拍 imem_addr = T（目标地址）：IMEM 本拍末采样 T → 下一拍吐出目标指令；
- PC 存的是“下一条要取的地址”：目标指令这拍已经被取走了，所以下一拍该取 T+4（顺着目标往下走）。

如果 PC 存 T：下一拍 imem_addr 又是 T → 同一条目标指令被取第二遍 → 重复执行。

比喻：你已经把“右转后第一家店”下进订单（IMEM 正在取），再下一站要写“那家店的下一家”；若还写“第一家”，就重复逛同一家店。

一句话：这拍取 T、下拍取 T+4；PC 存 T 就会重复取同一条目标指令。

判定：通过。准确区分同步取指采样与下一次取址，解释了正确预测零气泡所需的 T+4。

### 用户第 2 题完整答案

flush 后指令仍可能是 mul/store，哪些有效位门控保证它不启动、不提交？

关键是 valid 位——flush 会把年轻错误槽的 valid 清 0，而所有副作用都被 valid 门控：

| 副作用 | 门控条件 | valid=0 时 |
|:---|:---|:---|
| store 写内存 | dmem_we = mem_valid && mem_mem_write | 不写 |
| 寄存器写回 | rf_we = mem_valid && mem_reg_write && mem_rd!=0 | 不写 |
| 乘法启动 | muldiv_start = instr_valid && muldiv_valid && … | 不启动 |

即：IF/ID 的 instr_valid 挡住取指/启动，ID+EX/MEM+WB 的 mem_valid 挡住提交。
就算译码出来的 mul/store 控制位还残留，只要 valid=0，就一律不发生副作用。

一句话：instr_valid 挡启动、mem_valid 挡提交；valid=0 时 store 不写、寄存器不写、乘法不启动。

判定：通过。补充精确定义：instr_valid 不阻止 IMEM 本身取数，而是门控本槽执行副作用；
mem_valid 只属于 MEM+WB 槽。instr_valid 经 ex_accept/mem_in_valid 阻止无效槽进入有效提交状态；
没有额外 ID+EX 流水寄存器。redirect 和 BHT 更新/统计同样受 branch_resolve/ex_accept 门控。

### 用户第 3 题完整答案

四档功能数据完全一致，为什么仍不能证明主频达标？还需要哪些 Vivado 证据？

因为仿真的“功能/周期”数据和“真机时序”是两码事：

- Icarus 仿真里没有门延迟、没有布线延迟，算得出 CPI、CRC，但算不出“电路能不能在某个频率跑”；
- 主频达标（WNS≥0、Fmax）必须靠 Vivado 综合 + 布局布线 + 静态时序分析，在真实网表/器件上量。

还需要的 Vivado 证据：

- 时序报告：WNS、Fmax、timing summary、worst paths、check_timing（无未约束端点）；
- 目标频率实点：如 BHT2 的 11.520 ns（≈86.8 MHz）实测是否 WNS≥0；
- 资源报告：LUT/FF/BRAM/DSP 占用；
- DRC、以及 OOC/SoC 各级的时序结果。

判定：通过。频率判据是相同流程下的约束实点 WNS≥0，不将 slack 外推当作最高实测通过频率。
OOC 的外部数据口可能有刻意未约束项，需按原 OOC 契约检查，不能用无关 false path 隐藏内部违例。

总判定：3/3，通过；完整讲解见上文“逐段讲解”。本轮仅归档答案，不 commit、不 push。
下一项：交验证线按交接单 §5 复测 BHT2 11.520 ns 与四档 10 ns；优化后物理实现仍未验证。

## 经验

控制命名本身不减少时序深度；需要调整真实数据/选择拓扑。保持原 PC/flush 公式为
独立参考，功能等价与时序收益分别取证。三级不变通过“不加时序边界”兑现。
