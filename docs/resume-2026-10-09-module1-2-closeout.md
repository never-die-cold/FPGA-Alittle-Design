# 模块一／二文档收口续工记录（断电保护）
日期：2026-10-09；当前分支 `main`；HEAD `051aefaae9841e16237cc65a004b2c5ee5ec995d`。
本地 tag 列表：`partA-v0`；未查询远端，未新建替代 tag。
用户已要求立即停工；只保存本续工记录与 WIP 快照，不 commit／push／新建分支。

## 当前完整 git status --porcelain
```text
 M README.md
 M board/README.md
 M board/hardware.md
 M build/README.md
 M data/README.md
 M docs/README.md
 M docs/core_comparison.md
 M docs/partB-verify-plan.md
 M docs/partC-pc-depth-resume.md
 M docs/partC-verify-plan.md
 M docs/project-overview.md
 M docs/three-day-plan.md
 M docs/vision-offboard-next.md
 M docs/vision-sync-protocol-decisions.md
 M docs/workflow.md
 M plan.md
 M sim/README.md
 M src/pynq_host/README.md
 M src/riscv/README.md
 M src/riscv/design_v1.md
 M src/riscv/plan.md
 M src/vision/README.md
 M src/vision/vision_top.v
?? data/logs/2026-10-09-module1-2-closeout/
?? docs/resume-2026-10-09-module1-2-closeout.md
?? report/llm_log/2026-10-09-module1-2-closeout.md
```
以上含新增续工文件；证据目录为未跟踪目录，完整路径清单另见 WIP 快照附录。

## 已完成批次与实际行数
计数为各批新增＋删除；同一文件跨批分开计，机器索引／原始日志不计手工行数。
| 批次 | 已落盘内容 | 实际行数 |
|:---|:---|---:|
| B01 | docs/README、workflow；三层状态、证据与对应冻结契约 | 25 |
| B02 | project-overview 当前状态、7张旧图历史标记 | 96 |
| B03 | three-day-plan、partC-pc-depth-resume 历史范围 | 17 |
| B04 | PartB验收与core_comparison统计／证据口径 | 31 |
| B05 | design_v1实际转发、提交、分支控制映射 | 24 |
| B06 | design_v1补证、核README／plan当前四档 | 26 |
| B07文档 | sim/README入口／基线说明；脚本部分未做 | 34 |
| B08 | D6已冻结标题及Q01只读核查结论 | 9 |
| B09a／B09b | 根README／根plan三层状态、原型／部署边界 | 36／31 |
| B10 | build/README命令／目录及历史与当前频率分开 | 47 |
| B11 | board两份文档、data/README | 24 |
| B12 | vision／host README与vision_top两条注释；行为不变 | 35 |
| 补充文档／Q索引 | PartC验收＋vision历史计划；docs/README登记Q | 17／10 |
| 末轮抽检 | core_comparison历史范围与README复选框 | 3 |
| B14 | 5,978项初始文件索引、生成命令／SHA、原始验证日志 | 机器生成 |
| B15／B16已写部分 | 收口报告先75行，再追加29行、工具说明1行 | 75／29／1 |
| 证据入口／旧续工 | 证据README、证据目录resume.md | 34／30 |
| B13／B07脚本 | 仅保存18行拟议diff；三份原脚本未改 | 0（未应用） |

## 停工时验证事实
- arch矩阵 `arch.log`／`arch.exit.txt`：11×4＝44/44，exit=0。
- `core-g2001.log`：Verilog-2001编译exit=0零输出；`implicit-ports.log`无匹配；最近diff --check零输出。
- `rtl-fingerprint.log`：16核RTL与10/07 manifest一致；vision_top去注释后HDL不变；metrics未改。
- Python沙箱内socket被拒exit=1；同一入口沙箱外7项PASS、exit=0，两份日志均保留。
- 首次 `all.log` 主动中断exit=143；后续 `all-host.log` 也依本次停工请求中断，exit=143。
- all-host内benchmark四档已PASS；CoreMark只有nofwd与fwd完成：19057438／17114141周期，retired均10106386，CRC一致。
- BHT1 CoreMark中断、BHT2及后续全量段未完成：**本轮all未通过，不能用部分日志拼接完整PASS**。
- 本机Icarus11.0／GCC10.2.0／Python3.10.12；原验收13.0／14.2.0分别保留。无Vivado／XSim，无新硬件结论。
- 旧报告、证据README／旧resume的“运行中”描述尚未更新；以本记录的“已中断”状态为准。

## 下一步批次及原计划（须用户重新恢复工作后执行）
1. B02–B12原计划已落盘，不重复改；先对照上表和git diff复核文档／注释，保留历史失败数据。
2. B07脚本＋B13独立审核：展示proposed-script-changes.patch的18行diff及3题；用户确认后才改。
3. B13原计划只修program_soc Tcl默认失效路径、bat安装路径；默认40MHz fwd／BHT关，禁止默认BHT2；Windows待验证线。
4. B14索引已生成；核对file-index.sha256及inventory-command.txt即可，不重新冒充初始快照。
5. B16原计划：重新跑完整all、保留单次完整exit=0及四档CRC／retired对账；无活动回归进程后再启动。
6. all已有四档入口调用；arch44/44结果已取得，无新改动无需重复。追加后刷新静态门、链接与diff检查。
7. B15/B16报告补最终原始结果、明确代码／硬件收口区别；集中少量理解题，未获授权仍不提交。

## 本轮生效的按风险分档规则
- 纯文档：直接执行、免逐批理解题；单批≤100行，汇报文件／行数／diff／验证／证据；每3–4批给汇总抽检。
- RTL／脚本／接口行为：必须先停下给diff和2–3题，用户确认后才改、再进下一步；本轮禁止RTL语义变更。
- 不使用/tmp证据；不改写历史25% FAIL／8.14%及失败WNS；不默改语义；不commit／push／新建分支。
- 已授权根README／plan、build／board／data／vision／host文档；vision_top仅两条注释，下载脚本属条件授权。

## 仍未做／只登记项与证据位置
- 文件索引生成、Q01契约核查均**已完成**；Q01结果报文未知字段白名单修复／负例测试未做，需另批裁决，不放宽D6。
- 下载脚本和run_iverilog帮助修改未做；Windows实际执行、新Vivado／XSim／时序／资源／上板复验未做。
- Q02continue只登记；Q03本地未取得archive tag、不查远端；Q04双语不合并删除；Q05不重绘；Q06不改历史／第三方正文。
- 模块一核＋最小SoC已收口；模块二仅RTL／已验证链路级；全项目M2、CNN／网络硬件输出／工业闭环未完成。
- 板端现用vision.bit与本地修复版指纹、现用配置长时间／冷启动／断连证据仍待验证线闭环。
- 证据根目录：`data/logs/2026-10-09-module1-2-closeout/`；拟议patch、初始索引、所有原始日志均在此。
- 当前报告草稿：`report/llm_log/2026-10-09-module1-2-closeout.md`；WIP：`data/logs/2026-10-09-module1-2-closeout/wip-status.txt`。

## 恢复工作记录（2026-10-09，原断电快照保留）

- 已完整读本记录与WIP；恢复前status、diff --stat、未跟踪文件清单、HEAD／tag与WIP完全一致。
- 用户已批准B07帮助／B13路径diff；18增删行已应用（Tcl6、BAT2、runner10），continue及执行流程不变，默认40MHz／fwd／BHT关。
- bash -n通过、无效模式帮助exit=1符合预期；Windows BAT／Vivado实际执行待验证线确认。
- 全量已重新从头运行：`all-b13.log`，结束后写`all-b13.exit.txt`；工具session 31382。旧all及all-host的exit=143原样保留。
- 本次全量结束前不得写PASS；如续工时仍有活动回归，不得再启动共享sim/build的CoreMark。
- 第2／3题通过；第1显式选档原则正确，但“BHT2未上板”已据10/07实机证据纠正。补题：既然已有BHT2上板证据，为何本轮仍保留旧默认？
- 待办：拿完整all退出码与四档对账，刷新静态门／链接／范围指纹，补最终收口报告；不commit／push／新建分支。

## 本轮恢复完成（2026-10-09，以上停工／运行中记录为历史快照）

- session31382已结束；all-b13.exit.txt=0，完整all通过，不再有本轮活动回归。旧两次exit=143原样保留。
- 同次all四档CoreMark周期19057438／17114141／16335562／16232079；retired均10106386，CRC一致；机器对账命令与JSON／日志在证据目录。
- 57个tb运行块均有PASS；视觉23tb、Python7项、门禁8个故障注入均通过，注入FAIL不冒充DUT失败。
- B13=18增删行已落盘；最终Verilog-2001／隐式端口／diff门与源码指纹复核通过，Windows执行仍待验证线。
- 默认兼容性补题已通过，B13理解门槛完成；用户已确认最终报告审阅完成，本轮代码／文档整理收口结束。Q01修复／双语权威／重绘另裁决，M2应用验收与视觉位流追溯继续由对应负责人推进。
- 补题说明：已有上板证据证明BHT2可用，默认仍按兼容与本轮授权保留；四档显式传参不会因默认值改变而必然丢失对照锚点。未授权commit／push。
- 仍在main@051aefa；仅本地未提交改动，无commit／push／新分支。本机无Vivado／XSim，没有新增WNS／位流／上板结论。

## 后续归档与提交授权（2026-10-09）

- 用户新请求授权代码与分模块协作记录一起本地提交到现有dev/rtl，并由用户上传GitHub；前文“不commit／main”是此前阶段的历史状态。
- 已安全转到既有dev/rtl并快进至原main@051aefa；191个原WIP文件内容恢复一致，未新建分支，main未改变。
- 分模块记录入口为report/llm_log/template.md末尾索引；上传命令见docs/upload-rtl-code-and-logs.md。
- 原完整all／arch／静态证据仍沿用同一被测源码指纹，Windows执行／Q01／M2待办不因归档或提交而改变。
