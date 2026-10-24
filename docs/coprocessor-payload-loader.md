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

## 当前位流的 fail-closed 阻塞

当前 HWH 明示 `C_SG_LENGTH_WIDTH=14`，Direct Register MM2S 单包最大 16,383 B，小于权重
payload 的 36,032 B。不能简单分三笔：每笔 DMA 都产生 TLAST，而 loader 会把第一笔判为短包。
因此脚本在任何 MMIO 写之前报 `DMA_LENGTH_BLOCKED`。这是当前包不能跑 pattern/zero 的独立阻塞，
不是 payload/CRC 错误；按本轮要求先不改 RTL/BD。

第二个待处理点是当前 `cop_job` 上电只检查一次配置：Python 建立 MMIO 前配置尚未就绪时，固件会
以 RECHECK 退出，不会等待后续 payload。即使未来把 DMA 单包长度调大，也要先由 JL 提供可等待任务
或可控重启的固件/位流；否则 loader 会如实报 `NO_ACK`，不得由 PS 越权写 START 绕过。

## 命令

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20
sudo -E python3 payload/tools/cop_payload_loader.py run --package . --case zero \
  --measurement ./zero-measured.json --timeout 10
```

当前第二条命令预期在零副作用预检阶段报告上述 DMA 能力阻塞。兼容位流到位后，同一 schema、
payload 和命令继续使用；pattern 将 `--case zero` 改为 `--case pattern`。

## 失败排查

| 现象 | 含义 / 下一证据 |
|:---|:---|
| `DMA_LENGTH_BLOCKED` | HWH 单包长度不足；禁止分包，记录 `C_SG_LENGTH_WIDTH`，交 JL 改 BD 后重走整机门禁 |
| `payload_error=1` | 提前/延后 TLAST、keep、长度或 manifest bank 适配拒绝；保存 STATUS、DMA status、DMA_BYTES |
| `start_ready` 不置或不返回 | 请求 CDC 未受理/未应答或 start 电平未及时拉低；记录 GPIO 两通道与 DMA_BUSY 波形 |
| `NO_ACK` | 固件没有发 START/ACCEPTED；先查固件是否在配置就绪前已退出，再查核复位与 mailbox |
| 终态软件超时 | ACCEPTED 后无 DONE/ERROR/TIMEOUT；保留 STATUS、ERROR_CODE、RESULT_SEQ，不写 CONSUME |
| CRC/SHA256/字节数不符 | 包或传输损坏；失败发生在预检时保证零硬件副作用，重新解包并核对 `SHA256SUMS` |
| 40 MHz 下首读仍有 `0x0` | 否定“仅超频”假设；采集连续读数与 ILA，转查复位释放/首次 AXI 访问同步延迟，暂不改 RTL |
