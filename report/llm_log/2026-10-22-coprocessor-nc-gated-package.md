# [2026-10-22] 协作记录：带 bit/hwh 的门禁 NC 包与历史包区分

> 标签：#coprocessor #NC #交付包 #SHA256 #门禁
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`db8bcbc` `84f70b8` `5c4463c` `f856d58` `aa47713`

## 1. 任务与初始提示词

整机门禁已在 Windows 侧真跑 PASS，产物已回写仓库；要求：把
`pynq_cop_40mhz.bit/.hwh` 放进 NC 包 payload，重算 `FILES.txt`/`SHA256SUMS`；
`VERSION` 写 `VIVADO=2026.1/40MHz 整机门禁 PASS`、`BOARD=UNVERIFIED`；
`EXPECTED_OUTPUTS.tsv` 保持 J02 锚点；更新 NC/检查清单并区分历史包。禁止声称板级通过。

## 2. 模型第一版方案

`package_coprocessor_nc.sh` 接受 bit、hwh 与 `gate_summary.txt` 三个参数，固定产物名
`pynq_cop_40mhz.bit/.hwh`，写入 `payload/`；打包时重跑 `bram_network` 生成 evidence 与
`EXPECTED_OUTPUTS.tsv`；`VERSION` 记录 commit、bit/hwh 状态、VIVADO/BOARD 状态；
`build/reports/pynq_cop_40mhz/` 加入 `.gitignore`。

## 3. 失败现象

1. 旧 `dist/cop-board-gate-b821aa1d0c1f`、`c4839f39be2d` 只有离板包，没有 bit/hwh；
   若混用会被误认为本轮可下载产物。
2. 早期打包只收 bit，缺 hwh 与 gate summary，NC 无法核对整机门禁证据。
3. 报告目录未忽略，`gate_summary.txt` 等生成物可能误入库。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 历史包无 bit/hwh | 不能冒充本轮产物 | `84f70b8` 在检查点明确区分历史包 | 状态清晰 |
| 2 | 只收 bit | 缺整机门禁证据 | `db8bcbc` 固定 bit/hwh 名 + 三态 VERSION | 包内齐全 |
| 3 | 报告可能入库 | 生成物卫生 | `.gitignore` 加 `build/reports/pynq_cop_40mhz/` | 未污染仓库 |
| 4 | 板级未验 | 不能写 PASS | `BOARD=UNVERIFIED_NEEDS_NC` | 边界诚实 |

## 5. 最终结论

最终包：`dist/cop-board-gate-f856d5861db0/`。

- bit SHA256：`b499cabe3d9a54274b93c659199336d6bbcceaf4d6fb93ea152ab0f414ef7e0a`
- hwh SHA256：`6a0a398b6d95ef940beb0f66c9c105547e82f3dd4f7bdbb967ac0f72564042c6`
- tar SHA256：`af1a343afc147bd0bb758d8c002f05e60f212d9447b87197c4102c85fd5809dc`
- 包内 `sha256sum -c SHA256SUMS` 全部 OK；预期输出保持 pattern `0/0/0`、zero `2/2/258`。
- `VERSION`：VIVADO 整机 40 MHz PASS；BOARD 仍 UNVERIFIED；JL 交付 ≠ 板级验收。

NC 下载命令（解包并核验后）：

```bat
board\scripts\program_soc.bat dist\cop-board-gate-f856d5861db0\payload\pynq_cop_40mhz.bit
```

## 6. 经验沉淀

- 触发条件：整机门禁通过后，需要把产物交给下游下载。
- 排查步骤：包内固定产物名；同时收 bit/hwh/gate summary；重算 SHA256；VERSION 分离
  “整机门禁”与“板上验收”；历史包明确标注，不复用旧 bit。
- 适用范围：任何带 EDA 产物的跨团队交付；换板卡需重打包。
#skill候选
