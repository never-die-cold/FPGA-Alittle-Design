# 2026-10-25 DMA16+驻留固件合并后的离板门禁

> 基线：`dev/exe` @ `41ff893` + JL `origin/dev/riscv` `0aecf97`（合并 `70bdec6`）。
> 结论：合并 JL 的 DMA 16 位、驻留固件、`tools/cop_payload_loader.py`、干净门禁包记录后，
> 6 个关键离板模式全部 exit 0。

## 结果

| 模式 | 退出码 |
|---|---:|
| `firmware_e2e` | 0（驻留固件：等 CFG/MODEL/ROI 后 START→ACCEPTED→终态→FW→CONSUME） |
| `decision_ab` | 0 |
| `pynq_top` | 0（100/40MHz AXI-Lite 读 COP_ID；cop_job.hex 已参与 elaborate） |
| `manifest_v1` | 0 |
| `payload_network` | 0（manifest→DMA→shadow BRAM→atomic activate，bytes=36032 crc32=2f760211） |
| `bram_network` | 0（pattern/zero 各 73,795 元素，cycles=472594） |

原始日志与退出码在本目录。复现：`bash sim/build/vision/run-merge-gates.sh`（本机工具链
riscv32 + Icarus 13；无 host gcc，`firmware` 主机规则测试仍不在本机声称）。

## 包状态（JL `d735d6f`/`759744b`）

- 当前有效包：`cop-board-gate-759744b99891`，tar SHA256
  `7160fffb44d6a2869ae6696eb1dacdca6f62b128c6abaef8d24f3cf8d054432b`；
  bit `d14a4bd0…e2a1a`、hwh `928f0d59…9107`（`C_SG_LENGTH_WIDTH=16`）、xsa `755f7033…d96ec`。
- **旧包全部作废**：`21c4e751bbe8`（DMA-14/一次性固件，10-23 已上板预检用的就是它）、
  `f856d5861db0`、`d66916c49b80`、当日首构 `9e1b24e2…`。
- 期望输出不变：pattern `0/0/0`、zero `2/2/258`。

## 边界

- 离板 PASS ≠ 板级验证；`BOARD`/`BOARD_CLOCK` 仍 UNVERIFIED。
- loader 的 FCLK1=40 运行时改钟与 20 次首读判据待板上执行（OPEN-BOARD-CLK-1）。
- 未烧写任何位流；未做 pattern/zero 推理。
