# [2026-09-20] 协作记录：PR #15 PYNQ-Z2 LED smoke test 独立复核——仿真/Vivado 全通过、XDC 官方溯源与误建分支归并

> 标签：#hardware #验证 #构建
> 平台：OpenCode ｜ 模型：opencode-go/deepseek-v4.1-flash
> 相关 commit：本条记录本身
> 用途：第三方 PR 的独立复核记录（代码审查 + 实跑验证 + 证据归档）；误建分支归并到 `dev/rtl` 的处理留痕

## 1. 任务与初始提示词

> 用户转来 PR #15 邮件（LibJiang：新增 `board/smoke_test/` PYNQ-Z2 LED 流水灯测试，仿真已过，Vivado/上板待验证）
> "目前请先进行代码审查，完成 Vivado 和上板验证后再更新验证结果"
> "他错误创建了一个分支，要想把这些提交给原来分给他的rtl分支，这个新分支要删除"

## 2. 模型第一版方案

1. 拉取 PR 全量 diff，逐文件审查（RTL / tb / XDC / build.tcl / README / .gitignore）
2. 独立复跑 iverilog 自检；XDC 引脚对照官方 PYNQ-Z2 Master XDC（下载 ZIP 实算 SHA256）
3. 用本机 Vivado 2026.1 实跑 `build.tcl` 全流程（综合→实现→时序/DRC 门禁→bitstream）
4. 分支归并：确认提交已在 `dev/rtl` 后删除误建分支

## 3. 失败现象（真实偏差）

1. **git 协议连不上 github.com**（两次 21 s 超时，`gh` API 正常）：改用 `gh api` 的 raw 接口逐文件取回 PR 内容做审查与复跑；期间网络间歇恢复一次，完成 `git fetch`
2. **MSYS2 `bash -lc` 下 PATH 无 `/ucrt64/bin`**：`run_iverilog.sh` 的 `command -v iverilog` 失败，ERR trap 只打印 `TEST FAILED: simulation command failed`，现象具有误导性；`export PATH=/ucrt64/bin:$PATH` 后 4 组分频全 PASS（记为对脚本的非阻塞可移植性建议：仓库既有脚本是自动定位 iverilog）
3. **审查疑点未先入为主**：`build.tcl` 的 `check_ports` 断言 `llength [get_ports] == 6`（总线端口对象语义不确定）——不靠猜，直接实跑验证，结果通过
4. **分支状态与预期不同**：准备"迁移提交"时发现 PR #15 已被组长本人合并（`state: MERGED`，merge commit `93eeb97`），实际只剩"删分支 + 本地同步"

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | git fetch 超时 | 机器 git 通道不稳定，但 GitHub API 可用 | 全程改用 `gh api`（raw contents / pulls / branches）完成审查、验证与删除分支 | ✅ |
| 2 | iverilog 脚本直接报 TEST FAILED | PATH 缺 ucrt64 导致 `command -v` 失败触发 ERR trap，并非仿真失败 | 补 PATH 后复跑 1/2/5/8 四组 | ✅ 全 PASS |
| 3 | `check_ports` 端口计数断言存疑 | 端口对象语义不应靠猜，构建脚本自带断言，实跑即判 | 实跑 `build.tcl` 全流程 | ✅ BUILD PASSED（WNS +4.094 / WHS +0.052，0 失败端点） |
| 4 | 用户指出分支误建、需并入 `dev/rtl` 并删除 | PR base 本就是 `dev/rtl` 且已合并；`1fb6787` 在 `dev/rtl` 祖先链上、文件齐全 | 删除远端 `test/pynq-z2-smoke`；本地清理跟踪引用并把 `dev/rtl` 快进到 `93eeb97` | ✅ 远端仅剩 main / dev/rtl / dev/verify / dev/bench |

## 5. 最终结论

- **复核通过**：iverilog 13.0（4 组）与 Vivado 2026.1（BUILD PASSED）双通过；XDC 实算 SHA256 `07441E99…FE73` 与官方 Master XDC 成员逐字节一致，引脚/时钟与 Xilinx 官方 `base.xdc` 一致
- **证据归档**：`data/logs/2026-09-20-pynq-z2-smoke-vivado/`（README + timing/utilization/drc 报告 + iverilog 日志；bitstream SHA256 `B8D9EC9B…2E54`）
- **分支归并**：误建分支已删除，提交经 PR #15 合并入 `dev/rtl`（`93eeb97`）；本地 `dev/rtl` 已同步
- **遗留（`dev/rtl → main` 前置）**：理解门槛（逐段讲解 + 3 题 + llm_log）与真实上板验证；PR #15 评论区已留 Vivado 结果
- 复核非阻塞建议已反馈：脚本 iverilog 自动定位、README 去除作者本机路径、`board/README.md` 登记 `smoke_test/` 子目录

## 6. 经验沉淀

- 触发条件：独立复核队友/第三方的硬件验证类 PR（不是只看 diff，要实跑） #skill候选
- 排查步骤：
  1. 先用 PR 自带断言实跑一遍（构建脚本里的门禁本身就是判据），不要用"我觉得它会挂"代替运行
  2. 引脚约束做**溯源核验**：下载官方 Master XDC、实算 SHA256、与设计 XDC 逐项对照——比"看起来对"可靠
  3. 网络受限时 GitHub API（`gh api` raw/contents）可替代 git 协议完成审查、取文件、删分支
  4. 分支误建的处理：确认提交已在目标分支（`merge-base --is-ancestor` + 文件存在）后再删源分支，顺序不能反
- 适用范围（换题目/换板卡是否成立）：成立；任何"独立验证 + 证据归档 + 分支治理"场景均适用
