# 2026-10-23 协处理器 board bring-up：PARTIALLY READY（板卡/串口/JTAG OK；交接包缺失）

> **2026-10-23 更新**：JL `23e8aef`/`21c4e75` 已修复跨平台门禁并重打
> `cop-board-gate-21c4e751bbe8`，源码已合并到 `dev/exe`（`a87610c`）。
> 板卡现已通过 USB PROG/UART 连接：COM4 到 `xilinx@pynq:~$`，Vivado JTAG 只读探测到
> `xc7z020_1`；当前 PL 是旧 `base.bin`。**交接 tar 仍不在本机**，因此尚未烧写/预检。
> 修复复验见 [2026-10-23-cross-platform-fix-verify](../2026-10-23-cross-platform-fix-verify/README.md)。

> 状态：**板级验证 NOT RUN**；本记录不包含 STATUS/ERROR_CODE/RESULT_SEQ/推理字段，
> 只记录环境与阻塞点。没有伪造任何板级结果。

## 1. JL 交接信息（按用户转述）

- 包：`dist/cop-board-gate-21c4e751bbe8.tar.gz`，1,254,148 B；同名 `.sha256` 侧车。
- 位流 SHA256：`7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c`。
- 解包后 `sha256sum -c SHA256SUMS` 应 106/106 OK。
- 对照：`EXPECTED_OUTPUTS.tsv`（pattern class0/margin0/score0；zero class2/margin2/score258）。
- 边界：`BOARD=UNVERIFIED`；PROVISIONAL 诊断模型，不是发布模型。
- 本仓库可见的 `origin/dev/riscv` 最新为 `7c6cc40`；包名中的 `21c4e751bbe8`
  不在本地/已拉取的远端 refs 中，包的源提交未能核对。

## 2. 2026-10-23 实际检查（原样结果）

| 检查 | 结果 |
|---|---|
| 包路径 `sim/build/exe-wt/dist/cop-board-gate-21c4e751bbe8.tar.gz` | **不存在** |
| 同名 `.sha256` | **不存在** |
| 主工作区/两个 worktree 的 `dist/` | 不存在该包 |
| 用户 Desktop/Documents/Downloads、ZCode/临时目录 | 未找到该包或同名 tarball |
| D:/E: 根目录深度 3 | 未找到 |
| 远端分支 `dev/exe/dev/riscv/dev/vision/main` | 无该包；`dev/riscv=7c6cc40` |
| Vivado | 已安装：`D:\vivado\2026.1\Vivado\bin\vivado.bat` |
| `board/scripts/program_soc.bat` 默认 VIVADO | `D:\Vivado_downloads\2026.1\...`（与实机路径不一致，需 `set VIVADO=...`） |
| 板卡网络 | 无 192.168.50.x 接口；`ping 192.168.50.99` 失败；仅 Wi-Fi 10.54.149.251（改用串口 fallback） |
| JTAG/USB | **已连接**：FTDI COM4（PROG/UART）；Vivado `hw_server` 只读探测 `arm_dap_0` + `xc7z020_1`；`HW_XC7Z020_COUNT=1` |

因此：**包哈希未验、106 文件未验、未解包、未烧写、未只读预检、未提交任务、未读结果。**
板卡、串口、JTAG 已就绪；唯一缺的是交接 tar（以及完整推理所需的数据面 loader）。

## 2.1 板卡只读实测（2026-10-23，未烧写）

| 项 | 结果 |
|---|---|
| 串口 | COM4, 115200-8N1 → `xilinx@pynq:~$`（MobaXterm 关闭后可独占；工具 `sim/scripts/serial_board.ps1`） |
| OS | Linux `pynq 6.6.10-xilinx-v2024.1-gb36799f4e960`，armv7l |
| PYNQ | `pynq.__version__ == 3.1` |
| uptime / 内存 / 根分区 | up 22 min，491 MB RAM（可用 361），15G 根分区 52% |
| FPGA manager | `operating` |
| 当前 PL | dmesg 最后写入 `base.bin`；`/home/xilinx`/`/lib/firmware` 只有旧 `vision*.bit/hwh`，无 `pynq_cop*`/`cop-board-gate*` |
| JTAG | `hw_probe3.tcl`：`HW_DEVICE: arm_dap_0 PART=arm_dap`、`HW_DEVICE: xc7z020_1 PART=xc7z020`；[日志](logs/jtag-probe.log) |
| 温度 | XADC `in_temp0`：raw 2726 → **≈62.39 °C**；raw 2729 → **≈62.75 °C**（空载、烧写前；`/sys/class/thermal` 不存在） |
| Vivado | 2026.1，`D:\vivado\2026.1\Vivado\bin\vivado.bat`；`program_soc.bat` 默认路径不符，需 `set VIVADO=...` |

原始记录：[serial-inventory.txt](logs/serial-inventory.txt)、[serial-xadc.txt](logs/serial-xadc.txt)、
[jtag-probe.log](logs/jtag-probe.log)。串口工具：`sim/scripts/serial_board.ps1`（关闭 MobaXterm 的
COM4 会话后使用）。

## 3. 记录表（本次全部 NOT RUN）

| 项 | 值 |
|---|---|
| 日期 | 2026-10-23 |
| 操作者 | WC |
| Vivado 版本 | 2026.1（JTAG 只读探测已调用；未烧写） |
| bit SHA256 | 交接值 `7e1e3430…aa0b6c`，未在本机复核 |
| STATUS / ERROR_CODE / RESULT_SEQ | NOT RUN |
| pattern class/margin/score/logits | NOT RUN |
| zero class/margin/score/logits | NOT RUN |
| 与 EXPECTED_OUTPUTS 一致 | NOT RUN |
| 温度 | ≈62.4–62.8 °C（XADC 两次空载采样，烧写前） |
| 连续运行次数 / 首次失败原文 | NOT RUN（未烧写） |

## 4. 恢复条件（板卡/串口/JTAG 已就绪，只差包）

1. **交接包**：把 `cop-board-gate-21c4e751bbe8.tar.gz` 与 `.sha256` 放到
   `sim/build/exe-wt/dist/`，或放到 FAT32 U 盘插到本机；不需要以太网。
2. **串口**：COM4 已可用；使用我们的脚本时请关闭 MobaXterm 的 COM4 会话（独占）。
3. **JTAG**：已探测到 `xc7z020_1`；烧写前设
   `set VIVADO=D:\vivado\2026.1\Vivado\bin\vivado.bat`。
4. **基址**：解包后从 `pynq_cop_40mhz.hwh` 读 Address Editor 的 PS AXI base；
   只读预检不猜地址。
5. **完整推理**：还需 J08 数据面/`PynqDmaPlane` 或包内等效 payload/ROI loader；
   当前只有控制面/预检就绪。

恢复后执行顺序：

```bat
sha256sum -c cop-board-gate-21c4e751bbe8.tar.gz.sha256
tar -xzf cop-board-gate-21c4e751bbe8.tar.gz
cd cop-board-gate-21c4e751bbe8 && sha256sum -c SHA256SUMS
set VIVADO=D:\vivado\2026.1\Vivado\bin\vivado.bat
board\scripts\program_soc.bat dist\cop-board-gate-21c4e751bbe8\payload\pynq_cop_40mhz.bit
```

然后按 `docs/coprocessor-nc-handoff.md`：只读预检 → 确认无 UNCONSUMED →
提交 → 等 ACCEPTED → 等唯一终态 → 读 RESULT_SEQ/RESULT_* → 落盘后 CONSUME；
记录 STATUS/ERROR_CODE/RESULT_SEQ/class/margin/score/logits/温度/连续次数/首错原文。

烧写后在板卡上按 BTN0 复位；串口 115200 登录 `xilinx@pynq`；用解包 `.hwh` 里的
PS AXI base 跑只读预检。串口工具：`sim/scripts/serial_board.ps1`（先关闭 MobaXterm 的 COM4）。

## 5. 边界

- 这不是板级失败，也不是板级通过；当前是**交接包未提供 + 完整推理数据面未实现**。
- 板卡、串口、JTAG 已实测就绪；当前 PL 是旧 `base.bin`，未加载本轮 cop 位流。
- `BOARD` 仍为 `UNVERIFIED`；PROVISIONAL 诊断模型不是发布模型；下载成功也不等于验收。
- 未修改任何 RTL/固件/位流；未执行烧写。
