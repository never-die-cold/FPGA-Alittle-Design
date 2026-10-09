# 改动记录与收口工作：模块一／二（本轮代码／文档检查完成）
日期：2026-10-09；本轮只整理已有实现，不新增功能、接口或指令语义。
分支 main，HEAD `051aefaae9841e16237cc65a004b2c5ee5ec995d`；本轮未 commit／push／fetch。
文档已修订；用户确认后已应用B07帮助／B13默认路径修复。完整复跑all-b13.log已exit=0；未新增硬件验证结论。

## 1. 范围与三层结论
- 模块一核＋最小 SoC 已完成收口，见[核报告](../module1-closure.md)和[合并验收](../../data/logs/2026-10-07-module1-closure/README.md)。
- 模块二 HDMI 视觉预处理 RTL＋已验证视频链路已完成（RTL／链路级），见[10/03 视频](../../data/logs/2026-10-03-vision-onboard/README.md)、[10/07 相机](../../data/logs/2026-10-07-pi-pynq/README.md)。
- 全项目 M2 验收未完成。首个网络硬件输出／CNN 未完成；工业闭环按根 plan 的 M3 条件继续，不因前两项完成而通过。
- 已授权文本目录按清单执行；vision_top 只改两条注释，未改代码行为。未修改冻结验收阈值或历史失败数据。

## 2. 检查方法与环境
- 开始修改前已全量读取：5,964 普通文件＋14 符号链接，含 ignored 产物，排除仓库根 .git；无读取错误。
- 逐文件路径、作用、初始 SHA256 见[机器索引](../../data/logs/2026-10-09-module1-2-closeout/file-index.txt)；[生成命令](../../data/logs/2026-10-09-module1-2-closeout/inventory-command.txt)与[初始记录输入](../../data/logs/2026-10-09-module1-2-closeout/read-snapshot.tsv)在库，指纹不冒充修改后的源码。
- 文档声明分别对照冻结契约、实际端口／接线、脚本参数与产物名、原始日志／manifest／metrics；216 个本地文档链接初检无缺失。
- Icarus **11.0**／GCC **10.2.0**／Python **3.10.12**；原验收 Icarus 13.0／GCC 14.2.0／Vivado 2026.1 分开保留。
- 本轮 CoreMark 直接预载仓库既有 hex，未重编／改固件；arch 矩阵使用本地 GCC 10.2.0 编译同版本套件。
- 本机无 Vivado／XSim／tclsh；没有新 WNS／Fmax／资源、位流或下载结论。[本轮环境](../../data/logs/2026-10-09-module1-2-closeout/environment.json)。
- 16 份核 RTL SHA256 与 10/07 manifest 一致，见[核指纹检查](../../data/logs/2026-10-09-module1-2-closeout/rtl-fingerprint.log)；vision_top 去注释后与 HEAD 完全一致。
- 各手工批次均≤100新增＋删除行；机器索引／原始日志不按手工正文行数计。未用 /tmp 验证。

## 3. 逐文件改动与影响
下表为文字／注释整理，验证是本地链接存在、实际源码／脚本对照和 diff --check；功能复跑另见§6。

| 批次 | 文件 | 改什么／依据／影响 |
|:---|:---|:---|
| B01 | docs/README.md | 三层状态＋证据、对应版本入口、提交授权要求；后续补 Q 登记索引 |
| B01 | docs/workflow.md | 保留必须同步的强度，只细化为对应模块／版本的冻结契约 |
| B02 | docs/project-overview.md | 当前 v1/BHT、23视觉 tb、命中率／频率口径；7旧图标历史，未重绘 |
| B03 | docs/three-day-plan.md | 旧计划加历史标记；旧分支命令不作为当前指令 |
| B03 | docs/partC-pc-depth-resume.md | 旧续工加历史标记与后续复验证据，失败点保留 |
| B04 | docs/partB-verify-plan.md | 实际 mem_valid／tohost_exit、气泡对账与当前证据 |
| B04 | docs/core_comparison.md | 四档当前状态、Pico频率明确外推，不作同负载加速证明 |
| B05/06 | src/riscv/design_v1.md | 现有非load转发绑定、提交逻辑别名、branch_valid、BHT_MODE、静态redirect范围；无接口变更 |
| B06 | src/riscv/README.md | 当前v1契约、Radix-4算法与历史v0接口分开 |
| B06 | src/riscv/plan.md | 四档、valid冲刷、tb统计、声明arch子集和后续验收记录 |
| B07文档 | sim/README.md | 当前四档／arch入口与历史v0观察表分开；后续脚本只更新帮助／注释 |
| B08 | docs/vision-sync-protocol-decisions.md | D6已确认标题、结果报文字段拒绝缺口登记；条款未放宽 |
| B09a | README.md | 三层状态、旧面积论证、原型／正式部署区分、入库授权；不改历史指标 |
| B09b | plan.md | 已验证视频／EXE原型、当前依赖与位流追溯；M2/M3条件未改 |
| B10 | build/README.md | 按Tcl核对命令／目录；历史−1.530与现存−1.935报告分开 |
| B11 | board/README.md | 已有板端步骤和视频记录；自动开机加载仍未实现 |
| B11 | board/hardware.md | 实际相机接线及含采集卡125ms口径；不冒充PL延迟 |
| B11 | data/README.md | 已有指标／golden；不存在的data/images、data/models明确未建立 |
| B12 | src/vision/README.md | 23 tb、真实相机证据、不同位流断连结论不可借用 |
| B12 | src/pynq_host/README.md | 实际配置／黄金参考／mock与正式服务边界 |
| B12 | src/vision/vision_top.v | 仅注释：Sobel4拍／cop_buf双帧缓冲；HDL正文不变 |
| B07脚本 | sim/scripts/run_iverilog.sh | 只改帮助／注释；continue和回归执行流程不变 |
| B13 | board/scripts/program_soc.tcl | 默认位流改为当前40MHz fwd产物；仍支持显式位流路径，不默认BHT2 |
| B13 | board/scripts/program_soc.bat | 修安装路径回退；已有VIVADO环境变量不覆盖，Windows执行待验证 |
| 补充 | docs/partC-verify-plan.md | 实际四档、mem_valid／tohost_exit、tb统计来源；历史复选框保留 |
| 补充 | docs/vision-offboard-next.md | 历史计划标记＋当前视频证据，历史正文保留 |
| B14 | data/logs/2026-10-09-module1-2-closeout/ | 机器索引、原始命令／日志／退出码、指纹和已批准patch；不是硬件新验收 |
| B15/16 | 本文件 | 逐文件改动、检查方法、待审／未完成项与本轮证据 |

各批行数：B01=25，B02=96，B03=17，B04=31，B05=24，B06=26，B07文档=34，
B08=9，B09a=36，B09b=31，B10=47，B11=24，B12=35，补充两份文档=17，Q索引=10。
末轮抽检另补 core_comparison 历史范围／README复选框3行；证据README34行、续工记录30行，各自单批。
B07脚本10行、B13 Tcl6行／BAT2行，共18增删行；只应用用户审过的diff。
数据表、历史失败日志、第三方正文、重复文档和图片均未重写；不新增性能指标冒充实测。

## 4. 过时项与无需改动项
- N01–N18：当前状态、版本、入口／统计映射及脚本帮助已整理。
- N19–N27：已授权README／plan／注释与B13默认路径已完成修改；Windows执行待验证线。
- Q01核查：D6覆盖结果报文，validate_packet没有完整字段白名单；POST请求拒绝不能替代结果校验。只登记，不修Python／tb，不放宽契约。
- Q02：run_iverilog缺失tb时continue只登记。当前24份引用核tb均存在，不借此解除风险。
- Q03：本地只有partA-v0；未取得archive/pi-hdmi-diagnostics-2026-10-08，不查远端、不建替代tag。
- Q04：中文探索报告与英文名audit字节一致；保留两份，权威正文待拍板。
- Q05：旧图加“历史快照：BHT 尚未绘制”，重绘另批；图片与生成脚本未改。
- Q06：三处本地缺失链接只在[索引](../../data/logs/2026-10-09-module1-2-closeout/inventory-links.txt)登记；第三方／历史正文保留，外部HTTP未重查。
- 无需重复改：PartB/PartC handoff已有10/07当前证据横幅，§99与正式模块一报告已有闭环记录。
- 旧25% FAIL／8.14%、Radix-4净收益21.95%／组合28.30%、失败频率／WNS全部保留，不能由当前14.83%倒填历史门禁。

## 5. 已批准脚本与后续责任
- [已批准diff](../../data/logs/2026-10-09-module1-2-closeout/proposed-script-changes.patch)18增删行已应用：B07帮助／注释；B13 program_soc默认路径。
- 默认位流为build/run/soc_40mhz/pynq_z2_soc_40mhz.bit（fwd、BHT关）；BHT2只能显式传对应位流。
- bat默认安装位置D:/Vivado_downloads，已有VIVADO环境变量不覆盖；不存在／空文件仍提前拒绝。
- 用户已明确授权本批落盘；Windows实际执行／JTAG下载由验证线确认，本机不能代填。
- 用户另裁决Q01最小修复＋负例、双语正文权威、旧图重绘；未授权前不进行这些行为改动。
- 验证线：闭环板端现用vision.bit与本地修复源码／位流指纹，并补现用配置长期／冷启动／断连证据。
- 模块三／服务／EXE负责人：首网硬件输出、真实定位部署、正式结果服务、工单与批次闭环仍按主计划推进。

## 6. 本轮收口检查表（完整 all exit=0）

以下只列本轮实跑；历史 Vivado／上板证据沿用§1链接，不推断为本机新验证。

| 检查／原命令 | 结果与原始证据 |
|:---|:---|
| `bash sim/scripts/run_iverilog.sh all` | exit=0；[all-b13.log](../../data/logs/2026-10-09-module1-2-closeout/all-b13.log)与[退出码](../../data/logs/2026-10-09-module1-2-closeout/all-b13.exit.txt)；57个tb运行块均有PASS、23视觉tb＋7 Python检查通过 |
| `ARCH_TEST_LOG_DIR=data/logs/2026-10-09-module1-2-closeout/arch-matrix bash sim/scripts/run_arch_test_matrix.sh` | exit=0；[原日志](../../data/logs/2026-10-09-module1-2-closeout/arch.log)末尾 `PASS: arch-test matrix 11 tests x 4 modes`；44/44 |
| `iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v` | exit=0，零输出；[最终日志](../../data/logs/2026-10-09-module1-2-closeout/core-g2001-final.log) |
| `grep -rn '(\.\*)' src/` | exit=1，零匹配（通过）；[最终日志](../../data/logs/2026-10-09-module1-2-closeout/implicit-ports-final.log) |
| `bash sim/scripts/run_iverilog.sh vision_python`（沙箱外） | exit=0；[7项PASS原日志](../../data/logs/2026-10-09-module1-2-closeout/vision-python-host.log) |
| B13脚本范围 | [b13-scope-guard.log](../../data/logs/2026-10-09-module1-2-closeout/b13-scope-guard.log)：runner流程／continue不变，Tcl只改默认路径；此前scope-guard为B13前快照 |
| `bash -n sim/scripts/run_iverilog.sh` | exit=0，零输出；[原日志](../../data/logs/2026-10-09-module1-2-closeout/b13-bash-syntax.log) |
| `git diff --check` | 最终exit=0、零输出；[日志](../../data/logs/2026-10-09-module1-2-closeout/diff-check-final.log) |
| Vivado／XSim／位流／本轮上板 | 本机不具备工具／板卡；本轮未执行，不新增硬件验证结论 |

沙箱内协议预检被本地 socket 权限拒绝，exit=1，见[失败原文](../../data/logs/2026-10-09-module1-2-closeout/vision-python-precheck.log)。
因此主动停止第一次沙箱 all（exit=143），保留[原日志](../../data/logs/2026-10-09-module1-2-closeout/all.log)，不用部分结果拼接 PASS；完整 all 在可建立本地 HTTP 的环境从头重跑。
第二次[all-host.log](../../data/logs/2026-10-09-module1-2-closeout/all-host.log)也依用户停工请求中断，exit=143；只完成CoreMark前两档，不能作完整通过。两份历史日志均不覆盖。
原始 timescale／readmemh 提示不隐藏；CoreMark为32迭代短测，errors_raw=1不得写成官方认证分数或CRC失败。

同一次all调用四档入口，未另跑四次独立命令；[机器对账](../../data/logs/2026-10-09-module1-2-closeout/matrix-summary.json)、[原始对账输出](../../data/logs/2026-10-09-module1-2-closeout/matrix-check.log)与[可复跑命令](../../data/logs/2026-10-09-module1-2-closeout/matrix-check-command.txt)在库。

| CoreMark档 | cycles | retired | CPI |
|:---|---:|---:|---:|
| v1_nofwd | 19057438 | 10106386 | 1.885683 |
| v1_fwd | 17114141 | 10106386 | 1.693399 |
| v1_fwd_bht1 | 16335562 | 10106386 | 1.616360 |
| v1_fwd_bht2 | 16232079 | 10106386 | 1.606121 |

- 四档CRC均为e9f5／e714／1fd7／8e3a／8799，tohost=34713；分类之和、hit+miss、RAW差与周期差均通过。
- vision_gate的FAIL／ERROR／FATAL为8例门禁故障注入的预期输出，逐例核对reject后通过；不删除原始负例日志。
- [源码运行指纹](../../data/logs/2026-10-09-module1-2-closeout/b13-run-source-manifest.json)记录dirty状态；[复核](../../data/logs/2026-10-09-module1-2-closeout/b13-run-source-recheck.log)确认44项运行输入未变。两次后处理检查口径错误与修正也如实保留，非DUT失败。
- 本轮代码／文档收口检查通过；既有硬件收口依§1历史证据。本轮Windows脚本执行仍待验证线，未新增硬件验收；全项目M2未完成。

## 7. 集中审核与续工

- 文档批次按用户最新节奏免逐步出题；B01用户三题已通过。脚本须先审核拟议diff、答题后才落盘；未经授权仍不commit／push。
- [断电续工记录](../../docs/resume-2026-10-09-module1-2-closeout.md)保存WIP与禁改边界；[证据入口](../../data/logs/2026-10-09-module1-2-closeout/README.md)索引原始日志。
- 题1：默认路径修复为何不能顺便默认BHT2？要下载BHT2时怎样显式指定？
- 题2：BAT中if not defined VIVADO有什么作用？用户已设自己的路径时用哪个？
- 题3：all退出143但前两档CoreMark已PASS，能否记录完整回归通过？为什么？
- 用户回答摘录：题1要求“显式指定其位流路径／配置”，但理由包含“BHT2还没在板上跑过”；后者与已有证据冲突。
- 题2：“没设就用脚本默认，设了就用用户的”；题3：“143是被杀中断，只有重跑exit 0才写完整通过”。两题通过；两档PASS来自同次中断all，未另跑独立两次。
- B13第2／3题通过；第1题“BHT2未上板”已据[10/07实机证据](../../data/logs/2026-10-07-partC-postopt/README.md)纠正，默认兼容性补题现已通过。用户明确区分“可用”与“应当默认”，理解门槛完成。
- 保留默认的依据是向后兼容与本轮授权范围；四档显式传参仍可保留关闭档锚点，不能说改变默认就必然失去公平对照。本轮未授权提交，仍不commit／push。
- Q01行为修复、双语文档权威和旧图重绘继续等待单独裁决；未经授权仍不commit／push。
- 用户已确认本轮审阅完成；代码／文档整理收口结束。此确认不作为commit／push授权，不改变全项目M2未完成及Windows执行待验证的状态。
