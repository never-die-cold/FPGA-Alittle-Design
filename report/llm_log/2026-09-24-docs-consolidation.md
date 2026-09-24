# [2026-09-24] 协作记录：docs 整理——人读入口 + 文档合并去重（12 → 8 篇）

> 标签：#docs #工具链（文档工程）
> 平台：OpenCode ｜ 模型：deepseek-v4-pro
> 相关 commit：`f359683`（入口+workflow 三合一）、`a9c2ab8`（track_research 二合一）、`e8c0057`（CoreMark 契约+计划合并）、`a7b69ab`（删 repo_structure + 本条记录）

## 1. 任务与初始提示词

> 项目感觉在膨胀——文件夹关系复杂、文档 AI 味重、人难以阅读管理；评估后按"第 2 档：入口 + 合并重复"执行整理。

背景：仓库 184 个跟踪文件里 Markdown 占 4.2k 行（RTL 仅 1.5k 行），docs/ 有 12 篇文档且相互交叉引用；repo_structure.md 已过期（build/ 早已不是占位）。用户选择保留赛题 7 目录骨架、合并同类文档、新增人类唯一入口。

## 2. 方案要点

- 新增 `docs/README.md`：目录地图 + 四类信息归属（仿真日志→`data/logs`、上板→`board/logs`、协作→`report/llm_log`、契约→`design_v0.md`）+ 写作规范 5 条 + 旧路径对照
- 三合一 `docs/workflow.md`（kickoff_checklist + code_review_checklist + prep_checklist，kickoff 的开工三件事骨架保留）
- 二合一 `docs/track_research.md`（amd_track_awards + track_guides_2026_summary，双源互证变节内引用）
- 二合一 `docs/coremark.md`（coremark_tb_contract §1–§7 编号原样保留 + coremark_plan 转为附录 A）
- 删除 `docs/repo_structure.md`（目录职责已由各目录 README 承担）
- 全库约 30 处链接/注释路径修复；`report/llm_log/`、`src/riscv/done/`、`data/evidence/*.patch` 按"历史不改写"铁律保持原样

## 3. 偏差与修正（评估阶段的决策变更）

| 轮次 | 初判 | 依据 | 修正 |
|:---|:---|:---|:---|
| 1 | board/logs 与 data/logs 重复，合并 | 读内容后确认是真实边界：上板实测记录 vs 仿真/构建证据 | 不合并，归属规则写进 docs/README.md |
| 2 | CoreMark 两篇现在合并 | 约 12 处固件/tb/脚本注释当契约引用 | 用户拍板现在就合并；方案为契约 §号不变、只换文件名，注释改动全部是注释行 |

## 4. 验证结果

- `rg` 旧文件名：残留仅在 llm_log/、done/、evidence patch（历史快照）+ 新文档合并说明（有意保留）
- `git diff -U0`：`.c/.h/.ld/.v/Makefile` 改动全部是注释行
- `bash sim/scripts/run_iverilog.sh coremark` 复跑 PASS：cycles=21275738、crcfinal=0x8799、CPI=2.105，与入库证据一致
- `git diff --check` 干净

## 5. 最终结论

docs/ 12 → 8 篇，新增人读入口；所有合并用 `git mv` 保留历史；评审所需的 evidence 链（llm_log、evidence patch、golden）零改动。

## 6. 经验沉淀

- 触发条件：文档数量超过代码数量、交叉引用成网、同一规则多处复制。
- 排查步骤：
  1. 先统计（行数/链接数/过期点），找"同一信息住多处"的证据再动手；
  2. 合并时保住被引用方的编号体系（契约 §号），引用方只换文件名，diff 最小化；
  3. 历史文档（日志/归档/证据快照）一律冻结，用"旧路径对照表"兜底而不是改写历史。
- 适用范围：任何文档膨胀的仓库均成立。 #skill候选
