---
name: pynq-z2-bringup
description: Use when bringing up a PYNQ/Zynq board for the first time, when JTAG programming fails, when pin constraints are missing or suspect, when the board clock does not match core Fmax, when planning the HDMI demo chain, or when writing bitstream download tooling. 通用 PYNQ 板级踩坑清单：XDC 只认官方溯源、JTAG 按 PART 选器件、MMCM 分频+锁定复位、视频硬限制先查文档、下载工具默认档=安全档。Trigger on 上板 / bring-up / JTAG / 引脚约束 / 位流下载 / HDMI 链路. Not for RTL microarchitecture or timing closure (see timing-closure-workflow).
---

# 通用 PYNQ 板级踩坑清单（pynq-z2-bringup）

一句话规则：**板级事实只从官方文档与实跑取证，不从记忆与教程取证；下载工具的默认档 = 已验证安全档，激进配置一律显式 opt-in。**
适用板卡：PYNQ-Z2（TUL Zynq XC7Z020）；方法对多数 Zynq-7000 板卡可迁移，引脚/时钟/视频 IP 细节需按新板官方文档重核。

## 踩坑清单（触发条件 → 排查步骤）

### 1. 引脚约束只能官方溯源

- **触发**：新板 bring-up、仓库里的 XDC 没有任何 `PACKAGE_PIN`/`IOSTANDARD`。
- **排查**：下载板卡官方 Master XDC（记录下载来源、经手人、**SHA256**），用板卡参考手册核对极性（PYNQ-Z2：LED 高有效、BTN0 按下为高、PL 时钟 125 MHz @ H16）；**严禁凭记忆或 AI 建议填引脚**。
- **加固**：独立复核时对官方 XDC 实算 SHA256 逐字节比对，不靠"文件名对"。

### 2. Zynq JTAG 链按 PART 选器件，不按 index

- **触发**：`get_hw_devices` 取 index 0 编程报 `Device arm_dap_0 is not programmable`——PS 的 ARM 调试口排在链上第一位。
- **排查**：遍历 `get_hw_devices`，按 `PART` 过滤 `xc7z020*` 后 `program_hw_devices`。
- **概念表**：SD 卡烧录 = 启动 Linux 系统；JTAG = 直接配置 PL（两者互不替代）。

### 3. 板载 125 MHz 不得直连低速核时钟

- **触发**：核 Fmax 低于 125 MHz 时直连，综合/实现 WNS 大负、构建门禁拦下。
- **排查**：板级顶层加 MMCM 分频（如 VCO 1000 MHz，125×8÷25=40 MHz）；`mmcm_locked` 未锁定即复位、复位两拍同步释放；XDC 同时约束输入时钟与派生时钟，仅按钮/LED 设 false_path。
- **仿真注意**：Icarus 无 Xilinx 原语——tb 内建 MMCME2_BASE/BUFG 桩并断言分频比与 VCO 频率。

### 4. 视频/外设硬限制先查官方文档，再定演示链路

- **触发**：按"常识"规划 HDMI 摄像头/1080p/USB 摄像头直插。
- **事实**（PYNQ-Z2）：DVI 前端仅支持 720p（流水线 142 MHz < 1080p60 的 148.5 MHz）、不支持 HDCP、无 USB 主机口；HDMI OUT 由 PL 驱动，不可能显示 Linux 启动日志。
- **排查**：演示链路定为 源设备 → HDMI IN → HDMI OUT → USB 采集卡回显；采集卡 50–200 ms 延迟显式声明**不计入**端到端指标（指标改板上计数器/GPIO 打点）。

### 5. 下载工具：默认档 = 最稳已验证档

- **触发**：构建产物分目录/分档演进后，下载脚本引用旧默认路径失效；或想"顺手"把新优化档设为默认。
- **排查**：默认位流指向当前已验证产物，显式传参仍优先；环境变量用 `if not defined VIVADO` 条件回退，**不覆盖用户配置**；Vivado 安装路径不硬编码（tcl 直调 + README 留痕）。
- **规则**：有上板证据只证明"能用"，不证明"该当默认"；默认档还是公平对比的锚点（对照档=默认档）。

### 6. Vivado GUI 仿真三坑

- `$readmemh` 相对路径按仿真运行目录（`<工程>.sim/.../behav/xsim`）解析，不是工程目录；
- 默认 runtime 1000 ns 跑不完长程序，设 `xsim.simulate.runtime=all`；
- 长构建别在 GUI 跑（易崩），用 `vivado -mode batch`；阻塞式长构建被超时中断后 Vivado 子进程会残留，`Get-Process vivado` + `Stop-Process` 清理。

### 7. 共用板约定与阻塞解除同步

- 一块板多人用：报备制度 + 每次实测留 commit hash / 接线 / 结果。
- 长期阻塞项（如"板卡未到货"）解除后：全库 grep 旧关键词（"未到货/顺延"）同步现状，历史记录只追加不改写。

## 已验证效果

- 冒烟工程 4 组分频仿真 PASS + 故意打乱用例 FAIL（门禁有效）；JTAG 按 PART 过滤后 `xc7z020_1` PROGRAM PASSED、LED 流水/按键实测通过；MMCM 40 MHz 档实现 WNS +0.142 / DRC 0 Error 并上板。
- 来源（`report/llm_log/`）：`2026-09-20-pynq-z2-smoke.md`、`2026-09-20-pynq-jtag-bringup.md`、`2026-09-20-pynq-z2-smoke-verification.md`、`2026-09-20-board-arrival-doc-sync.md`、`2026-09-20-demo-hardware-chain.md`、`2026-09-23-partA-soc-onboard.md`、`2026-10-05-rtl-pynq-z2-dual-clock.md`、`2026-09-26-partA-soc-onboard-verify.md`、`2026-10-09-soc-download-collaboration.md`

## 失效条件

- 换板卡/修订版：引脚、时钟频率、视频 IP、JTAG 链全部按新板官方文档重核，本清单只保留方法不保留结论。
- 用 PYNQ 官方 base overlay 做纯 Python 应用时不涉及自定义 XDC/位流条目。
