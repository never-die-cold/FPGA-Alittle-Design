# [2026-09-11] 协作记录：RV32I 逐指令自检落地——lb 用例小端纠错与调试方法

> 标签：#riscv #验证 #bug修复
> 平台：OpenCode ｜ 模型：deepseek-flash (deepseek/deepseek-flash)
> 相关 commit：`87d3f4f`（自检汇编）、`58ed400`（逐指令 tb 与脚本）+ 本条记录本身

## 1. 任务与初始提示词

v0 核程序级冒烟 PASS 后，用户 "continue"，继续补齐 Part A 验收项「冒烟 testbench：每条 RV32I 指令一个汇编单测」。

## 2. 模型第一版方案

编写 `sw/riscv_fw/test_rv32i.S`（作为 `main` 被 start.S 调用）：38 个自检用例，约定 `a0 = 失败用例编号`，失败即跳 `L_done` 返回；全部通过 `a0 = 0`。
新增 `sim/riscv/tb_core_test.v` 检查 `tohost_exit == 0`；`run_iverilog.sh` 改为依次跑两个 tb。

用例覆盖：R/I 型算术逻辑移位（19）、U 型（2）、访存 sw/sh/sb/lw/lh/lhu/lb/lbu（8）、6 条分支 taken/not-taken 双向（6）、jal/jalr（2）、x0 硬连线（1）。

## 3. 失败现象（真实偏差）

1. **首跑 `FAIL: test #25 failed`（lb 符号扩展）**。逐拍 trace（过滤 a0/x6/x7 写回与访存）显示：
   ```
   t=1595000 STORE [80000800] = 80000000 be=1111
   t=1605000 RAW instr=ff010303 da=80000800 dr=80000000 we=0 ext=1 mask=00
   ```
   核的 `lb` 路径正确（`ext=1/mask=00`、内存值正确），问题出在**测试用例自身**：`0x80000000` 小端存储时 `0x80` 在第 3 字节，`lb` 读第 0 字节当然是 `0x00`。
2. **调试 tb 两处小坑**（临时文件，不入库）：
   - `imem_rdata` 再次被写成 `wire` 后又做过程赋值（与正式 tb 早期同一错误）；
   - 过滤条件用 `$time > 1580000` 不生效——`%t` 按精度（1ps）显示，但 `$time` 返回值单位与显示不同；且调试打印 `dmem[32'h80000800>>2]` 越界返回 x（下标需按 `[13:2]` 截断）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `FAIL: test #25` + 过滤 trace | 核正确读取了 `dr=80000000` 并按 `lb` 扩展；是测试期望值放错字节（小端） | 用例 25/26 的存储值改为 `0x00000080`（低字节即 0x80） | ✅ 38 用例全过 |
| 2 | 调试 tb 报 `imem_rdata` l-value | 与正式 tb 早期相同的 wire/reg 误用 | 调试 tb 中改 `reg` | ✅ 编译通过 |
| 3 | 过滤 trace 无输出 | `$time` 单位与 `%t` 显示不一致（ps） | 过滤阈值改 `1580 < $time < 1620` | ✅ trace 输出 |
| 4 | `final ... xxxxxxxx` | 调试打印数组下标越界 | 地址 `>>2` 后按 `[11:0]` 截断 | ✅ 打印正确 |

## 5. 最终结论

- `hello_test`（RV32I，38 用例）在 v0 核上全过：`PASS: all RV32I tests passed (tohost_exit = 0)`
- 程序级冒烟与逐指令自检两个 tb 由 `bash sim/scripts/run_iverilog.sh` 一键复跑，均 PASS
- 失败编号机制（`a0 = 失败用例号`）让"哪里挂了"一眼可见，适合后续回归
- 产物：`sw/riscv_fw/test_rv32i.S`、`hello_test.dis/hex`、`sim/riscv/tb_core_test.v`

**验证方式**：`run_iverilog.sh` 输出两行 PASS；逐指令用例覆盖 R/I/U/访存/6 分支/jal/jalr/x0。

## 6. 经验沉淀

- 触发条件：自检 testbench 报错时，先分辨"DUT 错"还是"测试期望错" #skill候选
- 排查步骤：
  1. 打印被测通路的**关键中间信号**（本例 `dr/we/ext/mask`），若数据通路各环节都符合预期，则回头检查用例的期望值
  2. 涉及访存/字节的期望值必须按**小端与字节偏移**复核（`0x80000000` 的 `0x80` 不在第 0 字节）
  3. 调试 tb 也要遵守正式 tb 的语法规范（wire/reg），避免浪费一轮编译
  4. 写时间过滤时注意 `$time` 单位与 `%t` 精度显示的差异；数组下标按位截断防越界
- 适用范围：换总线、换访存接口、换仿真器均成立
