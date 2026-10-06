# [2026-10-06] 协作记录：Part B T2 SoC 复验与上板（XSim 回归 + 40MHz 构建 + LED=1101）

> 标签：#riscv #验证 #hardware #build
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：被测 `dev/rtl@b93afaa`（T2）；证据随本条记录入库
> 用途：T2 上板验证（功能回归 + 40 MHz 构建 + 实机）；与核 OOC Fmax 记录配套

## 1. 任务与初始提示词

> "现在要求做上板验证了"

被测件 = `dev/rtl@b93afaa`（T2：`id_ex` 分支比较解耦 ALU + `core_top` 转发接线简化）。此前已做 T2 核 OOC 复测（`2026-10-06-partB-t2-fmax`）；本轮做 **SoC 上板**。

## 2. 模型第一版方案

按既有口径（`docs/partB-rtl-handoff.md` §2/§3）：切临时分支到被测提交 → XSim 功能回归 → 40 MHz SoC 构建（门禁）→ JTAG 下载 → 肉眼观察 LED=`1101` → 归档。

## 3. 失败现象（真实偏差）

本轮**无失败**：T2 功能回归全 PASS、40 MHz 构建 WNS +7.388、上板 LED=`1101`。相关未决项记录于配套证据：
- T2 核 OOC：11.52 ns 通过、**10 ns WNS −0.009（差 9 ps）未达 100 MHz**（见 `2026-10-06-partB-t2-fmax`）；
- 关键路径仍在 `if_stage` 控制→`pc`（倾向 T4，T3/T4 由 RTL 裁定）。
- SoC 125 MHz 档本轮未做（非阻塞）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | "要求上板验证" | 需先确认被测代码在 git（沿用上次教训） | `ls-remote` 确认 `dev/rtl=b93afaa`，切临时分支 | ✅ |
| 2 | T2 改了 RTL/tb | 功能需独立复跑 | `run_riscv_xsim.bat all` | ✅ `PASS: RISC-V XSim mode all` |
| 3 | 构建 40 MHz | 门禁 WNS≥0 / DRC | `build_soc.tcl -tclargs 40` | ✅ `WNS=+7.388`（T2 前 +4.850） |
| 4 | 上板 | 需真实观察 | `program_soc.bat <40MHz.bit>` | ✅ `PROGRAM PASSED`，LED=`1101` |

## 5. 最终结论

- **T2 代码 40 MHz 档上板验证通过**：XSim 功能回归 PASS；40 MHz 构建 `BUILD PASSED`，**WNS +7.388 ns**、0 Error/0 Crit DRC，LUT 6325 / FF 749；位流 SHA256 `E7BB4041…61E5`；`PROGRAM PASSED`，**LED=`1101` 静止**，BTN0 `0000→0001`（与 v0/前版一致）。
- 本次仅 **40 MHz 档**；SoC 125 MHz 未做；核 OOC 频率与 SoC 频率分开（配套记录 `2026-10-06-partB-t2-fmax`）。
- 证据：`data/logs/2026-10-06-partB-t2-board/`（`xsim/`、`reports/soc_40mhz/`、构建与下载日志）；上板记录 `board/logs/2026-10-06-partB-t2-board/README.md`。

## 6. 经验沉淀

- 触发条件：优化提交（改了 RTL/tb）后的功能复跑与上板复验 #skill候选
- 排查步骤：
  1. **先确认被测 commit 在 git**（`ls-remote` + 工作区），再切临时分支，label 与 commit 绑定；
  2. **优化也要跑功能回归**：改了 RTL/tb 就必须重跑 XSim，别默认"只影响时序"；
  3. 上板判据仍是同一固件同一现象（LED=`1101`），"优化不改语义"；
  4. 频率口径分离：核 OOC（约束点/外推）≠ SoC 档位。
- 适用范围（换题目/换板卡是否成立）：成立；任何"性能优化提交"的验证流程均适用。
