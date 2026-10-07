# Part B RTL 提交与验证交接单

> 2026-10-07 补证：完整三级核及四档外部复验见 [收口报告](../report/module1-closure.md)；下文“待执行/未验证”保留为当时交付快照。

日期：2026-10-05。当前状态：三级核、转发、Radix-4 乘法已完成功能验证；
XSim、Vivado v1 时序和 PYNQ-Z2 实机仍待执行，不能写“Part B 全部完成”或“v1 已上板”。

## 1. RTL 线提交前

```bash
bash sim/scripts/run_iverilog.sh clock_cfg
bash sim/scripts/run_iverilog.sh all
iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v
grep -rn '(\.\*)' src/
git diff --check
git status --short
```

判据：两项仿真退出码为 0 且出现 PASS；Verilog-2001、`grep` 和 `diff --check`
无输出。已知 `$readmemh: Not enough words` 表示短镜像后的预填区未覆盖，不是失败。

理解题通过后才可 commit。由于本地 `dev/rtl` 与远端曾分叉，推送前执行：

```bash
git add <本轮审定文件>
git commit -m "完成 Part B 三级核与双频构建配置；AI 协作：按古法补齐回归、CPI 与交接"
git fetch origin
git pull --rebase origin dev/rtl
bash sim/scripts/run_iverilog.sh all
git diff --check
git push origin dev/rtl
```

rebase 冲突或 push 拒绝时停止，禁止强推。

## 2. 验证线 Windows 复验

从仓库根目录依次执行：

```bat
sim\scripts\run_riscv_xsim.bat all
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_soc.tcl -tclargs 40
D:\vivado\2026.1\Vivado\bin\vivado.bat -mode batch -source build/build_soc.tcl -tclargs 125
```

- 40 MHz 是安全基准档，125 MHz 是非阻塞目标档；两档都经过 MMCM，125 MHz 未直连核。
- 报告分别位于 `build/reports/soc_40mhz/`、`build/reports/soc_125mhz/`。
- 每档必须确认两个时钟存在、无未约束内部端点、WNS≥0、无 Error/Critical Warning DRC。
- 125 MHz 失败时保留原始 FAIL 和实际最高通过频率，不得生成或冒用 125 MHz 位流。
- 当前 WSL 未实际运行 Vivado/XSim，因此上述项目均保持“待验证”。

## 3. 上板

只有门禁通过的位流才能下载。以 40 MHz 为例：

```bat
board\scripts\program_soc.bat build\run\soc_40mhz\pynq_z2_soc_40mhz.bit
```

`PROGRAM PASSED` 只证明配置成功；必须实际观察 `LED[3:0]=1101`，并记录 commit、
频率、Vivado 版本、板卡连接和照片/日志，才能写“v1 已上板”。125 MHz 同理使用
`build\run\soc_125mhz\pynq_z2_soc_125mhz.bit`，前提是该档所有门禁通过。

## 4. 不得改写的结论

- 原始“仅转发 ≥25%”门禁 FAIL，实测收益 8.14%；历史记录保留。
- Radix-4 工作点转发收益 10.20%，固定转发的乘法收益 21.95%，组合收益 28.30%。
- 功能仿真通过不等于时序通过，生成位流不等于已上板。

## 5. 2026-10-06 Part C PC/flush 降深度交接（保留三级）

起点 HEAD：`3c6b794`；理解门槛已通过，本轮未提交，验收 commit 待实际提交后填写。
代码指纹与原始日志：`data/logs/2026-10-06-partC-pc-depth/`，以 source_manifest.json
及 all.log/all.exit.txt、all-unsandboxed.log、all-final.log/all-final.exit.txt
绑定实际测试源码；分别保留沙箱 socket 失败、中断及最终完整重跑。
不能将起点 HEAD 当作优化后版本。
最终 `bash sim/scripts/run_iverilog.sh all` 退出码 0，全量 PASS；独立核对源码指纹、
四档 cycles/retired/CRC、分类统计和 BHT 三事件均匹配原锚点。续工入口见
`docs/partC-pc-depth-resume.md`；理解门槛于 2026-10-07 已 3/3 通过，完整答案见本轮
llm_log。尚未 commit/push；下一项为验证线 Vivado 复测。

改动：core_top 展开互斥的预测/恢复选择；ID+EX 直接拼接 B 立即数，独立产生目标
与目标后继；IF flush 只清 valid，不把原始指令强制换成 NOP。没有新增流水寄存器，
外部端口、BHT 状态机、muldiv 握手、DMEM 接口保持原约定。
新增 pc_control/if_stage 单独入口，补 B 全偏移地址与无效槽零副作用断言，均加入 all。

优化前时序来自用户转述验证线：BHT2 @11.520 ns，WNS=-0.334 ns，17 级路径
instr_hold_reg[5] -> pc_reg[27]，Data Path=11.860 ns，logic/route=33.4%/66.6%。
该实点 FAIL 保留；优化后 Vivado WNS 未验证。本机无 Vivado，交验证线按同法复测。

从仓库根目录执行（Windows 的 Vivado 路径沿用 §2）：

```bat
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top pcdepth_bht2_11p52ns 11.520 -core_profile bht2 src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top pcdepth_nofwd_10ns 10.000 -core_profile nofwd src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top pcdepth_fwd_10ns 10.000 -core_profile fwd src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top pcdepth_bht1_10ns 10.000 -core_profile bht1 src/riscv
vivado -mode batch -source build/build_fmax.tcl -tclargs core_top pcdepth_bht2_10ns 10.000 -core_profile bht2 src/riscv
```

首要判据：BHT2 在 11.520 ns 实跑 WNS≥0。报告存各自标签目录；记录实际约束点、
WNS、路径起终点、logic levels、logic/route 比例与 LUT/FF/BRAM。100 MHz 未过仍保留
FAIL，不能将 slack 外推 Fmax 当作最高通过点。PC 控制变浅可能增加扇出/布线，
独立目标后继可能增加 LUT；功能等价不能保证物理实现一定更快。
复测四档功能与统计；不将历史 40 MHz SoC 的 PASS 代替此次核 OOC 门禁。
