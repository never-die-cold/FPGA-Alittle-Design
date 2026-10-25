# 协处理器板端 40 MHz 时钟 runbook

> 当前板级功能状态仍为 **UNVERIFIED**。Windows Vivado 2026.1 的 40 MHz 整机门禁 PASS，
> 不等于 PYNQ 板上 FCLK1 已运行在 40 MHz，也不等于板级验收。

## 为什么 JTAG 后仍是 142.857 MHz

JTAG 下载 `.bit` 只配置 PL，不执行 XSA 中的 PS7 初始化，因此不会把 PS 产生的 FCLK1 改成
设计门禁使用的 40 MHz。NC 已实测 JTAG 成功且只读预检可用，但 FCLK1 为 142.857 MHz；
在读回确认 40 MHz 前，禁止写“40 MHz 板级通过”。

当前待验证假设是：142.857 MHz 超过本设计 40 MHz 门禁条件，时序违例使每组命令首次 STATUS
读到复位值 `0x00000000`，后续才读到 `0x00000001`。判据不是“后一次正常”，而是切到 40 MHz
后连续 20 次重新映射并首次读取 STATUS 均为 `0x00000001`（READY=1、BUSY=0）。若 40 MHz
仍出现 `0x0`，不要改 RTL；先沿“复位释放到首次 AXI 访问的同步延迟”采集连续读数和 ILA 波形。

## 路径 A：PYNQ Linux 运行时改钟（本轮首选）

解包新 NC 包、核验 `SHA256SUMS`，在板上包目录执行：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20
```

该命令执行等价于 `Clocks.fclk1_mhz = 40.0`，随后读回 `Clocks.fclk1_mhz`，并为每个样本
重新建立 COP MMIO 映射后读取一次 STATUS。合格证据必须同时包含：

- `measured_fclk1_mhz=40.000000`；
- `status_first_reads=` 后 20 项全部为 `0x00000001`。

命令只打印实测值，不宣告板级 PASS。掉电或 PS 重启可能恢复启动镜像的时钟配置，届时必须重做。

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
