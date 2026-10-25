# [2026-10-25] 协作记录：干净重建门禁与 DMA-16 上板包

> 标签：#coprocessor #Vivado #门禁 #NC #交付包
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`759744b` `d735d6f`

## 1. 任务与初始提示词

DMA-16/驻留固件修改后，用干净仓库重跑 Windows Vivado 2026.1 整机 40 MHz 门禁；
只有通过才采纳新 bit/hwh/xsa 并重打 NC 包；旧包一律不进入上传候选；
`LOADER` 只可标“离板阻塞已解除、待板上验证”，`BOARD`/`BOARD_CLOCK` 保持 UNVERIFIED。

## 2. 模型第一版方案

丢弃与固件提交并发的首构 bit（前缀 `9e1b24e2`）；从干净仓库重建并跑门禁，
包源固定为 `759744b`；重新生成 bit/hwh/xsa 哈希，用 `package_coprocessor_nc.sh` 重打包，
保留 `EXPECTED_OUTPUTS.tsv` 与 J02 锚点，`VERSION` 写三态与 loader 阻塞解除说明。

## 3. 失败现象

1. 同日首构 bit 与固件提交并发，产物不可信，已作废。
2. 旧包 `d66916c49b80`（DMA-14/一次性固件）、`21c4e751bbe8`、`f856d5861db0` 均不应再上传。
3. `LOADER` 阻塞只是离板解除；板上 FCLK/首读仍未验证，不能写 PASS。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 首构 bit 与固件并发 | 产物不可追溯 | 丢弃 `9e1b24e2`，干净重建 | 新门禁 PASS |
| 2 | 旧包仍在 dist | 防止误上传 | 只选 `759744b99891` 包 | 旧包排除 |
| 3 | loader 仅离板验证 | 不能写板上 PASS | `LOADER=BLOCKERS_RESOLVED_PENDING_BOARD_VALIDATION` | 状态诚实 |
| 4 | 板上 FCLK 未验 | 必须保留阻塞 | `BOARD_CLOCK=UNVERIFIED_NEEDS_40MHZ_READBACK` | 可追溯 |

## 5. 最终结论

干净门禁 PASS：WNS **+2.771 ns**、DSP **136/220**、BRAM36 **69/140**、LATCHES=0、
DRC blocking=0；CDC-15=73、CDC-3=12、CDC-6=7 全部命中 allowlist，无 Critical。

- bit：`d14a4bd037b1809c74fe511f1c7667edbc6bd6ecac8a8712a423946f5f1e2a1a`
- hwh：`928f0d594ccbb83c8bd17e5ed284a6f2849e1b598c28073c779afb1ff9849107`（`C_SG_LENGTH_WIDTH=16`）
- xsa：`755f70337bdc5a06da0dcaa715c512806b7011efa09f95128314cb78a2ad96ec`
- 包：`dist/cop-board-gate-759744b99891/`；tar SHA256
  `7160fffb44d6a2869ae6696eb1dacdca6f62b128c6abaef8d24f3cf8d054432b`
- 包内 `sha256sum -c SHA256SUMS` 全部 OK；期望输出仍为 pattern `0/0/0`、zero `2/2/258`。

NC 解包后先执行 `sudo -E python3 payload/tools/cop_payload_loader.py clock --reads 20`；
只有 FCLK1=40 MHz 且 20 次 STATUS 首读全为 `0x1` 才继续 zero/pattern。
`BOARD`/`BOARD_CLOCK` 仍 UNVERIFIED。

## 6. 经验沉淀

- 触发条件：RTL/固件改动后重新出 bit，需要重打上板包。
- 排查步骤：先确认构建与源码提交一致（丢弃并发构建）；再跑整机门禁；用新哈希重打包；
  明确列出作废旧包；loader 阻塞解除与板上验证分开写。
- 适用范围：所有 EDA 产物交付；换 Vivado 版本或 BD 位宽需重新出包。
#skill候选
