# 协处理器最小 payload loader（J08-lite）

入口：`tools/cop_payload_loader.py`。它只接受 `kind=PROVISIONAL` 的 J02 诊断包，打印实测字段；
不会写“板级 PASS”，也不会把 `score_q15` 当概率。

## 地址与位定义

| 实例 | PS 物理基址 | 本轮用途 |
|:---|---:|:---|
| COP AXI4-Lite | `0x4000_0000` | 配置、STATUS、结果、消费写 |
| AXI DMA | `0x4001_0000` | Direct Register MM2S，64-bit stream |
| AXI GPIO `dma_control` | `0x4002_0000` | channel 1 发请求，channel 2 读状态 |

GPIO channel 1 bit0=`dma_start_ps_i`，bit1=`dma_kind_ps_i`（0 权重、1 ROI）；channel 2
bit0=`start_ready`，bit1=`payload_error`。`dma_start_ps_i` 是电平采样：ready=1 时写高会翻转请求，
软件必须紧接着写低；若一直保持高，在应答返回后会再次触发。`payload_error` 只有一拍，轮询只能
尽力捕获；持久判据还包括 STATUS、`DMA_BYTES` 和权重 CRC 形成的 `MODEL_VALID`。

## 实际时序

```text
校验包 SHA256/CRC/HWH/地址/单包长度（尚未触碰 MMIO）
  -> 确认 FCLK1 读回 40 MHz
  -> 写 shadow + CFG_SEQ，写 CFG_COMMIT，核对 CFG_APPLIED
  -> GPIO kind=0,start=1 -> 立即 start=0 -> 等 DMA_BUSY
  -> AXI DMA MM2S payload.bin -> 等 DMA idle、DMA_BUSY 清、start_ready 回来
  -> GPIO kind=1 同序列，MM2S 推 4096 B ROI
  -> 等固件 sticky ACCEPTED -> 等 DONE/ERROR/TIMEOUT
  -> RESULT_SEQ 前后复读；RESULT_INDEX=0 后读 META/LOGITS/SCORE/FW_DECISION
  -> 与 EXPECTED_OUTPUTS.tsv 对照，结果 JSON 成功落盘并 fsync 后才写 CONSUME
```

PS 不写 `CTRL.START`；当前冻结协议规定 START 由 RISC-V 固件发起。脚本有独立 NO_ACK 与终态
超时。pattern 预期 class/margin/score=`0/0/0`，zero 为 `2/2/258`，数值保持 J02 锚点。

## 16 位 Direct Register 长度门禁

BD 源码固定 `C_SG_LENGTH_WIDTH=16`，Direct Register MM2S 的 `MM2S_LENGTH[15:0]` 单包上限
65,535 B，可容纳 36,032 B payload；软件只在校验 HWH 同样为 16 后，才把长度按 16 位写入
`DMA_BASE+0x28`。当前实现保持单次 MM2S 传完整 payload，不执行分包；长度为 0 或超过
65,535 B 时在触碰 MMIO 前 fail-closed。2026-10-25 干净整机门禁产出的 HWH 已确认该字段为 16 位。

`cop_job` 源码现驻留等待：`CFG_APPLIED!=0` 且 CFG_VALID（即 `CFG_APPLIED==CFG_SEQ`）、
MODEL_VALID、DMA 空闲，并用 `DMA_BYTES==ROI_COUNT*4096` 区分 ROI 完成与前一笔权重完成；等待超时
仍按既有 CONFIG/RECHECK 退出。2026-10-25 干净门禁位流已包含该驻留固件；板上等待路径仍待
NC 验证，不得由 PS 越权写 START 绕过。

## 命令

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20
sudo -E python3 payload/tools/cop_payload_loader.py run --package . --case zero \
  --measurement ./zero-measured.json --timeout 10
```

loader 会在零副作用预检阶段拒绝非 16 位 HWH；当前门禁包使用同一 schema、payload 和命令；
pattern 将 `--case zero` 改为 `--case pattern`。

## 失败排查

| 现象 | 含义 / 下一证据 |
|:---|:---|
| `DMA_LENGTH_WIDTH_MISMATCH` | HWH 不是固定 16 位；核对是否仍加载旧 bit/hwh |
| `DMA_LENGTH_BLOCKED` | 当前单次传输实现的长度不在 1..65,535 B；先评审协议与 BD |
| `payload_error=1` | 提前/延后 TLAST、keep、长度或 manifest bank 适配拒绝；保存 STATUS、DMA status、DMA_BYTES |
| `start_ready` 不置或不返回 | 请求 CDC 未受理/未应答或 start 电平未及时拉低；记录 GPIO 两通道与 DMA_BUSY 波形 |
| `NO_ACK` | 固件没有发 START/ACCEPTED；核对 bit 是否含驻留固件，再查 CFG/MODEL/DMA_BYTES、核复位与 mailbox |
| 终态软件超时 | ACCEPTED 后无 DONE/ERROR/TIMEOUT；保留 STATUS、ERROR_CODE、RESULT_SEQ，不写 CONSUME |
| CRC/SHA256/字节数不符 | 包或传输损坏；失败发生在预检时保证零硬件副作用，重新解包并核对 `SHA256SUMS` |
| 40 MHz 下首读仍有 `0x0` | 否定“仅超频”假设；采集连续读数与 ILA，转查复位释放/首次 AXI 访问同步延迟，暂不改 RTL |
