# 今晚现场操作卡（给用户/队友的手）—— 2026-10-26 edge 包上板

> B 线（本会话）已完成：B2 收包校验全绿（12/12+12/12），传输方案、执行手册、
> 判据全部就绪。**只差板卡恢复 + 下面两步手工操作。**

## 第 1 步：修 SD 卡（B2 之后发现的根因）

板卡 22:17 起网络瘫（ping 死、SSH kex 被重置）、串口刷
`mmc0: Timeout waiting for hardware interrupt` + `I/O error, dev mmcblk0 (WRITE)`
——SD 卡写 I/O 持续报错，rootfs 卡顿导致一切通道失灵。

操作：**断电 → 拔出 SD 卡 → 检查金手指/卡槽 → 重新插紧 → 上电**。
上电后**不要**运行任何测试，直接做第 2 步（或喊我，我先做串口健康检查）。

若重插后 dmesg 仍刷 mmc0 错误 → 卡体损坏，需换备份卡（重刷镜像由你拍板，agent 不自作主张）。

## 第 2 步：JTAG 冷启动烧新 edge bit

新 bit（含 dma_start 上升沿修复，WNS +3.062 / DRC 0 / IMEM_FIRST_WORD=00008117）：

```
E:\Projects\FPGA-Alittle-Design\build\board-package-edge-fix\payload\pynq_cop_40mhz.bit
SHA256 = 9341F7FA008C4A853767B2850701758E0534C923AED955B4B3B3F7E750BC4160
```

Vivado → Hardware Manager → Open Target → Program Device（xc7z020）→
Bitstream file 选上面那个 .bit → Program。
（PS 已在跑 Linux，只烧 PL；不需要 ps7 init。烧完板面 LED 应见配置完成态。）

> 为什么必须先 JTAG：重启后 pynq 无设备上下文，loader/Overlay 的 Clocks 调用会
> "No Devices Found"（B 已在板上复现，见 b4-fclk-set-40.txt）。JTAG 烧一次后
> device 出现，后续 loader 自管重载。
> **两个 agent 不得同时碰板**：让 A 的板上操作全部停止后再开工。

## 第 3 步之后（agent 自动执行，你不用动手）

我按 B3（传输+板上逐文件 sha256）→ B4（loader clock --reads 20 --smoke-timeout 2，
期望 40.000000 + 20×0x1 + 固件活性）→ B5（zero/pattern）→ B6（roi_001 + frame），
全部产物落 `data/logs/2026-10-26-board/`，实时回传给 A。

## 期望结果（全部 matches_expected=true）

| case | class | margin | score | logits | low_conf |
|:---|---:|---:|---:|:---|---:|
| zero | 2 | 2 | 258 | 2,-3,4 | 1 |
| pattern | 0 | 0 | 0 | 1,-3,1 | 1 |
| roi_001 | 2 | 53 | 6837 | -12,-30,41 | 0 |
| frame | 0 | 29 | 3741 | 34,-41,5 | 0 |

MODEL_ID：诊断 0x4A303250 / 训练 0x4A303251。
