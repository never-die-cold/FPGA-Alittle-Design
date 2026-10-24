# 2026-10-23 跨平台门禁修复复验：8/8 离板模式全绿

> 基线：`dev/exe` @ `4c9caab` + JL `origin/dev/riscv` `94af6f6`（合并 `a87610c`）。
> 结论：上轮报的两个 Windows/Icarus 缺口已被 JL 修复；本轮复跑 **8 个 board-top 相关
> 离板模式全部 exit 0**，WC 两套门禁仍 19/21 exit 0。板上仍 `UNVERIFIED`。

## 1. JL 修复（`23e8aef`）

- `generate_payload_manifest.py` 改为 `write_bytes`，manifest/sidecar/负例都是 LF 字节，
  Windows 不再因 CRLF 导致 sidecar 哈希不一致；
- `cop_axi_lite_cdc.v` 把 `reg w_ack,r_ack,w_active,r_active;` 移到首个 `always` 之前，
  Icarus 13 的“先用后声明” elaboration 错误消失；
- NC 包从 `21c4e75` 重打（`94af6f6` 记录）：包名 `cop-board-gate-21c4e751bbe8`、bit
  SHA256 `7e1e3430…aa0b6c`、hwh `cba4d12c…d799d`、tar `d74189b9…e76046`，与用户交接一致。

## 2. 复跑结果

| 模式 | 退出码 |
|---|---:|
| `manifest_v1` | 0 |
| `payload_adapter` | 0 |
| `payload_network` | 0 |
| `activation_storage` | 0 |
| `pynq_top` | 0 |
| `axi_lite_cdc` | 0 |
| `axis_fifo_random` | 0 |
| `firmware_e2e` | 0 |
| inspection gate（WC） | 0（19 组） |
| vision gate（WC） | 0（21 组） |

原始日志/退出码：[rtl/](rtl/)、[inspection-gate.log](inspection-gate.log)、
[vision-gate.log](vision-gate.log)。本机 Icarus 13.0。

## 3. 下一步上板需要的硬件

针对当前 **compute-only** 的 `pynq_cop_40mhz.bit`（PS+PL，无视频通路）：

1. **PYNQ-Z2 板卡** + 12V 电源适配器（Power 跳线置 REG）+ 可启动 microSD（PYNQ 镜像）。
2. **Micro-USB 数据线**：PC ↔ PYNQ-Z2 的 **PROG/UART** 口（同时给 Vivado JTAG 和
   115200 串口控制台）。这是 `program_soc.bat` 下载 bit 的必需链路。
3. **网线**：PC ↔ PYNQ-Z2 以太网口。建议 PC 静态 `192.168.50.1/24`、板卡
   `192.168.50.99/24`，用于 SSH/Jupyter/运行 `cop_board_preflight.py`；若板卡用 DHCP，
   给出实际 IP 即可。
4. **Vivado 2026.1**：已装 `D:\vivado\2026.1\Vivado\bin\vivado.bat`；运行
   `program_soc.bat` 前需 `set VIVADO=...`（脚本默认路径与实际安装不一致）。
5. **交接包**：`cop-board-gate-21c4e751bbe8.tar.gz` + `.sha256` 放入
   `sim/build/exe-wt/dist/`（当前不在本机）。
6. **完整推理额外需要**：J08 数据面/`PynqDmaPlane` 或包内等效的 payload/ROI 装载工具；
   否则只能做只读预检/寄存器验证，无法产出 pattern/zero 的 class/margin/score/logits。
7. 视频相关（HDMI IN/OUT、Pi Camera、采集卡）**不属于当前 compute-only 位流**；
   等整机视觉位流（J07/后续）再接。

## 4. 边界

- 8/8 离板 PASS ≠ 板上跑通；`BOARD=UNVERIFIED_NEEDS_NC`。
- 包/板卡不在本机，本轮未烧写、未预检、未提交任务。
- PROVISIONAL 诊断模型不是发布模型；`score_q15` 不是概率。
- 未修改 JL 的 RTL/生成器；修复由 JL `23e8aef` 完成。
