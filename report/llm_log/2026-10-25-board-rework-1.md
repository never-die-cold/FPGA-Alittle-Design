# [2026-10-25] 上板返工第 1 轮：DMA-16 与驻留固件

> 分支：`dev/riscv`｜本地提交，未 push｜Windows Vivado/板级状态未在本轮改写。

## 已完成 commit

- `b78bf80`：`build/create_pynq_cop_bd.tcl` 固定 AXI DMA `c_sg_length_width=16`，保持
  SG=0、MM2S=1、stream=64-bit；loader 只接受 HWH 精确 16 位并按 `MM2S_LENGTH[15:0]`
  写长度。14 位 HWH 与 65,536 B 负例均在 MMIO 前拒绝，禁止分包绕过 TLAST。
- `a9b68d9`：`cop_job` 驻留等待 CFG/MODEL/ROI；CFG_VALID 证明
  `CFG_APPLIED==CFG_SEQ`，`DMA_BYTES==ROI_COUNT*4096` 区分 ROI 完成与前一笔权重完成。
  BUSY/UNCONSUMED 仍立即拒绝，等待超时仍按 CONFIG/RECHECK，START 仍只由固件发起。

## 仓库内验证

- `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh payload_loader`
  → 退出 0；`PASS: payload_loader requires 16-bit/65535-byte Direct MM2S length; 14-bit HWH rejects before MMIO and 36032-byte payload preflight passes at 16-bit`。
- `RISCV_CROSS=riscv64-unknown-elf- COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh firmware_e2e`
  → 退出 0；`PASS: firmware_e2e waits for delayed CFG/model/ROI then CPU START/ACCEPTED/DONE/RESULT_SEQ/FW + PS CONSUME; J02 zero=2/2/258/1`。
- 按规定先执行同环境的 `bash sim/scripts/run_coprocessor_iverilog.sh all` → 退出 0；最后一条
  zero `9225 packed words/73795 elements match integer network; logits=04fd02 class=2 margin=2 cycles=472593`。
- 随后执行 `bash sim/scripts/run_coprocessor_iverilog.sh bram_network` → 退出 0；延迟边界 PASS，
  pattern/zero 各 `9225 packed words/73795 elements` 逐项一致，cycles 均为 472594。
- `EXPECTED_OUTPUTS.tsv` 未改：pattern `0/0/0`，zero `2/2/258`。

## 未完成 / 状态边界

- 新源码尚未在 Windows Vivado 2026.1 重跑；WNS/DSP/BRAM/CDC/DRC 和新 bit/hwh/xsa 哈希均
  **UNVERIFIED**。不得沿用旧门禁数字证明新构建。
- `dist/cop-board-gate-d66916c49b80` 是旧 DMA-14/一次性固件包，VERSION 的 BLOCKED 结论仍真实；
  本轮未重打包，也未把 LOADER 提前改成可运行。
- JL 门禁通过后才可回写新产物、更新 LOADER 具体状态并重打 NC 包；BOARD 继续 UNVERIFIED。

## 下一条命令（JL / Windows 仓库根目录）

```powershell
powershell -ExecutionPolicy Bypass -File build\run_pynq_cop_gate.ps1 -Vivado "D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat"
```

该脚本先强制重建 `cop_job.hex`，再跑 ENABLE_COP=0 基线和 40 MHz 整机门禁。失败时不得产新包。

## 理解门槛与本次例外

本轮提示词已明确回答三项关键理解点：不能分包是因为每笔 DMA 都产生 TLAST；固件必须驻留是
因为 PS 配置晚于 CPU 上电；新 bit 会变化，所以必须先重走整机门禁再打包。沿用 board-top 已记录
的逐题等待/单步行数临时例外；其余纪律保持：本地不 push、不改冻结契约、不声称板级结论。
