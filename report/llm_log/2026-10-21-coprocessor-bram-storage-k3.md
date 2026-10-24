# [2026-10-21] 协作记录：K3 单拍 BRAM 存储与 `bram_network` 对拍入口

> 标签：#coprocessor #存储 #BRAM #K3 #回归入口
> 平台：Codex + OpenCode（VS Code/WSL）｜ 模型：GPT-5 / deepseek-flash
> 相关 commit：`097fbd7` `45c677f` `62168f8`；本轮 runner/TB 接入见 `git log -1`

## 1. 任务与初始提示词

K2 只加约束：文件保持 PLAN/UNVERIFIED，payload 布局以 manifest 为唯一权威，
只有 K3 逐元素对拍 + Windows 侧 Vivado 通过后才能升级状态。
K3：用带真实读延迟的 BRAM 替换行为级数组，保留 parameter 在行为级/BRAM 间切换且默认行为级；
BRAM 模式逐元素比对 J02 golden（pattern + zero），并加“读延迟边界”用例，错误必须可见。

## 2. 模型第一版方案

新增 `cop_bram_storage.v`：`(* ram_style="block" *)` 存储、16 路×64-bit 权重 bank、
同步单拍读、窄口 init 装载、ping/pong/gap 写口。新增 `tb_cop_bram_latency.v`：
标准单拍读正确，提前/延后一拍采样都产生可观察不匹配。
`tb_cnn_sequencer` 增加 `USE_BRAM=0` 默认参数；`USE_BRAM=1` 时经 init 口把 ROI、权重、
bias/multiplier/shift 装入 BRAM。runner 新增 `bram_network` 模式，
用 `-P tb_cnn_sequencer.USE_BRAM=1` 编译。

## 3. 失败现象

1. 只按容量估算权重约 9 块，无法每拍供给 128 B 权重——容量够、端口不够（OPEN-K2-1）。
2. WSL 无 Vivado，BRAM 推断数量、端口模式与时序都不能确认。
3. 若 `bram_network` 沿用 `+fault_tests`：故障注入只存在于行为级路径，BRAM 模式不会真正注入，
   故障用例会失去意义。
4. BRAM 模式 `cycles=472594`，行为级为 `472593`，相差 1 拍；逐元素结果仍一致。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 9 块容量估算不满足带宽 | 容量与带宽混为一谈 | 16 路×64-bit 权重 bank | K2 方案自洽，标 OPEN-K2-1 |
| 2 | 无 Vivado | 不能宣称已实现 | K2 全文 PLAN/UNVERIFIED | 未越权 |
| 3 | BRAM 模式跑 fault_tests 无意义 | 故障注入只在行为级 | `bram_network` 跳过 `+fault_tests` | 模式语义清晰 |
| 4 | 只有手工 `-P` 命令 | 不满足脚本入口可复现 | runner 加 `bram_network` | 官方入口 PASS |

## 5. 最终结论

```text
$ bash sim/scripts/run_coprocessor_iverilog.sh bram_network   # 62168f8 起先跑延迟边界再跑整网
PASS: K3-LATENCY nominal one-cycle BRAM read matches; early/late samples mismatch visibly
PASS: ... pattern all 9225 packed words/73795 elements match integer network;
      logits=01fd01 class=0 margin=0 cycles=472594
PASS: ... zero all 9225 packed words/73795 elements match integer network;
      logits=04fd02 class=2 margin=2 cycles=472594
```

默认行为级 `network` 仍 PASS（含 fault/watchdog），`pattern`/`zero` 各 73,795 元素匹配，
`cycles=472593`。实体 BRAM 推断、端口模式、综合/时序与板级仍 **UNVERIFIED**；
K4/K5 的脚本与交接见 `2026-10-21-coprocessor-k4-vivado-gate.md` 与
`2026-10-21-coprocessor-k5-nc-handoff.md`。

## 6. 经验沉淀

- 触发条件：把行为级数组替换成真实 BRAM，同时必须保持既有 golden 不变。
- 排查步骤：保留默认行为级参数；用窄口 init 装载；两种模式都做逐元素比对；
  另加“提前/延后一拍必须可见地失败”的延迟边界用例；故障注入不能跨模式盲用。
- 适用范围：任何存储模型替换（BRAM/DDR/URAM）；Vivado 推断与板级仍需单独验证。
#skill候选
