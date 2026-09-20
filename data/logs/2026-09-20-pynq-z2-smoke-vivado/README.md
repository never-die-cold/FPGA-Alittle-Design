# PYNQ-Z2 LED smoke test 验证证据（2026-09-20）

> 用途：PR #15（`test(board): add PYNQ-Z2 LED smoke test`）的独立复核证据；`board/smoke_test/` 上板前的仿真与构建门禁记录。
> 步骤与上板验收说明见被测件自带文档 [`board/smoke_test/README.md`](../../../board/smoke_test/README.md)（不在此重复维护，避免两份步骤漂移）。

## 被测版本（锚点）

| 项 | 值 |
|:---|:---|
| PR | #15，head commit `1fb6787`（`test/pynq-z2-smoke`，误建分支，已删除） |
| 合并后位置 | `dev/rtl`，merge commit `93eeb97`（本轮证据即在此树复跑） |
| 被测文件 | `board/smoke_test/`（rtl / constraints / sim / scripts，共 7 个文件） |

## 环境

| 工具 | 版本 |
|:---|:---|
| Icarus Verilog | 13.0（MSYS2 ucrt64，需 `export PATH=/ucrt64/bin:$PATH`） |
| Vivado | 2026.1（BASIC，win64，SW Build 6511674） |
| 器件 | `xc7z020clg400-1`（PYNQ-Z2，速度等级 -1） |

## 结果 1：Icarus Verilog 自检（4 组分频全过）

```
TEST PASSED: DIV_CYCLES=1, startup/reset/24 steps
TEST PASSED: DIV_CYCLES=2, startup/reset/24 steps
TEST PASSED: DIV_CYCLES=5, startup/reset/24 steps
TEST PASSED: DIV_CYCLES=8, startup/reset/24 steps
TEST PASSED: all divider configurations
```

原始输出：`run_iverilog_2026-09-20.log`（从 `dev/rtl@93eeb97` worktree 复跑）

## 结果 2：Vivado 综合/实现/bitstream（BUILD PASSED）

| 项 | 实测 | 说明 |
|:---|:---|:---|
| 综合 | 0 error / 0 warning | 常量函数、寄存器 INIT、ASYNC_REG 均被 2026.1 正常接受 |
| 时序（route 后，8 ns / 125 MHz） | **WNS +4.094 / TNS 0.000 / WHS +0.052 / THS 0.000 / WPWS +3.500**，失败端点 0 / 65 | "All user specified timing constraints are met." |
| DRC | 0 Error / 0 Critical Warning；1 Warning `ZPS7-1`（纯 PL 设计未例化 PS7，预期现象） | 不阻塞 JTAG 配置 PL |
| 资源 | LUT 8 / FF 32 / IOB 6（4.8%）/ BUFG 1 | XC7Z020 占用 < 0.1% |
| bitstream | 4,045,772 B，SHA256 `B8D9EC9B624EA8FD04D95FFE8316254E49C1F1CDF9EA9DF572BE9E75A6312E54` | 生成于 `C:\fpga_build\pynq_z2_smoke\run_20260920_150800_13452\pynq_z2_smoke.bit` |

附件（本轮构建产物副本）：

| 文件 | SHA256 |
|:---|:---|
| `timing.rpt` | `240B74DDAD93A549D6230495D25FBB3F91B5E72F8E5C45E95B9CDD322B4EC902` |
| `utilization.rpt` | `22D1590CCF4BA1BCA3C01633DAEAD2590731FC94A237CAC151B05A84416D3EFC` |
| `drc.rpt` | `0E33FD07EF242A423287E58A7E9544E987B473018669717CC44C9AF44458719E` |

## 复跑方法

```bash
# 仿真（MSYS2 UCRT64 shell；注意 PATH 需含 iverilog/vvp）
bash board/smoke_test/sim/run_iverilog.sh

# 构建（Windows Vivado，产物写到 C:/fpga_build，不入库）
cd /d C:\fpga_build\pynq_z2_smoke
vivado -mode batch -source "<repo>/board/smoke_test/scripts/build.tcl"
```

## 边界与待办

- 本目录只归档**独立复核证据**；被测件步骤文档、上板验收清单在 `board/smoke_test/README.md`（归 RTL 线维护）
- **上板实测记录**按 `board/README.md` 约定另记（日期/接线/bitstream hash/现象，只追加）
- **理解门槛**（逐段讲解 + 3 题 + llm_log）与上板验证为 `dev/rtl → main` 合并前置，PR #15 评论区已留验证结果

## 关联

- PR #15 复核评论（Vivado/仿真结果）
- `report/llm_log/2026-09-20-pynq-z2-smoke-verification.md`
