# Board-Gate 断点存档

## a) 基线

- 本轮代号：`board-gate`；分支：`dev/riscv`。
- 存档内容基线 HEAD：`de057ff`（本 checkpoint 是其后的纯文档提交）。
- 未 push；写入 checkpoint 前相对 `origin/dev/riscv` ahead 12，提交本文件后应为 ahead 13。
- 缺陷收尾涉及的 9 个唯一文件已拆成 6 个提交，最大文本提交为 74 行；`cop_job.hex` 按 binary 记录。
  历史 K3 提交 `4a57ef4` 为已知 232 行超标，不重写历史；其后的提交均按 ≤100 行拆分。

## b) 已完成

- K1 WC 接口与裁决 A/B：`b8496fe`、`a0d3d99`。
- K2 存储方案与 UNVERIFIED 边界：`5d2f867`、`097fbd7`。
- K3 BRAM 实现/延迟边界/逐元素对拍：`45c677f`、`4a57ef4`、`62168f8`。
- K4 Vivado Tcl/XDC 与 Windows 检查清单：`c9c3c97`、`b821aa1`。
- K5 NC 打包与交接：`7b2df64`、`c4839f3`。
- 缺陷 1，工具链前缀传播、回落、SKIP 与 Python 路径稳定：`09fbebf`、`8317fa6`。
- 缺陷 2，固件 E2E、runner/Makefile 与刷新后的 BRAM 镜像：`ee1aff2`、`7fe58f3`、`e0337ad`。
- 缺陷 3，双索引与 OPEN 登记：`038f674`；下一执行点同步：`de057ff`。

## c) 已验证证据

- 裸环境审计：`bash sim/scripts/run_coprocessor_iverilog.sh all` → **退出 1**；最后一条 PASS：
  `PASS: objdump 失败 → make 非零退出，cop_job.dis 未被改写（sha256 aa69601a2073…）`。
  随后 `generate_network_vectors.py` 因系统 `python3` 缺 NumPy 终止；不得写成 all PASS。
- 可复现全回归：
  `RISCV_CROSS=riscv64-unknown-elf- COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh all`
  → 退出 0；最后一条：
  `PASS: cnn_sequencer .../zero all 9225 packed words/73795 elements match integer network; logits=04fd02 class=2 margin=2 cycles=472593`。
- BRAM 对拍：`COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh bram_network`
  → 退出 0；pattern/zero 均为 `9225 packed words/73795 elements match integer network`，并有
  `PASS: K3-LATENCY nominal one-cycle BRAM read matches; early/late samples mismatch visibly`。
- 固件 E2E：`COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python bash sim/scripts/run_coprocessor_iverilog.sh firmware_e2e`
  → 退出 0；`PASS: firmware_e2e CPU START/ACCEPTED/DONE/RESULT_META/RESULT_SEQ/FW writes + PS CONSUME; J02 zero=2/2/258/1`。
- 索引：逐个 `rg` 四个文件名到 `docs/README.md docs/contracts/README.md`，4/4 文件均在两处命中。
- 收口前 `git status --short` 无输出；六个缺陷提交逐项 `git show --numstat` 均满足 ≤100 文本行。

## d) 未完成 TODO

1. P0 Windows Vivado 40 MHz compute/storage 两档 → JL。
2. P0 bitstream + `.hwh`（门禁通过后才产出）→ JL。
3. P1 NC 下载 + 现场稳定 + 实板结果 → NC。
4. P1 WC 把 mock 换真接口，跑通一轮检查 → WC。
5. P2 生产 payload → 物理 bank 的 manifest 地址适配、板级顶层 → JL。

## e) OPEN 全量列表

- OPEN-K2-1：16×64 权重 bank、BRAM 数量/端口模式及整机布线待 Windows Vivado 确认。
- OPEN-FW-1：固件进入 bitstream/BRAM 初值的通路未验证。
- OPEN-ENV-1：裸系统 Python 缺 NumPy 时 `all` 退出 1；干净环境依赖边界仍待复测。
- OPEN-DOC-1（已修复）：`cop_job.hex` 已由 Makefile `all` 重建并由 `firmware_e2e` 加载。

## f) 下一条命令

```bat
call "D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 compute && call "D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat" -mode batch -source build/build_coprocessor_gate.tcl -tclargs 40 storage
```

## g) 纪律提醒

本地不 push；单 commit ≤100 行；不改已冻结契约；不声称未执行的综合、时序或上板结论。
