# 2026-10-22 board-top 同步：整机门禁 PASS、bit/hwh 与 Windows 复现性缺口

> 基线：`dev/exe` @ `202c81e` + JL `origin/dev/riscv` `7c6cc40`（合并 `a315537`）。
> 结论：JL 的 Windows Vivado 2026.1 **整机 40 MHz 门禁 PASS**，bit/hwh 与 NC 包装备好；
> **板上仍 UNVERIFIED**。WC 复跑新离板门禁时发现 **3 个 Windows/Icarus 可复现性缺口**，
> 已定位到具体文件/行，未擅自修改 JL 的 RTL/生成器。

## 1. 拉取到的 JL 更新

- production PL top `src/riscv/pynq_cop_top.v`、AXI-Lite CDC、AXIS 异步 FIFO、payload adapter、
  shadow model bank、16 ROI activation slots；
- manifest v1（`docs/contracts/coprocessor-manifest-v1.md`）与 PROVISIONAL 36,032 B payload；
- Windows 整机 40 MHz 门禁：WNS **+2.498 ns**、DSP 136/220、BRAM36 69/140、LATCHES=0、
  DRC blocking=0，CDC-15/3/6 全部命中 allowlist；
- bit SHA256 `b499cabe…ef7e0a`、hwh SHA256 `6a0a398b…4042c6`、
  NC 包 `dist/cop-board-gate-f856d5861db0/`（tar `af1a343a…5809dc`）。
  `dist/` 不在本 worktree（生成物，未入库）；板上仍由 NC 下载验证。

## 2. WC 复跑结果（本机 Windows + Icarus 13.0）

| 模式 | 退出码 | 结论 |
|---|---:|---|
| inspection gate（WC） | 0 | 19 组 PASS；[log](inspection-gate.log) |
| vision gate（WC） | 0 | 21 组 PASS；[log](vision-gate.log) |
| `manifest_v1` | 1 | **FAIL**：`manifest.json` CRLF 与 sidecar 哈希不一致 |
| `payload_adapter` | 0 | PASS |
| `payload_network` | 1 | **FAIL**：先跑 `manifest_v1`，同因失败 |
| `activation_storage` | 0 | PASS |
| `pynq_top` | 2 | **FAIL**：Icarus elaboration，`w_ack/r_ack` 先用后声明 |
| `axi_lite_cdc` | 2 | **FAIL**：同因 |
| `axis_fifo_random` | 0 | PASS（四档 257 beat，无重复/丢失/乱序） |
| `firmware_e2e` | 0 | PASS（CPU/固件/MMIO/ACCEPTED/终态/结果/CONSUME） |

原始日志与退出码在 [rtl/](rtl/)。

## 3. 缺口 1：manifest sidecar 在 Windows 上必失败

`generate_payload_manifest.py` 用 `Path.write_text(text)` 写 `manifest.json`，Windows 会做
`\n→\r\n` 转换；sidecar 却用 `hashlib.sha256(text.encode())`（LF）计算。结果：

```text
manifest_bytes 4182
crlf_pairs     212
sha256_actual  95012d1d304f1c84cf70fba04c9d3001f683c62adb4db63376ed58e647ef19ff
sha256_lf      4a414729fb37921be974b54fb22ac8b83b03477f339e88c0614f44b0fe59e4bd
sidecar        4a414729fb37921be974b54fb22ac8b83b03477f339e88c0614f44b0fe59e4bd
```

完整输出：[logs/manifest-crlf.txt](logs/manifest-crlf.txt)。这会让 Windows 上的
`manifest_v1`/`payload_network` 和 NC 打包重跑失败；Linux 上不会暴露。
**建议**：`write_text(..., encoding="utf-8", newline="\n")`（manifest 与两个 bad 负例），
或改为对实际写入字节做哈希。属 JL 的生成器；本轮未改。

## 4. 缺口 2：`cop_axi_lite_cdc.v` 先用后声明

Icarus 13.0 报：

```text
src/coprocessor/cop_axi_lite_cdc.v:32: error: Unable to bind wire/reg/memory `w_ack'
src/coprocessor/cop_axi_lite_cdc.v:32: error: Unable to bind wire/reg/memory `r_ack'
src/coprocessor/cop_axi_lite_cdc.v:47: : A symbol with that name was declared here.
```

第 32 行在 `always` 块里使用 `w_ack/r_ack`，第 47 行才 `reg w_ack,r_ack,w_active,r_active;`。
Vivado 接受这种写法，所以整机门禁 PASS；但仓库的 Icarus 入口在 Windows 上无法复现
`pynq_top`/`axi_lite_cdc`。证据：[logs/cdc-declaration.txt](logs/cdc-declaration.txt)。
**建议**：把该 `reg` 声明（含 `w_active/r_active`）移到第一个 `always` 之前；语义不变。
属 JL 的 RTL；本轮未改。

## 5. 这对 WC 意味着什么

- **板上执行仍等 NC**：bit/hwh 已就绪，但本机无板、`dist` 未入库；WC 不能把 JL 的 Vivado
  PASS 写成板级 PASS。
- NC 下载后 WC 先跑只读预检：
  `python sim/scripts/cop_board_preflight.py --base <Address Editor base>`；
  之后才谈提交/消费一轮。
- manifest v1 是 PROVISIONAL，不是正式模型；`OPEN-BT-4` 只支持 `target_id==roi_index`
  恒等映射——我们当前引擎的描述符正是 identity，兼容；任意描述表仍未接。
- 数据面 `PynqDmaPlane` 仍未实现；物理 bank/结果 DMA/实际地址等 J08。
- 上述两个 Windows 缺口不影响 Vivado 整机门禁结论，但会让 Windows 一键 Icarus/NC 打包
  失败，需 JL 修后 WC 才能用同一入口复验。

## 6. 复现

```bash
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_inspection_python.sh
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_vision_python.sh

export PATH=/ucrt64/bin:/usr/bin:$PATH
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh manifest_v1
# 其余模式见 rtl/*.log；本机 Icarus 13.0
```

## 7. 边界

- JL 整机 40 MHz 门禁 PASS ≠ 板级验收；板上仍是 `UNVERIFIED`。
- PYNQ 包与 bit/hwh 不在本 worktree；哈希来自 JL 交接文档，未在本机复核产物。
- 诊断 J02/PROVISIONAL payload 不是正式模型；`score_q15` 不是概率。
- 未修改 `src/coprocessor/`、`src/riscv/` 或 `sim/coprocessor/` 的 JL 文件。
