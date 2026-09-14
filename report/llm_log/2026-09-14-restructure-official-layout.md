# [2026-09-14] 协作记录：仓库结构对齐指南 §3.3.5.4——metrics 并入 data、sw 并入 src

> 标签：#仓库合规 #架构决策 #文档
> 平台：OpenCode ｜ 模型：deepseek-flash (deepseek/deepseek-flash)
> 相关 commit：`metrics→data`、`sw→src`、README 对照表重写 + 本条记录本身

## 1. 任务与初始提示词

> "根据官方的文件结构规范来整理文件结构"

背景：`docs/amd_track_awards.md`（2026-09-11 调研）与 9/14 归档的 7 企业指南摘要都已入库，用户据此提出按官方规范整理。

## 2. 模型第一版方案

对照仓库 README 既有"目录对照表"检查合规性——该表引用指南"3.2.5.5"。

## 3. 失败现象（真实偏差）

1. **对错赛道编号**：README 对照表引用的 §3.2.5.5 是**具身智能赛道**的推荐结构（fpga/、host/、metrics/）；本队报名的**自主选题赛道**推荐结构是 **§3.3.5.4**（src/sim/build/board/data/skill/report），两者不同——此前 metrics/ 目录正是按另一赛道的结构建的。
2. **历史遗留的未提交删除**：`report/llm_log/2026-09-14-understanding-gate.md` 在 git 索引中存在但磁盘上已被删除（前一会话遗留，未提交）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 用户三决策：docs/ 保留并登记；sw 并入 src；被删 llm_log 提交删除 | docs/ 走指南明示的"非强制 + 对照说明"豁免，改动最小；sw/ 官方 src 定义（"RTL/HLS/PS 侧软件"）本就涵盖 | 顶层收敛为官方 7 目录 + docs/ 登记 | ✅ 顶层 = README/LICENSE + 7 官方目录 |
| 2 | metrics 并入 data | `data/` 官方定义"测试数据与参考结果"与 metrics.csv/logs/scripts/evidence 语义完全吻合，且 `data/README.md` 最初规划本就含 metrics.csv | `git mv` 四件套，README 合并，引用修正（README/amd_track_awards/proposal_upgrade） | ✅ commit 完成 |
| 3 | sw 并入 src | 指南 `src/` = "设计源码（RTL / HLS / **PS 侧软件**）"，固件与上位机均属之 | `git mv` 两个子目录；**同步修正 2 个 tb 的 `$readmemh` 相对路径**与 .gitignore/文档引用；立即跑 `sim/scripts/run_iverilog.sh` | ✅ 双冒烟 PASS（路径无回归） |
| 4 | README 对照表重写 | 引用编号 3.2.5.5 → **§3.3.5.4**；docs/ 登记为非强制扩展；.github/.opencode 标注为仓库基础设施 | 目录树 + 对照表全新 | ✅ |

## 5. 最终结论

- 顶层结构对齐指南 §3.3.5.4：`README.md / LICENSE / src / sim / build / board / data / skill / report`（+ 非强制 `docs/`、基础设施 `.github/ .gitignore .opencode/`）
- `data/`：metrics.csv + logs + scripts + evidence（含演示级指标行，采集约定不变）
- `src/`：RTL 四子目录 + riscv_fw + pynq_host
- 对照表在 README 中重写，编号更正为 §3.3.5.4
- llm_log 历史（2026-09-11 及更早）中出现的旧路径一律不改——它们是历史快照，本条记录即为指针
- 提交 `understanding-gate.md` 的删除（已被 `docs/code_review_checklist.md` 与 `.opencode/skill/understand-gate` 取代）

## 6. 经验沉淀

- 触发条件：按"官方推荐目录"整理仓库/检查合规 #skill候选
- 排查步骤：
  1. **先确认自己赛道的那一节**：同一份指南里不同赛道（具身智能 §3.2 vs 自主选题 §3.3）的推荐目录不同，引用编号要落到本赛道（§3.3.5.4）
  2. 官方结构"非强制 + 对照说明"是明确豁免通道：额外目录要么并入语义吻合的官方目录，要么在 README 对照表登记理由
  3. 移动目录必须**全库 grep 引用**（含 .gitignore 的路径模式、tb 的相对路径），且移动后立即跑一遍可执行验证（冒烟仿真）证明无回归
  4. 历史记录（llm_log）中的旧路径是时间戳证据，只追加不改写
- 适用范围：换赛题、换赛道、换仓库均成立
