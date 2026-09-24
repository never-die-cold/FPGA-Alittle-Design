# Part A SoC 与真实上板决策记录（2026-09-23）

## 背景

Part A 已完成 RV32IM 核、32KB IMEM/DMEM 和可复现回归，但 `soc_top.v` 仍是空壳。此前 PYNQ-Z2 流水灯已真实下载，只能证明板卡、JTAG 和 LED 链路可用，不能证明 RISC-V SoC 已上板。

本阶段拆成 10A 仿真 SoC、10B 板级时钟与约束、真实下载验收三段。仿真 PASS、Vivado 实现 PASS 和生成 bitstream 都是前置证据；只有 bitstream 下载到 PYNQ-Z2，并观察到约定 LED 结果，才能标记“已上板”。

## 冻结决策

1. `soc_top` 外部接口固定为 `soc_top(clk, rst_n, led)`，内部例化 `core_top`、`imem`、`dmem`。
2. 本阶段 SoC 固定预载 RV32I `src/riscv_fw/hello_v0.hex`。该程序写 `tohost=13`（`0xD`），所以 LED 期望为 `4'b1101`。RV32IM `hello.hex` 的 `tohost=142879`、低四位 `1111`，继续保留为整核回归，不作为本次板上 LED 镜像。
3. LED 不是运行灯：复位时清零；每当核在 `0x8000_3FF0` 写 DMEM，就在同一写入沿锁存 `dmem_wdata[3:0]`，之后保持。这样 LED 直接反映最后一次 `tohost` 写入的低四位。
4. PYNQ-Z2 板载 PL 时钟为 125 MHz（H16），高于 v0 已归档的 86.8 MHz Fmax。板级顶层使用 MMCM 产生 40 MHz 安全核时钟，并在锁定前保持 SoC 复位。125 MHz 直连核被禁止，留作 Part B 提频目标。
5. Vivado 必须检查 125 MHz 输入时钟、40 MHz 派生时钟、未约束路径、WNS 和资源。WNS 必须不小于 0，报告存入 `build/reports/`。
6. 上板记录只追加到 `board/logs/`，必须包含源码 commit、bitstream 路径与哈希、连接方式、Vivado 版本和实际 LED 现象；实测指标再同步到 `data/metrics.csv`。

## 当前环境事实

- WSL 的 `PATH` 中没有可直接调用的 `vivado` 或 `xsim`。
- Windows Vivado 2026.1 启动器存在于 `D:\Vivado\2026.1\Vivado\bin\vivado.bat`，WSL 可找到 `cmd.exe`，但直接执行会报 `Exec format error`；Vivado 构建由用户在 Windows PowerShell 中运行。
- 本记录创建时，新的 RISC-V SoC 尚未综合、生成 bitstream 或下载；该历史快照由后文 2026-09-25 实现结果接续，真实下载前仍不得写作“已上板”。

## 后续顺序

先实现并回归 `soc_top`，再加入 40 MHz MMCM 板级顶层、XDC、构建和下载脚本；通过理解门槛并形成可追溯 commit 后，构建对应 bitstream、JTAG 下载并人工核对 LED=`1101`，最后追加板上证据与指标。

## 2026-09-25 实现反馈与修订

50 MHz 首次有效实现的 WNS 为 -0.956 ns；改用 `Explore` 后改善为 -0.214 ns，但仍有 15 个 setup 失败端点，因此构建门禁正确阻止了 bitstream 生成。板级安全核时钟下调为 40 MHz：MMCM 保持 1000 MHz VCO，输出改为 `125 × 8 ÷ 25`，约束周期改为 25 ns。该调整只增加时序裕量，不改变 SoC 功能；是否收敛仍以重新运行 Vivado 后 WNS≥0 为准。

## 10B-4b：40 MHz 调整理解检查

1. 用户正确计算：VCO 为 `125×8=1000 MHz`，输出为 `1000÷25=40 MHz`；只调整输出分频，不改变 VCO。
2. 用户正确说明：RTL 与 XDC 不一致会让时序分析失真；`require_clock core_clk_40 25.000` 会拦截时钟缺失、名称错误或周期错误。
3. 用户正确区分：Icarus 只验证功能，Vivado 实现报告验证 WNS，实际下载并观察 LED 才能证明已上板。

判定：三题全部通过，可以进入 40 MHz Vivado 实现复跑。

## 2026-09-25：40 MHz Vivado 实现结果

- 工具/器件：Vivado 2026.1，`xc7z020clg400-1`；输入 `sys_clk_125=125 MHz`，核时钟 `core_clk_40=40 MHz`。
- 时序：setup WNS=+0.142 ns、TNS=0，hold WHS=+0.071 ns、THS=0；无时钟、常量时钟、未约束内部端点和断开的派生时钟均为 0。按本次 slack 粗略折算的极限约为 40.23 MHz，不替代频率扫描实测。
- 资源：6267 LUT（11.78%）、408 FF（0.38%）、8 RAMB36（5.71%）、0 DSP；其中 DMEM 异步读推断为 4140 个分布式 RAM LUT。
- DRC：0 Error、0 Critical Warning；保留 22 个普通 Warning，其中 20 个 `REQP-1839` 来自异步复位寄存器驱动只读 IMEM BRAM 的地址/使能，1 个 `CHECK-3` 为报告数量提示，1 个 `ZPS7-1` 来自纯 PL 设计未例化 PS7。警告不隐藏，最终以 JTAG 下载和 LED 观察验证。
- 位流：`build/run/soc/pynq_z2_soc.bit`，4,045,766 bytes，SHA-256 `d81cb8cf1837f6845bb2be73e4e54a1d9c211f2f3b5e781a32e98928f4d9a044`。
- 当前状态：实现与 bitstream 生成通过；尚未下载到 PYNQ-Z2，仍不得标记“已上板”。

## Commit 前最终理解门槛

### 逐段讲解

1. `soc_top.v` 例化 `core_top`、IMEM 和 DMEM。程序写 `0x8000_3FF0` 时，只有 `dmem_we=1` 才把 `dmem_wdata[3:0]` 锁存到 LED；读同一地址不会误更新显示。
2. `pynq_z2_top.v` 用 MMCM 将 H16 的 125 MHz 输入变为 40 MHz。MMCM 未锁定或 BTN0 按下时立即复位；锁定后复位经过两拍同步释放，避免寄存器在不同时刻离开复位。
3. XDC 同时约束 125 MHz 输入和 40 MHz 派生时钟，只对异步按钮与人眼观察的 LED 设置 false path；核内部同步路径全部参与分析。
4. 构建 Tcl 在综合和布局布线后检查两个时钟、未约束端点、WNS 与 Error/Critical Warning 级 DRC，全部通过后才生成 bitstream。
5. SoC testbench 同时检查完整 `tohost=13`、LED 低四位 `1101` 与复位清零；全量回归还覆盖 RV32I、RV32M、存储器和整核冒烟。
6. 下载脚本检查位流存在且非空，并按 `PART=xc7z020*` 唯一选择 JTAG 设备。下载成功只证明配置完成，必须实际观察 LED=`1101` 才能记录已上板。
7. 40 MHz 实现 WNS=+0.142 ns、WHS=+0.071 ns，bitstream 已生成。DRC 保留 22 条普通 Warning；它们已分类记录，没有伪装成“0 Warning”。

### 三道题与用户答案

#### 第 1 题

题目：从 `hello_v0.hex` 开始，程序结果经过哪些模块和信号，最终变成 LED=`1101`？为什么必须同时检查 `dmem_we` 和 tohost 地址？

用户答案：

> `hello_v0.hex` 经 `$readmemh` 预载到 IMEM，`core_top` 取指、译码并执行；程序 store tohost 时产生 `dmem_we=1`、`dmem_addr=0x8000_3FF0`、`dmem_wdata=13`。DMEM 保存结果，`soc_top` 同拍锁存低四位 `1101` 到 `led_q`。只看地址会让读取 tohost 的 `lw` 也触发并锁存无意义写数据，所以必须同时要求 `dmem_we=1`。

判定：通过。数据链和写使能语义均正确。

#### 第 2 题

题目：删除 `mmcm_locked` 控制或让复位异步释放会怎样？为什么 WNS 通过不能消除风险？

用户答案：

> 删除 `mmcm_locked` 会让核在 MMCM 输出尚未稳定时运行，可能执行错指令、状态混乱或死机。异步释放可能违反建立/保持时间，引发亚稳态和寄存器不同步醒来。WNS 假设时钟稳定且复位已正常释放，只分析正常工作数据路径，不覆盖上电锁定和异步释放问题。

判定：通过。正确区分了静态时序与时钟/复位启动风险。

#### 第 3 题

题目：已有 WNS 合格的 bitstream 为什么还不能记“已上板”？`PROGRAM PASSED` 后还缺什么？为什么必须保留 22 条普通 Warning？

用户答案：

> 当前只完成实现与 bitstream 生成，还没有下载或观察 LED。`PROGRAM PASSED` 只证明 FPGA 配置成功，仍需在真实 PYNQ-Z2 上看到 LED=`1101`，并记录板卡、commit、位流和照片/日志。普通 Warning 虽不拦门禁，但是真实设计证据，必须披露并解释，尤其 `REQP-1839` 反映异步复位驱动 BRAM 的设计事实。

判定：通过。正确区分了位流、配置和功能上板三类证据。

### 总判定

三题全部通过，用户已理解本次 SoC 外壳、板级时钟/复位、约束、构建门禁和上板证据要求，允许进入 git commit；真实上板状态仍保持未完成。
