# 协处理器板端 40 MHz 时钟 runbook

> 状态：历史快照（直连改钟方案已被片内 MMCM 方案取代，见 data/logs/2026-10-27-startup-clock-repair/ 与 plan.md §3.1）；「JTAG 后 FCLK1 仍 142.857 MHz」「JTAG≠PS7 初始化」两节仍有效。本地产物路径已迁 others/build/。
> 2026-10-27 现况：本页下方为旧直连时钟方案；同名 edge 包现已替换成 MMCM 版，不能原样执行其中的改钟/上板命令。
> 先阅读[并发会话审计](runbooks/concurrent-agent-audit-2026-10-27.md)，核对 bit 哈希、时钟拓扑和 loader 配套关系。

> 当前板级功能状态仍为 **UNVERIFIED**。Windows Vivado 2026.1 整机门禁已随新源码于 2026-10-26 复跑
> PASS（edge-fix bit `9341F7FA…`，WNS +3.062 ns，见 `data/logs/2026-10-26-build/README.md`）；
> 门禁通过不等于板级验收。

## 2026-10-26 冷启动补充（edge-fix）

- 冷板/重启后 PL 未配置，PYNQ Clocks 找不到 device：cop_fclk.py 会报 No Devices Found
  （B 已复现，见 data/logs/2026-10-26-board/b4-fclk-set-40.txt）。
- 修正顺序：
  1. 先由用户/队友 JTAG 烧 edge-fix bit（PL 配置、PYNQ device 出现）。
  2. 跑 loader clock：

~~~bash
sudo -E /usr/local/share/pynq-venv/bin/python3 payload/tools/cop_payload_loader.py clock --package . --reads 20 --smoke-timeout 2
~~~

     它内含 FCLK1=40、重载 PL、FCLKRESET1、20 次首读。
  3. 再跑 zero/pattern、roi_001/frame。
- 若坚持用 cop_fclk.py：必须在已有 PL/device 后 set，再 JTAG 重载 bit，再跑 loader clock。
- 板卡 mmc0/SDHCI 报错时先恢复 SD/电源，不要继续烧写；现场卡见
  data/logs/2026-10-26-board/USER-ACTIONS.md。
- edge-fix bit 9341F7FA...；包 build/board-package-edge-fix 与 -trained；
  证据 data/logs/2026-10-26-build/README.md。

## 为什么 JTAG 后仍是 142.857 MHz

JTAG 下载 `.bit` 只配置 PL，不执行 XSA 中的 PS7 初始化，因此不会把 PS 产生的 FCLK1 改成
设计门禁使用的 40 MHz。NC 已实测 JTAG 成功且只读预检可用，但 FCLK1 为 142.857 MHz；
在读回确认 40 MHz 前，禁止写“40 MHz 板级通过”。

NC 已复现：FCLK1 改成 40 MHz 后，旧 PL 上连续 20 次 STATUS 仍为 `0x00000000`；保持时钟不变
重新配置 PL 后，20 次全部为 `0x00000001`。因此 `0x0` 只表示 cop 域未就绪、处于复位态或已因
改钟失效，**不能**再解释成“超频”。唯一允许的运行时顺序是：改 FCLK1 → 重新配置 PL → 等
PL done/时钟稳定 → 脉冲 FCLKRESETN1 → 首读校验；任一步未完成都禁止访问 COP MMIO。

## 路径 A：PYNQ Linux 运行时改钟（本轮首选）

解包新 NC 包、核验 `SHA256SUMS`，在板上包目录执行：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --package . --reads 20
```

该命令先写 `Clocks.fclk1_mhz = 40.0`，再用包内相邻的 `.bit/.hwh` 创建 fresh `Overlay`，确认
`is_loaded()` 后等待稳定；随后按 UG585 对 SLCR `FPGA_RST_CTRL` bit1 先置 1 再清 0，复位
`cop_rst_n_i` 对应的 FCLKRESETN1。只有此后脚本才建立 COP MMIO。合格证据必须同时包含：

- `board_sequence=set_fclk,reconfigure_pl,wait_stable,pulse_fclkreset1,status_check`；
- `measured_fclk1_mhz=40.000000`；
- `status_first_reads=` 后 20 项全部为 `0x00000001`；
- 两秒内出现 `firmware_smoke=PASS`；否则输出 `firmware_smoke_timeout_dump` 并失败。

`run` 命令也会在任何 COP MMIO 前完整重做同一序列，避免人工停顿耗尽固件等待期限。仅改钟而
未重配时，状态守卫报 `CLOCK_SEQUENCE_INCOMPLETE`；若重配后仍读到 `0x0`，报 `COP_NOT_READY`，
不得继续 DMA/START。命令只打印实测值，不宣告板级 PASS；掉电或 PS 重启后必须重做。

## 路径 B：由 XSA 生成 FSBL + bit 的 BOOT.BIN

工具固定为 **Vitis/XSCT/Bootgen 2026.1**，必须与 Vivado 2026.1 生成的
`pynq_cop_40mhz.xsa` 同档。下面在 AMD 2026.1 Command Prompt 中执行，路径按实际仓库替换：

```text
xsct
xsct% setws D:/boardtop/boot-work
xsct% app create -name fsbl -hw D:/repo/build/run/pynq_cop_40mhz/pynq_cop_40mhz.xsa -os standalone -proc ps7_cortexa9_0 -template {Zynq FSBL}
xsct% app build -name fsbl
xsct% exit
```

新建 `D:/boardtop/boot-work/pynq-cop.bif`：

```text
the_ROM_image:
{
  [bootloader] D:/boardtop/boot-work/fsbl/Debug/fsbl.elf
  D:/repo/build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit
}
```

生成并复核：

```bat
bootgen -arch zynq -image D:\boardtop\boot-work\pynq-cop.bif -o D:\boardtop\boot-work\BOOT.BIN -w on
certutil -hashfile D:\boardtop\boot-work\BOOT.BIN SHA256
```

SD 卡第一分区必须是板卡现有的 FAT 启动分区。断电、取卡，在 PC 上先把原 `BOOT.BIN` 复制为
`BOOT.BIN.known-good` 并记录 SHA256，再把新文件以 `BOOT.BIN` 放到分区根目录；其余文件不动。
重新上电后仍须按路径 A 读回 FCLK1 和 20 次 STATUS，不能从文件名推断时钟。

重要限制：上面的两分区 BIF 只含 FSBL 与 bit，不含 U-Boot，因而不能单独启动 PYNQ Linux/Python。
它适合验证 PS7 初始化与 PL；若要在同一启动链运行 loader，必须由 JL 使用**当前板卡镜像精确匹配**的
U-Boot/启动文件生成完整启动链，不能随意混用另一 PYNQ 镜像。当前实际跑 loader 应使用路径 A。

## 回滚

关机并断开 USB/JTAG 电源，取出 SD 卡，把 `BOOT.BIN.known-good` 恢复为根目录 `BOOT.BIN`，
再次核对备份 SHA256 后开机。若启动分区已损坏，换回事先保留的原始 SD 卡镜像；不要覆盖唯一备份。
回滚后记录镜像哈希、FCLK1 读回值和 STATUS 序列，BOARD 仍保持 UNVERIFIED。
