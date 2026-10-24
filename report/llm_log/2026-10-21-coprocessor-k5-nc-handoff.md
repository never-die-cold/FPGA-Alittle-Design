# [2026-10-21] 协作记录：K5 NC 交付包与三级状态交接

> 标签：#coprocessor #NC #交付包 #SHA256 #交接
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`7b2df64` `c4839f3`

## 1. 任务与初始提示词

K5：新增打包脚本，生成文件清单 + 每文件 SHA256 + 版本号 + 预期输出表（数值/CRC 取自
J02 golden 与仿真结果），输出到 `dist/`（gitignore）；产出 NC 交接文档，含下载、启动与复位、
“应该看到什么”、失败恢复、已知限制，并明示三类状态：仿真跑通 / 综合实现通过 / 板上跑通。
必须写清：JL 交付 ≠ 板级验收；NC 负责下载与现场稳定；WC 负责软件接入。

## 2. 模型第一版方案

`sim/scripts/package_coprocessor_nc.sh` 在打包时重跑 `bram_network`，从 manifest、
`result.txt` 与 BRAM 日志重新生成 `EXPECTED_OUTPUTS.tsv`，不抄手写表；收集源码、golden、
日志到 `dist/cop-board-gate-<commit>/`，生成 `FILES.txt`、`SHA256SUMS`、`VERSION` 和
`.tar.gz + .sha256`。`VERSION` 中 `VIVADO`/`BOARD` 固定为 UNVERIFIED，除非有对应证据。

## 3. 失败现象

1. 本轮没有 JL 门禁通过的 bitstream：若包内放旧 bitstream，会被误当成可下载结果。
2. 预期输出表若手写，容易与当前提交/仿真结果漂移。
3. `dist/` 产物若入库，会把每次生成的二进制和临时包带进仓库。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 没有 JL bitstream | 不能伪造可下载状态 | 只打离板包，`BITSTREAM=UNVERIFIED` | 状态诚实 |
| 2 | 预期值可能漂移 | 手写表不可复现 | 打包时重跑 K3 并从日志/manifest 生成 TSV | 与当前提交绑定 |
| 3 | 用户后续提供 bitstream | 需区分“JL 提供”与“板上通过” | 标记 `JL_SUPPLIED_UNVERIFIED_ON_BOARD` | 不冒充板级验收 |
| 4 | `dist/` 可能入库 | 仓库卫生 | `.gitignore` + 每次重新生成/校验 | 未提交生成物 |

## 5. 最终结论

打包脚本与 `docs/coprocessor-nc-handoff.md` 已交付；实际生成并校验：64 个文件 SHA256 全部
OK，归档自身 SHA256 也 OK。`VERSION` 保持 `VIVADO=UNVERIFIED_NEEDS_WINDOWS`、
`BOARD=UNVERIFIED_NEEDS_NC`。三类状态：仿真 PASS（行为级 + BRAM 逐元素）、综合/实现
UNVERIFIED、板上 UNVERIFIED。NC 解包后必须先 `sha256sum -c SHA256SUMS`。

## 6. 经验沉淀

- 触发条件：把“仿真通过”交付给下游下载/上板。
- 排查步骤：打包时重跑证据而不是抄结论；版本文件里显式写三级状态；无 bitstream 就只交离板包；
  JL 提供的 bitstream 也只标“未上板验证”。
- 适用范围：任何跨团队软硬件交付；换板卡仍需重新生成 golden 与预期输出。
#skill候选
