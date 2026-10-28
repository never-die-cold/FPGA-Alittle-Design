# 2026-10-28 前端定为 HTML 网页端：移除 EXE 形态与管理性文档内容

> 请求：①核对文档与代码并精简、去防御性表达（提供 anti-defensive writing skill）；②前端已定为
> HTML 网页端，把仓库中全部 EXE 相关部分移除，仅本地留备份；③负责人、排期、看板等管理性内容全部去掉，
> 仓库只服务提交前（2026-11-4）的优化与调整。文档类改动豁免理解题（用户 2026-10-28 确认）。

## 决策点

1. **EXE 相关 = 代码 + 构建 + 测试 + 当前态文档口径**；带日期的历史存证（`data/logs/**`、
   `report/llm_log/**`、plan.md §3.1 带日期条目与变更记录表、契约决策表、带日期引文块）不改写——
   记录/代码/时间线互锁，改了就假。
2. **`rounds.py`/`records.py`/`export_records.py` 不删、移入 `src/pynq_host/`**：三者是
   D2/D3/D5/D8–D10 冻结轮次/记录/CSV 语义的纯 stdlib 实现，被服务端回归
   `test_cop_service.py`、`test_vision_live_standin.py` 引用，删除会断检查链回归；
   docstring 同步改为"前端参考实现"，网页端重建记录/CSV 时以此为参考。
3. **网页端字体自持**：字体目录从 `src/vision_client/assets/fonts/` 移到
   `src/web_client/assets/fonts/`，`index.html` 的 `@font-face` 改相对路径。
4. **plan.md 瘦身口径**：删 §1.2 里程碑表（保留 11/3 复验、11/4 提交两行）、§2 分工与协作
   （保留 3 条仓库规矩：PR 合入、禁强推、理解门槛 commit）、§3.2 交付看板、§3.3 交接顺序、
   §5.3 后续模块安排；保留 §1.1/§1.3 产品边界、§1.4 验收口径（EXE→前端措辞）、§3.1 当前状态、
   §3.4 风险表、§3.5 完成条件、§4 接口入口。
5. **历史 runbook/看板按仓库惯例加"历史快照"横幅**：`runbooks/offline-inspection.md`、
   `non-algorithm-plan.md`（其回放入口/EXE 行随 EXE 移除失效）。
6. **tech-report 诚实重写**：`build_tech_report.py` 25+7 处、`make_tech_report_figures.py` 4 处
   EXE 叙述改为网页端口径；真实 UVC/HTTP 检查记录联调事实保留（改述为"检查记录链路已在真实
   UVC 与 HTTP 下联调验证"），不虚构网页端已接真实数据；图 3-2 截图注明"截图为原视口形态"。
7. **冻结契约加更新注（追加不改写）**：`vision-sync-protocol-decisions.md`、
   `vision-live-semantics.md` 头部加"前端形态改为网页端，本文所称 EXE 指当时实现载体，
   协议语义不变"。
8. **去人名范围**：README/plan/project-map/各模块 README/视觉契约观众注/核专项计划 §2 分工表与
   §6.1 负责人列（改为"核开发线/验证线"）；契约与决策单变更记录表、带日期分工注记（如
   design_v0.md §6 的 2026-10-01 注）作为历史保留。

## 改动（53 个文件，+182/−2019）

- 删除：`src/vision_client/`（README、hud/hud_text/preview/replay_viewer/requirements）、
  `sim/scripts/build_vision_client.ps1`、客户端专属测试 5 个、
  `docs/project-closeout-three-person-checklist.md`。
- 移动：字体目录 → `src/web_client/assets/fonts/`；rounds/records/export_records → `src/pynq_host/`。
- 修改：README.md、plan.md、docs/README.md、docs/project-map.md、docs/onboarding.md、
  src/web_client/README.md、src/web_client/index.html、src/README.md、src/vision/README.md、
  src/vision/design_v0.md、src/coprocessor/README.md、src/pynq_host/README.md、src/pynq_host/ONBOARD.md、
  两个回归脚本名单、5 个保留测试、两个契约（加注）、tech-report 两脚本与 README、
  file-guide 两个 roles.json（清理已删文件条目）。
- 备份：`E:\Projects\FPGA-Alittle-Design-local-backup-20261028\`（23 文件，5.0 MB，仓库外）。

## 验证

- `bash sim/scripts/run_vision_python.sh`：exit 0（20 组，原 21 组减 vision_joint）。
- `bash sim/scripts/run_inspection_python.sh`：exit 0（17 组，原 19 组减 inspection_viewer/cop_exe_round）。
- 移动后单测复跑：vision_rounds / vision_records / vision_export / vision_live_standin / cop_service 全 PASS。
- `python -m py_compile`：build_tech_report.py、make_tech_report_figures.py PASS。
- `git diff --check`：CLEAN。残余 EXE 字样仅在历史存证与溯源标注位置（决策 1/8）。

## 待办（未实现）

- 网页端三根线：真实视频流接入、板端 `:8765` `/v1/check`·`/v1/status` 接线、网页端检查记录与 CSV 导出。
- 简介/材料口径：tech-report 已按网页端重写，答辩材料中"实时/全链"表述不得越过 §3.1 记录的验证边界。
- 本次改动**未 commit**：待确认后提交。

## 补充（同日）：本地非仓库文件归入 others/

用户要求把本地不应进 GitHub 的东西全部移入 `E:\Projects\FPGA-Alittle-Design\others\`（仓库内目录，
已加 .gitignore `/others/`，永不入库）：

- `others/vivado/`：根目录与 `sim/` 的 Vivado/XSim 运行日志（vivado*.jou/log、clockInfo.txt、.Xil/、xsim_*.backup.*）。
- `others/build/`：`build/` 下全部板卡包与本地报告（board-app-*/board-package-*/board-packages/run/reports{fmax,pynq_*,vision_ooc}，约 1.7 GB 同盘移动）——**刷板包路径由 `build/board-package-*` 变为 `others/build/board-package-*`**。
- `others/NA/`：Vivado PS 配置摘要。
- `others/yolo/`：YOLO 本地专用件（yolov8n.pt、4 个脚本、train_localization_cnn.py、results/*yolo*.json、data/logs/2026-10-27-yolo-switch-r1/）。
- `others/misc/`：7 个 VCD 波形、fwd/cop_job ELF/BIN 编译产物、本地临时 runbook（board-workorder-2026-10-20.md）；误建空目录 `-p` 已删除。
- 纯缓存（__pycache__ ×9、.pytest_cache）直接删除（可再生，不搬）。
- **保留原地**：`tools/`（已入库的正牌仓库内容，cop_payload_loader.py 等被文档引用）、`sim/build/`（回归脚本标准暂存区，脚本会重建）、`data/logs/` 内被忽略的 .jou/.dcp/.bit（证据目录只追加不改写）。
- 验证：未跟踪仅剩本次 llm_log（待 commit）；ignored 剩余 = `others/`、`sim/build/`、`data/logs/` 内部证据件；`git diff --check` CLEAN（顺带修掉 README EOF 多余空行）。

## 补充2（同日）：全仓文档清理（doc-cleanup skill 两遍式，用户批准"全按推荐"）

三路并行诊断（src / docs 现行 / board+build+data+skill+历史横幅覆盖）产出 22 组发现，全部处置：

- **A 组必读文档**：docs/README（三人清单"当前入口"引用删除、目录表补 tools/others）、repo-hygiene（白名单补 tools/others；Vivado 输出路径改 others/build/）、onboarding（"空壳占位"句删除、分工/PR 指针改仓库规矩）、branch-layout（dev/verify 经 PR #91 重建说明、dev/model 退役标注）、workflow（"收口与验收"）。
- **B 组死链**：三人清单类链接 9 处、`#12-收口时间总览` 死锚 2 处、src/vision_client 死链 8 处、`docs/coremark.md`、coprocessor-nc-handoff 相对路径、final-status 的 runbook 路径——全部 correct。
- **C 组产物路径迁移注记**：build/README、vivado-checklist、imem-init-gate、nc-handoff、clock-runbook（加"产物现位于 others/build/"注记）。
- **D 组状态滞后修正**：smoke_test"尚未验证"→9/20 实测 PASS；handoff-v0 加 10-28 更新注（BOARD UNVERIFIED 标为 10-26 时点口径）；vision/design_v0 cop_top、vision/README 未实现清单、riscv_fw cop_job/bench_v0_1、coprocessor README/design_v0 状态句。
- **E 组 EXE 角色名**：contracts 三篇、contracts/README 索引行、board/hardware（Pi mock 宿主标历史）、pi-dev-roles、nc-release-demo-preflight（交付行改网页端）。
- **F 组**：sim/README Icarus 版本口径限定、board/README 现用位流=r6 共存包（锚 plan §3.1）、board/logs 模板 media 注记、data/golden/vision/README 新建、data/logs/README 加"run README 均为历史快照"顶层说明、src/riscv/plan.md 两项补勾选、coprocessor/design_v0 残句补全。
- **closeout-todo 收敛**：§0 基线刷到 10-28（板卡恢复/真实数据 33 ROI/r6 逐项一致）、A07 勾掉、D03/D06 改网页端、E03 去三人签收、F01 改为当前未验收项清单。
- **历史横幅 10 篇**（原位，不迁 archive）：runbooks 9 篇（nc-offline-readiness/nc-return-checklist/nc-offboard-workboard/n03-custom-return/board-morning/concurrent-agent-audit/module1-reproduction/arm-localize-baseline/arm-localize-results）+ coprocessor-board-clock-runbook（MMCM 取代注记，JTAG≠PS7 陷阱保留）。
- **检查脚本两处同步**：check_repo_hygiene.py 白名单加 others/、链接豁免加 docs/archive/；data/logs/2026-10-28-sync-selftest 补 PROVENANCE GAP 标注 README。
- **裁决落实**：data/logs 125 个 run README 不批量加横幅（顶层说明代替）；过期执行单原位横幅不迁移。

## 验证（清理后）

- `python sim/scripts/check_repo_hygiene.py`：**exit 0，0 ERROR**（修复 18 个断链/缺 README/stale index；duplicate blob WARN 为历史证据重复字节，信息性，不处理）。
- 全量相对链接抽验（改动文件 468 个链接）：0 死链（plan.md 的百分号编码中文文件名经验证真实存在，为检查脚本误报口径）。
- `python -m py_compile` 两个 tech-report 脚本 PASS；`git diff --check` CLEAN。
- 累计本会话改动：107 文件，+311/−2163，全部未 commit。
