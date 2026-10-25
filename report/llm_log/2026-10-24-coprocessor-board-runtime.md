# [2026-10-24] 协处理器板端时钟与 J08-lite 续档

> 标签：#coprocessor #PYNQ #clock #DMA #NC
> 分支：`dev/riscv`｜未 push｜包源 HEAD：`d66916c49b807f5b94a77e35e04540a04a3c4dab`

## 已完成

- `a5c2612`：新增 `tools/cop_payload_loader.py`、离线门禁与 runner `payload_loader` 模式；
  校验 PROVISIONAL manifest、SHA256、CRC32、HWH 地址/位宽、结果字段与 RESULT_SEQ。
- `d66916c`：新增 40 MHz 时钟/BOOT.BIN runbook、loader 时序与排错表；NC 文档改为
  “JTAG/只读预检已完成，板级功能仍 UNVERIFIED”；打包加入 loader 与 XSA。
- 未改 RTL、冻结契约或 EXPECTED_OUTPUTS；未重跑 Vivado，也未改变既有门禁结论。

## 已验证证据

- `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh payload_loader`
  → 退出 0；`PASS: payload_loader manifest/SHA256/CRC/HWH/address/result/clock guards; 14-bit DMA rejects 36032 before MMIO`。
- 对旧包执行 `python3 tools/cop_payload_loader.py run ... --case zero ...` → 退出 1；
  `BLOCKED: DMA_LENGTH_BLOCKED: payload=36032 max_single_packet=16383`，且未创建 measurement 文件。
- `RISCV_CROSS=riscv64-unknown-elf- COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all`
  → 退出 0；最后一条 `PASS: cnn_sequencer .../zero all 9225 packed words/73795 elements match integer network; logits=04fd02 class=2 margin=2 cycles=472593`。
- 重打包命令：
  `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/package_coprocessor_nc.sh build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh build/run/pynq_cop_40mhz/pynq_cop_40mhz.xsa build/reports/pynq_cop_40mhz/gate_summary.txt`
  → `PASS: NC package .../dist/cop-board-gate-d66916c49b80`；包内 `sha256sum -c SHA256SUMS` 全部 OK。

## 产物与状态

- 包：`dist/cop-board-gate-d66916c49b80/`；tar SHA256
  `95c246fc2354487d90153032c5de9bafd01ff0fe016cc63eb32c1dd15f808855`。
- bit SHA256：`7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c`；
  hwh：`cba4d12c58213897c0dbdafd327348ce5d4bd9d21dad6d5a469eb44bd03d799d`；
  xsa：`beac251a9cb2bbc28dd24efabf45d08e25023b77696007a4c3fe61726e1ba8aa`。
- VERSION：Vivado 2026.1/40 MHz whole-system PASS；BITSTREAM 为 JL gate passed；
  BOARD 与 BOARD_CLOCK 均 UNVERIFIED；LOADER 明示 DMA 长度/固件启动顺序阻塞。
- EXPECTED_OUTPUTS 未变：pattern `0/0/0`，zero `2/2/258`；`score_q15` 是整数分数，不是概率。

## OPEN / 下一步

1. `OPEN-BOARD-CLK-1`：NC 实测 FCLK1=142.857 MHz。先运行 clock 命令，要求读回 40 MHz
   且 20 次 STATUS 首读全为 `0x1`；超频导致首读 `0x0` 目前只是待验证假设。
2. `OPEN-LOADER-1`：当前 DMA `C_SG_LENGTH_WIDTH=14`，单包上限 16,383 B；禁止把
   36,032 B payload 分包制造提前 TLAST。由 JL 改 BD 后必须重走整机门禁和出包。
3. `OPEN-LOADER-2`：一次性 `cop_job` 可能在 PS 配置前退出。由 JL 提供等待任务或可控重启的
   固件/位流；PS 不得越权写 START。修复前 loader 的 NO_ACK 是预期 fail-closed。
4. 若 40 MHz 下首读仍为 `0x0`，NC 采集连续读数，JL 用 ILA 查复位释放/首次 AXI 访问同步；
   在证据出现前不改 RTL。NC 现场功能、稳定性与 BOARD 结论均未验证。

NC 下一条命令：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20
```

随后记录零副作用能力阻塞：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py run --package . --case zero --measurement ./zero-measured.json --timeout 10
```

## 本次例外

沿用 board-top 中 JL 对古法编程逐步问答/单步行数门槛的临时豁免；其余纪律保持：本地提交、
未 push、不改冻结契约、不把 Windows 门禁或 JTAG 下载称为板级验收。
