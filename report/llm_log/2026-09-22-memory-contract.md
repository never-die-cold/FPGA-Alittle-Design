# [2026-09-22] 协作记录：Part A 统一 32KB 存储器契约

> 标签：#riscv #架构决策 #soc
> 平台：Codex（VS Code 插件，WSL）｜模型：GPT-6
> 相关 commit：未提交；等待理解门槛

## 1. 决策

- IMEM/DMEM 均冻结为 `8192×32`（32KB），地址范围均为
  `0x8000_0000–0x8000_7FFF`，数组索引统一取 `addr[14:2]`。
- IMEM 保持同步读；DMEM 保持异步读并支持 4 位字节写使能。
- `tohost=0x8000_3FF0`、`tohost_exit=0x8000_3FF4` 保持不变。
- 当前纯 PL 核只使用片上存储资源，不假设能直接访问 PS 侧 512MB DDR3。

## 2. 为什么定为 32KB

`plan.md` §3.2 把存储扩容列为 CoreMark 前置任务。统一为 32KB 可消除固件、
testbench 与 SoC 外壳容量不一致，并为后续基准程序留出空间。PYNQ-Z2 的
XC7Z020 有 140 个 36Kb BRAM 块；按原始容量折算，每个 32KB 存储器需要
`ceil(32KB / 4.5KB)=8` 块，两侧合计约 16 块，即 `16/140≈11.4%`，容量宽裕。

该数字是容量等价估算，不代表最终综合映射：同步读 IMEM 预计可映射约 8 个
BRAM36；异步读 DMEM 通常不能直接推断为 Xilinx 块 RAM，可能映射为 LUTRAM。
实际 BRAM/LUT 占用必须以后续 Vivado utilization report 为准。

## 3. 为什么 DMEM 保持异步读

`design_v0.md` §9 决策 1 已冻结数据 RAM 异步读。两级核要求 load 数据在执行拍
同拍返回并写回，才能保持 §2.2 的“无 load-use 停顿、CPI≈1”锚点。改成同步读
会引入额外等待拍并改变基线微架构，因此本次扩容只改容量和索引，不改读时序。

## 4. 为什么不移动 `tohost`

现有 RV32I/RV32IM 固件和 testbench 都以 `0x8000_3FF0` 的结果字及相邻退出码
作为冒烟判据；扩容后这两个地址仍合法。保留地址可继续复用既有判据并避免无关
的链接脚本、固件和验证协议迁移。32KB 新增空间位于它们之后，不要求移动观测口。

## 5. 范围与后续验证

本轮只同步 `design_v0.md`、修正 `plan.md` 的旧容量表述并记录决策，尚未改变
固件、testbench 或 SoC RTL。后续分步统一存储器模型并运行
`bash sim/scripts/run_iverilog.sh all`，重新确认 RV32IM `tohost=142879`；完成
SoC 外壳、Vivado 综合与真实板级测试前，不声称已经上板。
