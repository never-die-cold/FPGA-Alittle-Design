# [2026-10-25] 上板返工第 1 轮：干净门禁包

> 分支：`dev/riscv`｜包源提交：`759744b99891317537869c050b54aca576f58cac`｜本地未 push。

## Windows 门禁证据

- 同日首构的 bit 前缀 `9e1b24e2` 与固件提交并发，已经作废，不得打包或上传。
- JL 从干净仓库用 Vivado 2026.1 重跑：WNS +2.771 ns、DSP 136/220、BRAM36 69/140、
  LATCHES=0、DRC blocking=0；CDC-15=73、CDC-3=12、CDC-6=7，均在 allowlist 内且无 Critical。
- 最终采用的 bit SHA256：
  `d14a4bd037b1809c74fe511f1c7667edbc6bd6ecac8a8712a423946f5f1e2a1a`。
- 最终采用的 hwh SHA256：
  `928f0d594ccbb83c8bd17e5ed284a6f2849e1b598c28073c779afb1ff9849107`；其中
  `C_SG_LENGTH_WIDTH=16`。
- 最终采用的 xsa SHA256：
  `755f70337bdc5a06da0dcaa715c512806b7011efa09f95128314cb78a2ad96ec`。
- JL 报告干净构建后的 `all` 共 67 条 PASS；本次没有重跑 Vivado，也不外推板级结论。

## NC 重打包证据

命令：

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/package_coprocessor_nc.sh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.bit \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.hwh \
    build/run/pynq_cop_40mhz/pynq_cop_40mhz.xsa \
    build/reports/pynq_cop_40mhz/gate_summary.txt
```

- `PASS: NC package .../dist/cop-board-gate-759744b99891`。
- BRAM pattern/zero 各 9,225 packed words、73,795 元素逐项一致，cycles=472594；
  pattern class/margin/score=`0/0/0`，zero=`2/2/258`，未改 EXPECTED_OUTPUTS。
- payload loader：16-bit/65,535-byte 门禁 PASS，14 位 HWH 在 MMIO 前拒绝，36,032 B 预检 PASS。
- 包内 `sha256sum -c SHA256SUMS` 全部 OK；包内 bit/hwh/xsa 与上节三份哈希一致。
- tar SHA256：`7160fffb44d6a2869ae6696eb1dacdca6f62b128c6abaef8d24f3cf8d054432b`。

## 状态边界

- `LOADER=BLOCKERS_RESOLVED_PENDING_BOARD_VALIDATION`：DMA-16 与驻留固件已进干净门禁产物，
  只表示两个离板阻塞解除；不是 loader 板上 PASS。
- `BOARD=UNVERIFIED_NEEDS_NC`，`BOARD_CLOCK=UNVERIFIED_NEEDS_40MHZ_READBACK`。
- `d66916c49b80`、`21c4e751bbe8`、`f856d5861db0` 三个旧包均不进入上传候选。
- JL 门禁 PASS 不等于 NC 板级验收；payload 仍是 `kind=PROVISIONAL`，不是发布模型。

## 上传候选（等待 JL 确认）

优先作为 GitHub Release 附件上传：

1. `cop-board-gate-759744b99891.tar.gz` — SHA256
   `7160fffb44d6a2869ae6696eb1dacdca6f62b128c6abaef8d24f3cf8d054432b`
2. `cop-board-gate-759744b99891.tar.gz.sha256` — 文件自身 SHA256
   `c4c5f57eb44e9fff38494ee592bfa9814244399ce4cfedd1e221847f7b19216a`

本轮未上传。若 Release 不可用，回退方案只 `git add -f` 上述 tar.gz，不加入 checksum sidecar、
解包目录或裸 `.bit/.hwh/.xsa`；执行前仍须 JL 明确确认。

## NC 下一步

解包并核验 `SHA256SUMS` 后，先执行：

```bash
sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20
```

只有 FCLK1 回读为 40 MHz 且 20 次 STATUS 首读均为 `0x1`，才执行 zero/pattern loader；
BOARD 状态在 NC 实测前保持 UNVERIFIED。

## 本次例外

沿用 board-top 已由 JL 授权的逐题等待/单步行数临时例外；其余纪律保持：本地不 push、
不改冻结契约、不把综合实现结论写成板级结论。此次只改一行 VERSION 状态及对应文档，
状态语义已由 JL 在任务中明确指定。
