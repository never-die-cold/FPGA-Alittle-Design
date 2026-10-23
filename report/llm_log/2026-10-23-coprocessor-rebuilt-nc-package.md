# [2026-10-23] 协作记录：修复源码后的 NC 包重打与哈希废止规则

> 标签：#coprocessor #NC #交付包 #SHA256 #复现
> 平台：Codex + JL（Windows Vivado 2026.1）｜ 模型：GPT-5
> 相关 commit：`21c4e75` `af64a5f`

## 1. 任务与初始提示词

JL 用修复后的源码两次独立复跑整机门禁，均 PASS；新 bit/hwh 已回写。要求：更新文档中的
新哈希；重打 NC 包并更新 `FILES.txt`/`SHA256SUMS`/`VERSION`；
`VERSION` 写 `BITSTREAM=JL_GATE_PASSED_UNVERIFIED_ON_BOARD`、
`VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM`、`BOARD=UNVERIFIED_NEEDS_NC`；
注明“两次独立构建仅文件头 4 字节差异，网表等价”；`EXPECTED_OUTPUTS.tsv` 数值不变；
旧包禁止继续沿用。

## 2. 模型第一版方案

`package_coprocessor_nc.sh` 的 `VERSION` 增加
`BUILD_REPRO=2_INDEPENDENT_BUILDS_ONLY_4_HEADER_BYTES_DIFFER_NETLIST_EQUIVALENT`；
`EXPECTED_OUTPUTS.tsv` 改 `write_bytes`（UTF-8+LF）；从 `21c4e75` 重打包，
包内固定 `pynq_cop_40mhz.bit/.hwh`，重算清单与 SHA256；文档换新哈希并标旧包废止。

## 3. 失败现象

1. 旧包 `dist/cop-board-gate-f856d5861db0/` 的 bit 是旧构建，SHA256 与新构建不符，
   继续沿用会让 NC 下载到与门禁证据不一致的位流。
2. 两次独立构建的 bit 仅文件头 4 字节不同，SHA256 不同但网表等价；若只看哈希会误判为
   不同设计，若忽略哈希又会放过真实差异。
3. `EXPECTED_OUTPUTS.tsv` 若用文本模式写，Windows 宿主可能引入 CRLF，影响包内复算。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 旧包 bit 哈希不符 | 旧构建不可复用 | 从 `21c4e75` 重打包，旧包标废止 | 新包生成 |
| 2 | 两次 bit 仅头 4 B 不同 | 需记录“等价但哈希不同” | VERSION 加 BUILD_REPRO 说明 | 状态可追溯 |
| 3 | 预期输出可能漂移 | 必须重跑并逐元素校验 | 打包时重跑 K3，保持 0/0/0 与 2/2/258 | `sha256sum -c` 全 OK |
| 4 | 文本换行风险 | 显式字节写入 | `EXPECTED_OUTPUTS.tsv` 用 `write_bytes` | LF-only |

## 5. 最终结论

当前包：`dist/cop-board-gate-21c4e751bbe8/`。

- bit SHA256：`7e1e34304ef71efdfe86ec3e6dbeead6ab419c741806a3334a71474746aa0b6c`
- hwh SHA256：`cba4d12c58213897c0dbdafd327348ce5d4bd9d21dad6d5a469eb44bd03d799d`
- tar SHA256：`d74189b9e1db2d0b7b0d7256a280ec166be8b35868b9cb01664a277bd8e76046`
- `VERSION`：BITSTREAM=JL_GATE_PASSED_UNVERIFIED_ON_BOARD；
  VIVADO=PASS_2026.1_40MHZ_WHOLE_SYSTEM；BOARD=UNVERIFIED_NEEDS_NC；含 BUILD_REPRO 说明。
- 包内 `sha256sum -c SHA256SUMS` 全部 OK；预期输出仍为 pattern `0/0/0`、zero `2/2/258`。
- 旧 `dist/cop-board-gate-f856d5861db0/` 已废止；JL 门禁通过 ≠ 板级验收。

NC 下载命令（解包并核验后）：

```bat
board\scripts\program_soc.bat dist\cop-board-gate-21c4e751bbe8\payload\pynq_cop_40mhz.bit
```

## 6. 经验沉淀

- 触发条件：修复源码后重新出 bit，但旧交付包仍在目录里。
- 排查步骤：包与源 HEAD 绑定；重打包时重跑证据；新哈希写进 VERSION/文档；
  旧包明确标废止；对“仅文件头不同”的重复构建，记录网表等价依据而不是只比哈希。
- 适用范围：所有带 EDA 产物的交付；换 Vivado 版本或器件需重新定义可复现口径。
#skill候选
