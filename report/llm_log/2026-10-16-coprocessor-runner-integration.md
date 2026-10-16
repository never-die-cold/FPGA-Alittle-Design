# [2026-10-16] 协作记录：sim runner 模块——把 mac_lane / dot8 接入协处理器回归入口

> 标签：#coprocessor #工具链 #验证
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-5 系列；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：`sim/scripts/run_coprocessor_iverilog.sh`、`sim/scripts/run_iverilog.sh` 随本轮提交；被测单元见 `2026-10-13-coprocessor-mac-lane.md`、`2026-10-13-coprocessor-dot8.md`

## 1. 任务与初始提示词

上一步以 origin 为基线补回了本地独有的 `mac_lane.v` / `dot8.v` 单元，但它们的 tb 还没有接入团队的协处理器回归入口——**孤立、无法一键复现**。本轮把它们接进 runner（含 `all`）。

## 2. 模型第一版方案

- `sim/scripts/run_coprocessor_iverilog.sh`：新增 `mac_lane)` / `dot8)` 两个模式，并纳入 `all`（复用其 `run_test`，按 `src/coprocessor/*.v` 编译、跑 `tb_<name>`）。
- `sim/scripts/run_iverilog.sh`：新增前端 `cop_mac_lane` / `cop_dot8`，并更新用法串。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 无功能失败；两步均一次通过。
2. **未决**：本轮只改脚本、不涉及 Vivado/综合/上板；这些单元的时序/资源未验证。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 新单元未被回归覆盖 | 需接入单独模式 + `all` | `mac_lane`/`dot8` 模式并纳入 `all` | ✅ `cop_mac_lane`/`cop_dot8` PASS |
| 2 | 顶层入口不统一 | 加 `run_iverilog.sh` 前端 | `cop_mac_lane`/`cop_dot8` | ✅ `coprocessor all` 含两步且全 PASS |

## 5. 最终结论

`mac_lane`（7 向量）、`dot8`（5 向量）现已接入团队 runner：`bash sim/scripts/run_iverilog.sh cop_mac_lane` / `cop_dot8` 可单独跑，`coprocessor all`（及总 `all`）已包含它们，与 origin 既有 `int8_mac`/`mac_array`/`pipeline`/`conv`/`network` 一起全 PASS。

## 6. 经验沉淀

- 新增 RTL 单元**必须同时接入单独模式与 `all`**，否则孤立、无回归保护；
- 顶层入口（`run_iverilog.sh`）与底层 runner 保持**同名子命令**，便于脚本/证据对照。 #skill候选
