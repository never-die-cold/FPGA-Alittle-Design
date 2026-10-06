# [2026-10-05] Part B D2.2b：RV32M 转发双档冒险边界

> 标签：#riscv #流水线 #RV32M #验证
> 范围：同一三级核、同一程序，只切 `ENABLE_FORWARDING`

## 1. 任务与设计

现有 `tb_core_v1_muldiv_flow.v` 只验证转发开启。D2.2b 将它参数化，补齐无转发时
M 指令启动前后的 RAW 行为：

- `addi x2` 后紧跟 `mul x3,x1,x2`：无转发时先停 1 拍，操作数就绪后才 start；
- `mul x3` 后紧跟 `addi x4,x3,1`：无转发时再停 1 拍，等 x3 提交；
- 每个数据停顿拍断言 `muldiv_start=0`、`front_stall=1`、`mem_in_valid=0`；
- 两档都要求 start/done/x2/x3/x4 写回各恰好一次，busy 恰好 32 拍。

脚本新增 `v1_muldiv_fwd` / `v1_muldiv_nofwd`，并把两档顺序纳入 `all`；旧
`v1_muldiv_flow` 入口保留兼容。

## 2. 验证结果

```text
PASS: v1 muldiv mode=1 start=1 busy=32 done=1 x2/x3/x4=1/1/1 stalls=0/0/0
PASS: v1 muldiv mode=0 start=1 busy=32 done=1 x2/x3/x4=1/1/1 stalls=2/1/1
PASS: muldiv 8 operations, boundaries and handshake
PASS: RV32IM core tohost=142879 exit=0
PASS: coremark cycles=21926510 instrs=10106387 bubbles=1243810 cpi=2.169
```

完整命令 `VISION_PYTHON=python3 bash sim/scripts/run_iverilog.sh all` 最终退出码为
0。`git diff --check` 无输出，`src/` 无 `.*`。Vivado OOC、正式 CPI 与 arch-test
仍未验证。

## 3. 理解门槛

### 问题 1

无转发档中，`mul` 等 `addi x2` 的停顿拍为什么不能 start？

用户回答：x2 尚未写回寄存器堆，若此时启动，muldiv 会锁存旧 x2 或垃圾值；必须
保持 `muldiv_start=0`，等正确操作数可见后再启动。

### 问题 2

为什么 M 结果的后继消费者在转发开时不停，关闭时停 1 拍？

用户回答：转发开时直接从 MEM+WB 结果旁路取得 21；转发关时只能等待 x3 写回，
下一拍再从寄存器堆读取 21。

### 问题 3

为什么无转发多两拍，start/done/x3 写回仍必须各一次？重复 start 如何暴露？

用户回答：停顿只延长周期，不能改变一条指令的架构事件次数。重复启动会使 start
计数大于 1，并可能使 busy 拍数、done 次数、x3/x4 写回次数或结果偏离期望。

### 判定

三题全部通过。用户能够说明启动前操作数就绪门控、完成后的旁路/等待差异，以及
“增加周期不增加提交次数”的原则。D2.2b 理解门槛完成，可以本地提交；不得把
本次微测试周期或停顿数当作正式 CPI，也不得声称 Vivado 已验证。
