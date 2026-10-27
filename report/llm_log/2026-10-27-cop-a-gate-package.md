# [2026-10-27] A 变体整机门禁包收口

> 分支 `dev/riscv`；打包源提交 `2fc2bdd4a8f8cc012f3816cef917df9bd51f4d9b`；
> 本地未 push。A 是核+协处理器首包，B 视频变体未进入本包。

## 1. Windows 门禁证据

JL 在 Windows Vivado 2026.1 使用：

- `COP_BUILD_NAME=pynq_cop_a_20261027_r1`
- `COP_WITH_VIDEO` 未设置
- WNS `+2.078 ns`、DSP `136/220`、BRAM36 `69/140`、LATCHES `0`、DRC blocking `0`
- IMEM_FIRST_WORD `00008117`、IMEM_INIT_NONZERO `1`、READMEM_WARNINGS `0`
- CDC-15=`73`、CDC-3=`12`、CDC-6=`7`，allowlist 仍为 5 条

上一版 WNS 是 `+3.071 ns`，本版下降 `0.993 ns`；三级控制同步与 `COMMIT_RESULT` 增加了
实现逻辑/寄存路径，但 WNS 仍为正。CDC 计数完全不变，说明三级同步未新增跨域起点或报告路径；
本轮没有扩大 allowlist。

## 2. 产物哈希

| 产物 | SHA256 |
|:---|:---|
| bit | `f325a0dc4c2cb143e24ef13df6608e206af5c58f0354b3deec6f039d5875f71f` |
| hwh | `480d04a3d9abee59e81892378c2457dfe92ea0cf6fc0822d4467b2121dbab358` |
| xsa | `9e0a56276e89e2a94e3155eea7e267c97b97014ed74c8874524d03eaa462534c` |
| tar.gz | `e2eb5bd340f01c9cbfb2930a55d8ec36cbbdcdd6f0923636ed1e812b8b862127` |

包路径：`dist/cop-board-gate-2fc2bdd4a8f8/` 与
`dist/cop-board-gate-2fc2bdd4a8f8.tar.gz`。包内 `FILES.txt`/`SHA256SUMS` 均为 116 行，
`sha256sum -c SHA256SUMS` 为 116/116 OK；FILES 不含 `attach_pynq_video`、`src/vision`
或 HDMI XDC。

## 3. 离板重打包证据

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/pynq_cop_a_20261027_r1/pynq_cop_40mhz.bit \
    build/run/pynq_cop_a_20261027_r1/pynq_cop_40mhz.hwh \
    build/run/pynq_cop_a_20261027_r1/pynq_cop_40mhz.xsa \
    build/reports/pynq_cop_a_20261027_r1/gate_summary.txt
```

- BRAM pattern/zero 各 `9225 packed words/73795 elements`，cycles=`472594`，PASS。
- payload_loader 的 direct/MMCM 正负路径 PASS。
- `EXPECTED_OUTPUTS.tsv` 未改：pattern `0/0/0`，zero `2/2/258`。
- VERSION：`BOARD=UNVERIFIED_NEEDS_NC`、`BOARD_CLOCK=UNVERIFIED_NEEDS_40MHZ_READBACK`、
  `LOADER=BLOCKERS_RESOLVED_PENDING_BOARD_VALIDATION`、
  `BUILD_VARIANT=A_core_plus_coprocessor_ONLY`。

门禁与哈希不等于板级通过；NC 仍须读回时钟并验证 loader/结果。

## 4. 作废与上传清单

- 作废且不得使用：`f856d5861db0`、`759744b99891`、`5653d5911b76`；目录保留追溯。
- 只上传：
  1. `cop-board-gate-2fc2bdd4a8f8.tar.gz` — SHA256 `e2eb5bd3…2127`
  2. `cop-board-gate-2fc2bdd4a8f8.tar.gz.sha256` — SHA256 `513c2f1c…1bdd`
- 不上传裸 bit/hwh/xsa，不上传 B 视频变体。
