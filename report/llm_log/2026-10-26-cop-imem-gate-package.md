# [2026-10-26] IMEM 整机门禁包归档

> 分支 `dev/riscv`；包源提交 `5653d5911b76c980e04d8e60012e4d84e03e74f8`；本地未 push。

## Windows 门禁证据

JL 在 Windows 暂存副本 `D:\boardtop` 用 Vivado 2026.1 直接运行 Tcl；该路径对应同一仓库内容，
不是提交文件中的硬编码路径。主机无 Windows RISC-V 工具链，未使用 PowerShell 包装脚本：

```powershell
$env:COP_PYTHON="C:\Microsoft VS Code\anaconda\python.exe"
& "D:\vivado\2026.1\Vivado\bin\vivado.bat" -mode batch `
  -source build\build_pynq_cop_gate.tcl
```

- WNS `+3.071 ns`；DSP `136/220`；BRAM36 `69/140`；LATCHES `0`；DRC blocking `0`。
- CDC：CDC-15=`73`、CDC-3=`12`、CDC-6=`7`，均命中 allowlist。
- IMEM：`IMEM_FIRST_WORD=00008117`、`IMEM_INIT_NONZERO=1`、`READMEM_WARNINGS=0`。
- bit SHA256：`1232769fdeabe59c962dae62a75bc1a5ebca07b1985898b6961fd574878f05db`。
- hwh SHA256：`dce025d3db119824126d4af6915983971ca9eaf98ccdbf726f2d66a9c7c73070`。
- xsa SHA256：`255794ec8f07488dbe8b5feec3a6b1a3e8048f9a689777333fa0b639f0c23d28`。

这些数字证明整机综合实现与 IMEM 初始化门禁通过，不等于板级验收。

## NC 重打包证据

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.xsa \
    build/reports/pynq_cop_40mhz/gate_summary.txt
```

- 新包：`dist/cop-board-gate-5653d5911b76.tar.gz`。
- tar SHA256：`a342287dbce47e3d1f24e22b757243f97626d11336be248e88aed3fc805178af`。
- 包内 `sha256sum -c SHA256SUMS` 全部 OK；bit/hwh/xsa 与 Windows 哈希逐项一致。
- BRAM pattern/zero 各 9,225 packed words、73,795 元素逐项一致，cycles=`472594`。
- `EXPECTED_OUTPUTS.tsv` 未改：pattern class/margin/score=`0/0/0`，zero=`2/2/258`。
- `cop-board-gate-759744b99891` 已作废，不得上传或用于本轮板验；本轮只交付新 tar 与 sidecar。

## 状态与下一步

- `VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`。
- `BOARD=UNVERIFIED_NEEDS_NC`。
- `BOARD_CLOCK=UNVERIFIED_NEEDS_40MHZ_READBACK`。
- `LOADER=BLOCKERS_RESOLVED_PENDING_BOARD_VALIDATION`。

NC 解包、执行 `sha256sum -c SHA256SUMS` 后运行：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --package . --reads 20 --smoke-timeout 2
```

只有读回 40 MHz、20 次 STATUS 均为 `0x1` 且两秒内固件活性 PASS，才能继续 zero/pattern；
当前不得声称板级通过。
