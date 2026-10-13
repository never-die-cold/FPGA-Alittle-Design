# 2026-10-13 SoC 复位/CE 物理代价修复：mem_wb_stage 分离复位

一句话结论：`mem_wb_stage.v` 把 payload 移出异步复位块的 `else` 分支后，SoC 40 MHz bht2 的 WNS 从 3.618 ns 升到 6.447 ns，复位派生 CE 类最差路径全部消失，benchmark 周期数逐拍不变，CoreMark 金标准 PASS。

## 内容

- `README-regression.md` —— 仿真证据：基线（HEAD `3e2e1c9`）与改后各模式的命令、退出码、周期数。四档 benchmark 周期数逐拍一致；全量 CoreMark 2K/32 金标准改后 PASS（17114141 cycles，CPI 1.693）。
- `vivado/README-ab.md` —— Vivado A/B 证据：方法、WNS/端点/资源对照、control sets 与高扇出机制证据、频率外推与下一步瓶颈。
- `baseline-*` / `postpatch-*` —— 逐模式原始日志与 `.command.txt` / `.exit.txt`。
- `baseline/` —— 上一会话一次失败的 Vivado 启动尝试（`setupEnv.bat` 拒绝访问），按惯例保留痕迹；与本轮 A/B 无关，本轮实际入口是 `build/run/run_vivado.bat`。
- `vivado/baseline_root/` —— 基线源码快照（`git archive HEAD src/riscv`），两棵源码树仅 `mem_wb_stage.v` 不同。

## 改动

- RTL：`src/riscv/mem_wb_stage.v`（`mem_valid` 保留异步复位；payload 独立无复位无使能时序块）。
- 测试：`sim/riscv/tb_mem_wb_stage.v`（新增复位期 payload、释放、短脉冲检查）。
- 契约：`src/riscv/design_v1.md` §12.5。
- 工具：`sim/scripts/build_soc_ab.tcl`（A/B 对照构建入口）。

副作用安全性：`rf_we`、`dmem_we/dmem_be`、转发资格（`ex_valid`/`p_valid`）均由 `mem_valid` 门控（`core_top.v:125/148/160/209-210`），复位期间 payload 变化无架构副作用。

## 未做 / 未接入

- dmem 分银行或同步 BRAM（下一个物理瓶颈：4140 LUT、地址位扇出 4097）。
- 核 OOC fmax 的 A/B 复测。
- bitstream 重出与上板复测（本轮 A/B 不写 bitstream）。
