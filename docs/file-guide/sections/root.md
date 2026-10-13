# root：逐文件说明

10个文件；返回[主页](../README.md)，完整关系见[搜索页](../index.html)或[JSON](../files.json)。

| 文件 | 一两句话说明 | 关联文件（最多展示5项） |
| --- | --- | --- |
| **根目录** | | |
| [.gitattributes](../../../.gitattributes)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 配置Git行尾、二进制和差异处理；它影响证据快照是否仍保持原始字节。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[data/logs/2026-10-10-model-reference/numpy-parity-before.log](../../../data/logs/2026-10-10-model-reference/numpy-parity-before.log) |
| **.github/ISSUE_TEMPLATE** | | |
| [.github/ISSUE_TEMPLATE/bug_report.md](../../../.github/ISSUE_TEMPLATE/bug_report.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 新建缺陷Issue时的填写模板，要求说明复现步骤、现象和环境；与工作流中的问题留痕配套。 | 所在目录说明：[README.md](../../../README.md) |
| [.github/ISSUE_TEMPLATE/task.md](../../../.github/ISSUE_TEMPLATE/task.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 新建任务Issue时的填写模板；用于把工作范围、验收与依赖说清楚。 | 所在目录说明：[README.md](../../../README.md) |
| **.github** | | |
| [.github/PULL_REQUEST_TEMPLATE.md](../../../.github/PULL_REQUEST_TEMPLATE.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 提交PR时的说明模板，提醒作者给出改动、验证和理解门槛；服务于main合入流程。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[sim/scripts/run_iverilog.sh](../../../sim/scripts/run_iverilog.sh)<br>文本引用：[skill/understand-gate/SKILL.md](../../../skill/understand-gate/SKILL.md)<br>文本引用：[src/riscv/plan.md](../../../src/riscv/plan.md) |
| **根目录** | | |
| [.gitignore](../../../.gitignore)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 规定哪些构建产物、缓存和依赖不入Git；本索引按它排除本地生成目录，但保留已经纳入Git的证据。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[sim/scripts/fetch_arch_test.sh](../../../sim/scripts/fetch_arch_test.sh) |
| [AGENTS.md](../../../AGENTS.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 本仓库给开发者和AI的开工、目录边界、验证与提交纪律；执行细节指向 docs/workflow.md 和 skill/。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[docs/workflow.md](../../../docs/workflow.md)<br>文本引用：[sim/scripts/run_iverilog.sh](../../../sim/scripts/run_iverilog.sh)<br>文本引用：[skill/gufa-programming/SKILL.md](../../../skill/gufa-programming/SKILL.md)<br>文本引用：[skill/understand-gate/SKILL.md](../../../skill/understand-gate/SKILL.md)<br>另2项见搜索页 |
| [LICENSE](../../../LICENSE)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 本项目代码的许可证文本；第三方IP、字体和CoreMark各自另有许可证。 | 所在目录说明：[README.md](../../../README.md) |
| [README.md](../../../README.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 项目总入口，说明作品目标、模块、当前进度与复现方式；后续任务由根 plan.md 细化。 | 文档链接：[LICENSE](../../../LICENSE)<br>文本引用：[board/README.md](../../../board/README.md)<br>文档链接：[board/README.md](../../../board/README.md)<br>文本引用：[data/README.md](../../../data/README.md)<br>文档链接：[data/README.md](../../../data/README.md)<br>另41项见搜索页 |
| [plan.md](../../../plan.md)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 全项目目标、分工、里程碑与验收看板；模块专项计划和接口契约都引用它。 | 所在目录说明：[README.md](../../../README.md)<br>文本引用：[data/evidence/2026-10-12-c01-exact-build-inputs/README.md](../../../data/evidence/2026-10-12-c01-exact-build-inputs/README.md)<br>文档链接：[data/evidence/2026-10-12-c01-exact-build-inputs/README.md](../../../data/evidence/2026-10-12-c01-exact-build-inputs/README.md)<br>文本引用：[data/logs/2026-10-03-vision-onboard/README.md](../../../data/logs/2026-10-03-vision-onboard/README.md)<br>文档链接：[data/logs/2026-10-03-vision-onboard/README.md](../../../data/logs/2026-10-03-vision-onboard/README.md)<br>另52项见搜索页 |
| [tight_setup_hold_pins.txt](../../../tight_setup_hold_pins.txt)<br>软件/脚本/项目入口 · 已纳入Git（含暂存） | 记录时序紧张路径的引脚信息；用于定位setup/hold问题，不能单独代替完整时序报告。 | 所在目录说明：[README.md](../../../README.md) |
