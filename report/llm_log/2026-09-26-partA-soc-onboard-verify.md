# [2026-09-26] 协作记录：Part A SoC 上板独立验证（XSim 对拍 + 命令行构建 + JTAG 实测）与"复位后重跑"缺口

> 标签：#riscv #验证 #hardware #构建 #工具链
> 平台：OpenCode ｜ 模型：deepseek-flash
> 相关 commit：被测 `db9fe33`（`dev/rtl`）；证据 commit 为本条记录同一批
> 用途：验证线对 `2026-09-23-partA-soc-onboard.md` 所述 SoC 上板的**独立复现**；发现"BTN0 释放后重跑"契约/tb 缺口

## 1. 任务与初始提示词

> "我们的 git 仓库又更新了，我今天需要验证新的程序……从阅读队友写的待验证的程序到完成验证工作，再到上传今天我工作的成果。注意我的分支线从 dev/bench 改成 verify"

被测件 = `dev/rtl@db9fe33`（Part A SoC 上板准备与 40 MHz 时序收敛，新增 `soc_top`/`pynq_z2_top`/`tb_soc_top`/`build_soc.tcl`/`program_soc.*`）。该提交自述：仿真/构建通过，但**"尚未下载到 PYNQ-Z2，仍不得标记已上板"**。验证线职责：独立复现并完成真实上板。

## 2. 模型第一版方案

1. 读决策记录 + `design_v0.md` §5.6/§5.8 + RTL/tb/构建/下载脚本，产出验证判据（LED=`1101`、复位 `0000`、WNS≥0、DRC 干净）；
2. 独立跑 SoC 仿真（XSim）、独立构建（`build_soc.tcl`）、JTAG 下载（`program_soc.tcl`）、肉眼验收 LED；
3. 归档证据 + 写协作记录 + 提交 `dev/verify`。

## 3. 失败现象（真实偏差）

1. **本机无 iverilog/MSYS2、WSL 无发行版** → 无法用团队的 `run_iverilog.sh`；改用 **XSim**（Vivado 自带），正好与 RTL 线 iverilog 形成双工具对拍。
2. **GUI 行为仿真的固件路径坑**：`WARNING: File ../src/riscv_fw/hello_v0.hex ... can[not be found]`，且默认只跑 `1000ns`——tb 需要约 40081ns。原因：tb 相对路径只在"从 `sim/` 运行"时成立，而 GUI 仿真工作目录是 `<工程>.sim/.../behav/xsim`。
3. **Vivado GUI 跑 `build_soc.tcl` 连续两次崩溃/中断在综合阶段**，构建未完成（`vivado_<pid>.backup.log` 停在早期综合，未见新 bitstream）。
4. **上板现象偏差**：BTN0 释放后 LED = `0001`，而非回到 `1101`。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 本机无 iverilog | 用 Vivado 自带 XSim 替代，且跨工具对拍更独立 | 改用 `xvlog/xelab/xsim` | ✅ `PASS: tohost=13, LED=1101, reset LED=0000` |
| 2 | GUI 仿真报 hex 找不到 + 只跑 1000ns | 相对路径仅在 `sim/` 生效；GUI 运行目录不同；默认 runtime 太短 | 把 `hello_v0.hex` 拷到仿真运行目录对应位置（方式 A）；`xsim.simulate.runtime=all` | ✅ 仿真 PASS |
| 3 | GUI 构建两次崩溃 | 长时间非工程模式构建不适合 GUI（会连累构建） | 改用命令行 `vivado -mode batch -source build/build_soc.tcl` | ✅ `BUILD PASSED, WNS=+0.142ns` |
| 4 | BTN0 松开 LED=`0001` | 非 RTL bug：固件用 `tohost` 当种子（`sum=4*seed+13`），软复位不清 dmem、`tohost` 不在 `.bss` → 第二次 `seed=13`、`sum=65`、低 4 位 `0001` | 复核实测可重复 + 断电复位回 `1101`，确认为契约/tb 未覆盖 | ✅ 行为可解释、可复现 |
| 5 | 是否算验证通过 | 主判据（下载后 LED=`1101`）达成；`0001` 属未定义场景 | 判定**上板 PASS**，并将缺口记为发现反馈 RTL 线 | ✅ |

## 5. 最终结论

- **独立验证通过**：
  - 仿真（XSim）：`PASS: SoC tohost=13, tohost_exit=0, LED=1101, reset LED=0000`；
  - 构建（Vivado）：`BUILD PASSED`，WNS +0.142 / WHS +0.071，0 Error/0 Critical Warning，LUT 6267 / FF 408 / RAMB36 8 / DSP 0；
  - 上板：`PROGRAM PASSED`，LED=`1101` 静止，复位 `0000`。
  - 本次下载位流 SHA256 `8D28219B…E53E71C`，405 万字节。
- **验证发现（非阻塞）**：BTN0 释放后重跑的 LED 期望**未在契约/tb 中定义**（现象 `0001` 可由固件语义解释）。建议 RTL 线：tb 增加重跑期望 / 契约写明 / 复位时一并清 `tohost`。
- 证据归档：`data/logs/2026-09-26-soc-onboard/`（含 `reports/`、`sim_xsim.log`）；上板记录 `board/logs/2026-09-26-soc-onboard/README.md`。
- 上板下载走 Vivado **Hardware Manager（GUI）**（等价脚本 `board/scripts/program_soc.tcl`）；归档时板卡已断开，未重抓命令行下载日志，以板上 LED 现象为判据。

## 6. 经验沉淀

- 触发条件：独立验证队友的"仿真+构建已过、真实上板未做"类硬件提交 #skill候选
- 排查步骤：
  1. **跨工具对拍**：本机缺 iverilog 时用 XSim，结论一致即增强可信度；
  2. **GUI 行为仿真的相对路径坑**：`$readmemh` 相对路径按仿真运行目录解析，不是源文件目录；把初始化文件放到运行目录对应相对位置，并把 runtime 设为 `all`；
  3. **长构建用批处理**：非工程模式综合/实现别在 GUI 里跑，`vivado -mode batch` 更稳（GUI 崩了会连累构建）；
  4. **"省电/软复位后重跑"要单独验**：软复位通常不清数据存储器（本例 dmem），凡有"用自身状态当输入"的固件，重跑结果会变——不能只看首次结果就判全过。
- 适用范围（换题目/换板卡是否成立）：成立；任何"仿真通过但需真实上板确认 + 软复位/重跑行为"的验证场景均适用。
