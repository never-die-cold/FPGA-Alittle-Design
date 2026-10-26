# [2026-10-25/26] cop IMEM 初始化与改钟重配返工

> 分支 `dev/riscv`；起点 `0aecf97`；本地提交、未 push。

## 已完成提交

- `2e3a1a1`：IMEM 源文件检查、完整 IMEM/DMEM 映像生成、综合日志扫描工具。
- `0d4e973`：IMEM 门禁正例与缺失/空/前缀错误/readmem warning 负例。
- `e7959f9`：Vivado 构建期绝对路径、显式 hex 依赖、日志与 RAMB INIT 回读门禁。
- `af6a4e5`：改钟→重配 PL→稳定→FCLKRESETN1→MMIO，以及两秒固件活性检查。
- `9368f6c`：顺序、未重配拒绝、静默固件超时的 loader 离板测试。
- `89eb3ce`：`imem_gate` runner 模式、`all` 和 NC 文件清单接入。
- `a579bb3`：IMEM 调用清单、综合证据边界与 Vivado checklist。
- `01deb1e`：板端时钟恢复勘误、loader/NC 说明与下一执行点。

## 工具与现场结论

- 本机 `vivado -version`：`vivado: command not found`；clean synth、INIT 回读、新 bit 均
  **UNVERIFIED**。
- NC 已复现：FCLK1=40 MHz 后旧 PL 的 STATUS 连续 20 次为 `0x0`；保持时钟 fresh Overlay
  后 20 次均为 `0x1`。`0x0` 表示 cop 域无效/未就绪，不是超频结论。
- fresh Overlay 后 6.5 秒 FW_DECISION 恒 0、ACCEPTED 不到；旧 bit 的固件活性结论保持
  FAIL/BLOCKED，不能证明 IMEM INIT 已进入 bit。

## readmem / IMEM 修复

- 可综合 `$readmemh` 仅 `src/riscv/imem.v` 与 `dmem.v`；生产路径为
  `wrapper → pl/pynq_cop_top → soc_top → u_imem/u_dmem`，无 `$readmemb`。
- 旧相对路径从 `build/run/pynq_cop_40mhz/project/pynq_cop_40mhz.runs/synth_1`
  解析，不是仓库根。
- 构建期检查 `cop_job.hex` 首三字 `00008117/00010113/00000297`，生成 8192-word
  IMEM/DMEM（尾部 NOP/零），并通过 module 参数传入绝对路径；提交文件不含机器路径。
- synth 后扫描 readmem/cop_job warning/error，并读取八个 4-bit RAMB36 lane 的全部 `INIT_*`；
  要求非全零且地址 0 重组为 `00008117`。`00000000` 是非法指令，`00000013` 是 NOP。

## 2026-10-26 本机验证

`python -m py_compile ...` 因本机没有 `python` 命令而退出 127；等价 Python 3 命令通过：

```bash
python3 -m py_compile tools/cop_imem_gate.py \
  sim/coprocessor/test_cop_imem_gate.py sim/coprocessor/test_cop_payload_loader.py
bash -n sim/scripts/run_coprocessor_iverilog.sh sim/scripts/package_coprocessor_nc.sh
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh imem_gate
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh payload_loader
RISCV_CROSS=riscv64-unknown-elf- COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh all
```

静态检查、两项模式与 `all` 均退出 0；关键原始 PASS：

```text
PASS: imem_gate validates cop_job prefix, materializes 8192-word NOP/zero images, and rejects missing, empty, wrong-prefix, and readmem-warning inputs
PASS: payload_loader DMA16 plus clock->PL reload->FCLKRESET1->STATUS ordering; unreconfigured access and silent firmware fail closed
PASS: firmware_e2e waits for delayed CFG/model/ROI then CPU START/ACCEPTED/DONE/RESULT_SEQ/FW + PS CONSUME; J02 zero=2/2/258/1
PASS: cnn_sequencer .../pattern all 9225 packed words/73795 elements match integer network; logits=01fd01 class=0 margin=0 cycles=472593
PASS: cnn_sequencer .../zero all 9225 packed words/73795 elements match integer network; logits=04fd02 class=2 margin=2 cycles=472593
```

Icarus 既有 TB 仍报告短源文件不足 8192 words；这是本地仿真原始行，不是 Vivado 证据。
生产构建改用完整派生文件。历史流程未保存 `synth_1/runme.log`，不可伪造旧 Vivado warning。

## OPEN / 未完成

- OPEN-IMEM-1：JL 须用 Windows Vivado 2026.1 clean build 验证日志门禁、RAMB INIT 首字与非零。
- OPEN-BIT-1：上述门禁通过后才能生成、哈希并打包新 bit/hwh/xsa；旧 bit 不得复用。
- OPEN-BOARD-1：NC 须用新包验证 20 次首读、两秒固件活性及真实 DMA/result；BOARD UNVERIFIED。

## 下一条命令（JL / Windows）

```powershell
powershell -ExecutionPolicy Bypass -File build\run_pynq_cop_gate.ps1 `
  -Vivado "D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat"
```

预期依次出现 `IMEM PRECHECK PASSED`、`IMEM MATERIALIZE PASSED`、
`READMEM LOG GATE PASSED`、`IMEM POST-SYNTH GATE PASSED` 和整机门禁 PASS；任一缺失即 FAIL，
不产 NC 包，也不声称综合、时序或板级通过。
