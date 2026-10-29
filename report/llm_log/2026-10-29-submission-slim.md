# prompt 要点 + 理解题：比赛提交瘦身 PR A（2026-10-29）

## 背景 prompt

用户口径：比赛 11/4 18:00 提交本仓库（README 即参赛作品仓库）。仓库对评委有大量内部过程产物，
代码存在 v0 遗留与重复件，要求「评委视角瘦身」；同时明确四项裁决：

1. 主页即仓库，直接清 main（git 历史留底，不改写历史）；
2. data/logs 155 个会话目录只保留被官方锚点（plan.md / README / metrics.csv / tech-report / 收口报告 / 契约）引用的；
3. report/llm_log 219 篇大模型协作记录全部保留（加分项定位不变）；
4. 代码裁剪取激进档，但「已进入出厂 bit 的例化路径（vision_top / pynq_cop_top / pynq_z2_top / soc_top 及其子模块）本轮不动」。

## 本步（PR A）做了什么

- 收编另一会话遗留的 25 文件 doc 收尾为独立底座 commit（cd7290e）。
- 引用矩阵审计：以官方锚点文档全文为语料扫描 data/logs、data/evidence、sim、build、docs、src 的引用，
  三档清单输出 `others/submission-slim-20261029/step0-audit.md`（本机不进仓库）。
- git rm 4,003 个 tracked 文件（删非引用的会话日志/证据外包包/过程文档/一次性探针脚本/半 .dis/ISSUE 模板），
  删前把 data/logs、data/evidence、docs、build、sim/scripts 全目录 + 零散 src 文件打包 180 MiB 备份到
  `others/submission-slim-backup-20261029.tar.gz`，满足「砍掉的都保留在本地」。
- 断链修复：初始 76 处断链。复活被冻结契约/官方报告/board 存证引用的 12 组目标
  （6 runbook + 2 research + 2 archive + 9 个 data/logs 会话目录 + data/logs/README.md + pi-camera runbook）；
  其余在引用方文档以「git 历史（88ac1c4 前）…」文字指针收口；docs/README.md 与 project-map.md 按新结构重写。
- 门禁：`python sim/scripts/check_repo_hygiene.py` 从 FAIL（76 断链+14 ghost+stale index+root）收敛到 PASS 0 ERROR；
  index_runs.py --write 重生成 logs/evidence 索引；`git diff --check` 干净。

## 三道理解题与答案（用户确认通过）

A. 为什么 sim 回归域「默认保留」而不是「审计不到就不留」？
   —— 回归驱动用变量拼名与 glob（如 `sim/vision/test_$name.py`、`tb_*.v`）枚举测试件，
      字面名匹配必然漏检，审计初版就曾把协处理器整域误标为可砍。因此脚本名级审计在此域不可信，
      需求侧以「保留后回归全量 PASS」为硬门，删除候选只能按显式运维模式（pi_*、serial_*、n03 收尾等）圈定。
B. 什么才算救活一个数据包的合格引用？
   —— 必须来自评委可达的官方叙事锚点（README/plan/metrics/收口报告/冻结契约/现状 runbook）。
      自我引用（bench 脚本注释指向自家数据目录，如 arm-localize-baseline 45 MiB）不构成锚点；
      在正确性语义上仅引用方被保留文档指向的历史会话目录数作复活口径。
C. 为什么用 git rm 而不是改历史？
   —— AGENTS §2 禁 reset/强推覆盖既有提交；git rm 只移动可见面，任何删除件都完整留在历史 commit 与
      本地 180 MiB tar 备份中，可按 commit 恢复，提交物干净且可回滚。

## 待办 / 未实现

- PR B（活代码剪枝）：mock 服务 parse_trigger_ref 搬迁、协处理器未例化变体删除、走访 sim/vision 诊断 tb——全部待回归；
- 全量回归矩阵一次跑齐（核 24 档 + 视觉 RTL/Python + 检查链 + 协处理器仿真/参考）；
- docs/tech-report 与 poster 内 EXE 时代配图（fig_exe.png / exe.png）需换为网页端形态（用户材料修订线，非本步范围）。
