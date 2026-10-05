# Part B RTL 提交与验证交接单

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
