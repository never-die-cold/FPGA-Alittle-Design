# 2026-10-27 早晨执行单：上板 → 真权重 → 相机

> 状态：历史快照（2026-10-27 晨检单，执行窗口已过）；§5 禁止事项仍然有效。
> 用途：板卡上电后按此顺序执行，一次只做一件事，失败即停。
> 背景与根因见 `data/logs/2026-10-26-board-gate566b/README.md`。

## 0. 上电前检查（30 秒）

- 板卡电源、网线（本机 `192.168.50.1/24`）、SD 卡在位；
- 本机网口状态：`Get-NetIPAddress | Where IPAddress -like '192.168.50*'`；
- 板卡启动后 `ping 192.168.50.99` 通、22 端口可连（约 60 s）。

## 1. 健康检查（决定今天走哪条路）

```bash
sudo -E /usr/local/share/pynq-venv/bin/python3 \
  payload/tools/cop_board_fast_run.py --package /home/xilinx/cop-pkg-imem-20261026 \
  --case zero --measurement /tmp/health-zero.json --timeout 30
```

- **PASS**（class 2 / margin 2 / score 258）→ 板子健康，直接进第 2 步；
- **超时** → 停手，不重试；今天放弃板端 DMA，走第 4 步的降级演示，同时把问题交 JL
  （很可能就是 `pynq_cop_top.v` 里那份 `dma_start` 上升沿改动的方向）。

## 2. 真权重（今晚已备好，只换 payload）

```bash
sudo -E /usr/local/share/pynq-venv/bin/python3 \
  payload/tools/cop_board_fast_run.py --package /home/xilinx/cop-pkg-trained566b \
  --case roi_001 --measurement /tmp/trained-roi001.json --timeout 30
```

判据：`class 2 / margin 53 / score 6837 / logits -12,-30,41`。
这一发过了，就说明"训练权重在自研硬件上出结果"，是今天最重要的一条证据。

## 3. 连续性与第二类

- `--case frame`（期望 class 0）确认同一份权重对不同输入有区分；
- 若第 2、3 步都会在不同 case 间挂死：记录"一次上电一次检查"，把 Overlay 重载写进演示脚本
  （每个 case 独立进程，本身就会重下位流）。

## 4. 相机链路（不依赖第 2 步是否 PASS）

1. 用 C01/base overlay 抓一帧真实相机 PNG（10/17 已跑通）；
2. 裁一个 64×64 ROI，套 `roi_preprocess.preprocess(mode="border")`；
3. 走 `sim/scripts/export_trained_payload.py` 同样的量化，把该 ROI 的 INT8 写进 golden case；
4. 板端跑该 case → 得到"真实相机图像 → 自研硬件 CNN"的结果。

## 5. 禁止事项（今晚已经踩过）

- 不要用 `cop_payload_loader.py clock/run`（会 pulse SLCR `FPGA_RST_CTRL`，本板回读为 0，
  可能连带复位 FCLK0/AXI，已两次把 PS 挂死）；
- 不要把 `.xsa` 放在 `.bit` 同目录（PYNQ 会把它当 XSA 解析并失败）；
- 不要指望 `Overlay(download=True)` 重配同一位流（它是空操作）；
- DMA 超时后**不要重试**，直接记录并断电。

## 6. 需要 JL 侧并行推进

- 用 `pynq_cop_top.v` 的 `dma_start` 上升沿改动出一版**干净构建**的 bit（WNS/IMEM 门禁照跑）；
- 若该版本能在不挂死的情况下连续跑多笔，今天的演示就可以省掉"每 case 重下位流"。
