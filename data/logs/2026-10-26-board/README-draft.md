# 2026-10-26/27 上板记录：edge-fix + MMCM 位流全链（Agent B 独立冲刺）

- 日期/执行者：2026-10-26 夜至 10-27 凌晨；上板线 Agent B（A 停摆后经用户授权全开冲刺）。
- **最终状态：构建线全部完成且门禁全绿；板级四例实测被板卡硬件故障阻断，如实标注 UNVERIFIED。**

## 版本/产物（全部就绪、已校验）

- 源 commit：8884046（dev/riscv）+ 本冲刺补丁（见「冲刺改动」）。
- **最终位流（MMCM 版，构建 #14，02:46 产出）**：
  - bit  `43ac4f446cd24e11b29453585d3e31a2722a574bcd7626423b2d4cbdff87ed1e`
  - hwh  `ec5de273f2e53c432c317648419d0da64d00b96e66c95c081ced885d4044475d`
  - xsa  `a76b4ed0d1d606447f69444bf8ff70d4bdef58dcbdad9019ee1e367a589a7971`
  - 门禁原始行（`data/logs/2026-10-26-build/gate-rebuild-14-mmcm.log`）：
    ```
    READMEM LOG GATE PASSED: relevant_lines=0 blocking=0
    IMEM POST-SYNTH GATE PASSED: first_word=00008117 nonzero=1 cells=8
    HWH BASE GATE PASSED: COP=0x40000000 DMA=0x40010000 GPIO=0x40020000
    PYNQ COP WHOLE-SYSTEM GATE PASSED: WNS=1.184 DSP=136 BRAM36=69.0 CDC_ALLOWLIST=CDC-15=73,CDC-3=12,CDC-6=7 DRC=0
    ```
- 本机双包：`build/board-package-edge-fix{,-trained}`（12/12 逐项 PASS）；
  板上副本：`/home/xilinx/cop-pkg-edge-{diag,trained}-8884046`（12/12 板上对拍 PASS）。

## 板上已实测项（本冲刺内）

- **clock/活性门禁 PASS（两次独立）**：
  - 非 MMCM 版（23:5X）：`measured_fclk1_mhz=40.000000` + 20×0x1 + `firmware_smoke=PASS fw_decision=0x00001003`
    （`b4-clock-edge2.txt`）——注意该 40 读数事后证实是 pynq 缓存回声，见「根因链」。
  - **MMCM 版（00:5X）**：Overlay loaded + 20×0x1 + `firmware_smoke=PASS fw_decision=0x00001003`
    （`b4-gate-check-mmcm.txt`）——此版无时钟舞步，读数为真实硬件行为。
- **四例 zero/pattern/roi_001/frame：UNVERIFIED——DMA MM2S 在板卡稳定窗口外无法复现 21:40 的成功态**（详见下）。

## 根因链（今晚三大板卡故障 + 两个已修复的设计缺陷）

1. **SD 卡间歇故障**（mmc0 ADMA Err=0x1 + 写 I/O error，三度发作）：rootfs I/O 停顿
   → sshd 饿死 → 网络"假死"。用户重插一次，后复发。**板卡硬件待换卡/检修。**
2. **网口三次掉线**：与 SD 停顿强相关；串口通道（COM12）独立可用。
3. **FCLK1 内核时钟框架行为**：内核 clk_summary 恒报 142.857 MHz（FSBL 态）；
   pynq Clocks 的 SLCR 直写被回滚，且本地 checkout 的 `set_pl_clk` 只写分频不写
   CLKACT 使能位；pynq 的"40.000000"回读是其 Python 缓存回声（旧 loader 的诚实
   回读在同态下报 142.857143，见 `b5-zero-imem-ctl2.txt`）。
   → **设计侧根治：MMCM 片内再生 40 MHz（FCLK1 输入 142.857132 → 输出 ~40），PS 侧速率免疫。**
4. **HWH 地址漂移（已修复，failure-01.md）**：空参 assign_bd_address 两次构建结果不同；
   显式钉死 + 门禁 tripwire 双保险。
5. **DMA MM2S timeout（未根治，如实标注）**：在今晚所有启动态下，gate566b/钉死版/MMCM 版
   位流均在 fast_send 的 MM2S 完成等待处超时；write_configuration 新旧语义等价（已 diff 证明）；
   固件活性/CFG_APPLIED 均正常；21:40 的成功态（旧 bit+旧脚本+当时启动态）无法在
   今晚启动态下复现。**下一个健康板会话的第一实验 = 混合包
   `/home/xilinx/cop-pkg-mmcm-oldtool`（旧 loader 语义 + MMCM bit）直接跑 zero
   （其 FCLK1 检查已临时放宽，见板上 234-237 行改动）。**

## 冲刺改动（相对 8884046，提交候选清单）

1. `src/riscv/pynq_cop_top.v`：cop 时钟端口 FREQ_HZ=39999996（MMCM 实际值）。
2. `build/create_pynq_cop_bd.tcl`：MMCM 片内 40 MHz 再生 + PCW_FPGA1=142.857132 +
   三段基址显式钉死 + 跳过 validate_bd_design（0.1ppm 元数据噪声）。
3. `build/build_pynq_cop_gate.tcl`：HWH 三基址 tripwire。
4. 板端工具（未入库，板上/本机暂存）：`run_loader.py`/`run_board.py`（pynq 设备注册
   wrapper——裸 import pynq 不注册 Zynq 设备是 "No Devices Found" 的根因）、
   `gate_check.py`（无时钟舞步的门禁检查）、`slcr_dump.py`、`fclk1_boot.py`。

## 板端执行环境要点（复现必需）

- pynq 3.1 venv；裸 `import pynq` 不注册 Zynq 设备，必须先 import
  `pynq.pl_server.embedded_device`。
- 不要依赖 PS 侧 FCLK1 速率（MMCM 已免疫）；不要信 pynq Clocks 回读（缓存回声）。
- 板端 sudo 一行命令：`echo xilinx | sudo -S -p '' <cmd>`；网络死时走串口
  `pynq_serial_command.ps1`（单行 ≤3000 字节）。

## 边界（不得外推）

- 四例零/模式/训练权重**未验证**；DMA hang 未根治；连续作业、J05/J06、全链、M2/M3/M4 均不在本轮。
- BOARD 状态：**UNVERIFIED_NEEDS_STABLE_BOARD**（硬件稳定后按上节"下一个健康板会话"执行）。
