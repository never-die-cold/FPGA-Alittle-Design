# 2026-10-21 board-gate 同步：K4/K5、固件 E2E 与真接口控制面

> 基线：`dev/exe` @ `e1779f0` + JL `origin/dev/riscv` `af53fe2`（合并 `d677c7a`）。
> 结论：JL 的 K4/K5、固件 E2E、K3 延迟门禁在离板通过；WC 把 `PynqMmio` 控制面
> 接缝修正并用“窗口假 MMIO”跑通一笔提交/消费。**没有 bitstream/上板，不是板上跑通。**

## 1. 拉取到的 JL 更新

- K4：`build/build_coprocessor_gate.tcl`、40 MHz OOC XDC、Windows Vivado 检查清单；
- K5：NC 打包脚本 `sim/scripts/package_coprocessor_nc.sh`、下载/恢复交接文档；
- 固件 E2E：`tb_cop_firmware_e2e.v` + runner `firmware_e2e`，真实 CPU 执行固件到
  START/ACCEPTED/终态/结果/FW 写 + PS CONSUME；
- `cop_job.hex` 已按 A2 固件重建（修掉上轮“陈旧镜像”）；K3 `bram_network` 增加
  `cop_bram_latency` 延迟边界；
- 工具链前缀回落/无工具链 SKIP、Python 路径稳定、文档双索引/OPEN 登记。

## 2. WC 侧改动

- `PynqMmio` 修正：PYNQ `MMIO(base, 0x1000)` 的 `read(offset)`/`write(offset)` 已带 base，
  适配器不再二次加 base；`base` 只作记录/校验，必须是 Address Editor 分配值。
- 新增 `probe(transport)` / `CopDriver.probe()`：只读 `IP_ID/VERSION/CAPABILITY/
  STATUS/ERROR_CODE/RESULT_SEQ`，用于板上开机自检。
- 新增 `sim/scripts/cop_board_preflight.py --base <base>`：只读、不写、不碰 DMA；
  无 `pynq` 时以退出码 2 明确失败（本目录有原始记录）。
- 新增 `test_pynq_transport_round`：用带 4 KiB 窗口的假 MMIO 包 `PynqMmio`，跑通
  `probe → 提交 → ACCEPTED → 终态 → 结果 → 消费`，验证基址/offset 接缝。
  数据面仍是 `SimDmaPlane`；`PynqDmaPlane` 仍故意未实现（J08 物理 bank/结果 DMA）。

## 3. 复现与结果

```bash
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_inspection_python.sh
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_vision_python.sh

export PATH=/ucrt64/bin:/usr/bin:$PATH
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh firmware_e2e
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh decision_ab
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh cop_top
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh bram_network
```

| 入口 | 退出码 | 关键输出 |
|---|---:|---|
| inspection gate | 0 | 19 组 PASS；[inspection-gate.log](inspection-gate.log) |
| vision gate | 0 | 21 组 PASS；[vision-gate.log](vision-gate.log) |
| `firmware_e2e` | 0 | CPU START/ACCEPTED/DONE/RESULT_META/RESULT_SEQ/FW writes + PS CONSUME；[log](rtl/firmware_e2e.log) |
| `decision_ab` | 0 | T1–T7 PASS；[log](rtl/decision_ab.log) |
| `cop_top` | 0 | AXI/J02/DMA error/ABORT/SOFT_RESET/CFG_VALID；[log](rtl/cop_top.log) |
| `bram_network` | 0 | K3-LATENCY + pattern/zero 73,795 元素；[log](rtl/bram_network.log) |
| `firmware` | 未跑 | 主机规则测试仍需 host `gcc`；本机 MSYS 无 gcc，不声称 PASS |
| 板上预检（无 pynq） | 2 | 明确的“请在板卡上运行”；[log](logs/board-preflight-no-pynq.log) |

## 4. 能证明什么 / 不能证明什么

**能证明**

- A1/A2 的固件/硬件闭环：真实 CPU 执行 `cop_job.hex` → MMIO → ACCEPTED → 终态 →
  结果/FW 写 → PS CONSUME；J02 zero=2/2/258/1。
- 我们的驱动在“基址 + 相对 offset”的控制面接缝上跑通一笔；`PynqMmio` 的 base 翻译
  不再二次加 base。
- 19+21 组视觉/检查回归、K3 BRAM 延迟边界仍全绿。

**不能证明**

- 没有 Vivado 40 MHz 门禁报告、bitstream、`.hwh`；K4 仍是 **UNVERIFIED**。
- 没有上板、没有真实 HDMI/UVC、没有物理 bank/结果 DMA；`PynqDmaPlane` 未实现。
- `firmware` 的主机规则测试未跑（缺 host gcc）；`all` 未在本机单次跑完。
- 固件仍是单作业 `main`；连续多轮需要 JL 的循环/完成通知（见 PS 驱动使用档 §6）。
- 模拟硬件的 `S_input=1/127` 与脚本/图像派生分类器不是正式模型或精度证据。

## 5. WC 下一步（等外部件）

1. JL Windows Vivado 40 MHz compute/storage 门禁通过并给 bitstream/.hwh + SHA256；
2. NC 下载/复位/稳定后，WC 先跑只读预检：
   `python sim/scripts/cop_board_preflight.py --base <Address Editor base>`；
3. J08 物理 bank/结果 DMA 落地后实现 `PynqDmaPlane`，替换 `SimDmaPlane`，
   复跑同一异常矩阵和一轮检查；
4. 全部真实链路就绪前，`prototype=true` 不关；模拟/软件/板上三档分开报。
