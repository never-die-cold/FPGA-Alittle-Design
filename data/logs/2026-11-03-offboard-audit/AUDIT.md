# 最终离板仓库审查（2026-11-03）

基线：`dev/submission-slim @ ffe0769`，包含开工时已有的未提交改动。审查只新增本目录证据，不修产品代码、不提交。

## 范围与结论口径

全仓枚举：3475 个跟踪文件；连同已有未跟踪文件共 3499 个（排除本轮审查产物）。225 个 Python、152 个 Verilog、43 个 Shell、19 个 PowerShell 文件进入清单。数量包含历史快照/第三方文件，不等于现役模块数。
全量自动扫描结合现役链路重点人工审查：核/固件、视觉、CNN/MMIO/DMA、PS 捕获/服务、网页、构建/回归入口、主计划/契约/技术报告/海报。历史日志与第三方二进制按来源及恢复入口核对，没有逐个重做历史实验。
本报告不声称每个文件已逐行人工证明正确；语法/仿真通过也不证明新综合时序、实板长测、模型精度或整机验收。
P1：提交前优先处理；P2：功能、复现或描述问题需明确处置；P3：维护/复杂冗余问题。以下区分实际复现、静态确认与待实测风险。
当前登记20项问题（5项P1、15项P2）与7项P3维护事项；不是20处已经证明的RTL逻辑故障。
`sources.sha256`覆盖src/sim/tools/build/docs的跟踪及未忽略未跟踪文件，`working-tree.diff`保存相对HEAD的原有跟踪改动；`source-hash-check.log`的校验进程退出0。未跟踪文件的实际内容仍须随发布清单保存，哈希不能代替源码。

## 发现清单

| 编号 | 级别 | 位置 | 问题、影响与建议 |
|---|---|---|---|
| F01 | P1 / 已复现 | `src/web_client/index.html:900`，`connectLive` | 同一 session 的 config 被另一客户端更新后，`liveRound` 因 config 不符断开；重连只有 session 变化或 config 为空才请求配置，故保留旧 config，下一轮继续失败。第二个浏览器页首次握手也会POST配置，因此演示双页/多客户端可触发。用户须重载/切换模式才能恢复。应支持只读确认当前配置并覆盖同会话配置变化，避免靠重复写配置造成多客户端争抢。见 `probe-web.mjs`、`probe-web.log`。 |
| F02 | P1 / 静态确认 | `docs/tech-report/latex/sections/02-architecture.tex:28` | 报告把“灰度 out_* 经 DDR 进入 PS”写成现行数据流；`src/pynq_host/cop_product_service.py:1`、`build/attach_pynq_video.tcl:71` 与共存交接记录均说明当前捕获 native RGB/BGR，PL 分析支路被裁掉，PS 做定位/灰度 ROI。须区分模块独立实现与现役整机实际接线，同步核对报告配图。 |
| F03 | P1 / 版本完整性 | `baseline-status.log` | 网页必需的 `src/web_client/protocol.mjs`、`serve.py`、三个网页测试，10/30 原始证据和全部 LaTeX 源仍未跟踪；依赖它们的 index/README 等也未提交。按当前 HEAD 导出无法得到本机这套 LIVE 功能和新报告。须先冻结明确的提交/打包清单，保留用户理解与 commit 门槛。 |
| F04 | P1 / 实际失败 | `sim/vision/test_n03_buffer_lifecycle.py:12` | 依赖已缺失的 `data/logs/2026-10-11-onboard-resume/n03-buffer-free-lifecycle.txt`，直接运行 FileNotFoundError。失去 cached-frame 二次 munmap 防护的原始复现依据。应恢复确切原记录并登记来源，或明确退役测试；不能临造替身充当原记录。见 `extra-python.log`。 |
| F05 | P2 / 已复现 | `src/web_client/protocol.mjs:8`；`src/pynq_host/vision_protocol.py:109` | JS 没有校验可选 trigger_ref 类型/长度，接受对象；Python 拒绝同类字段。手动轮额外做等值检查，但自动/文件回放仍可接受非法协议报文。应共享正负报文向量，补齐类型/长度语义。见 `probe-web.log`。 |
| F06 | P2 / 文档矛盾 | `plan.md:105`；`docs/project-overview.md:206` | 主计划最新段落写 C01/COP_HW 与 r6 多目标已上板，末尾无历史标题的“未实现”仍含首网板端输出/真实硬件 LIVE；总览第6节仍写应用路径未接入、FILE/LIVE 用文件代硬件，与其第8节相反。应把旧快照显式归入历史，当前表只保留最新结论。 |
| F07 | P2 / 回归覆盖 | `sim/scripts/run_iverilog.sh:203`；`run_coprocessor_iverilog.sh:203` | 名为 all 的统一入口不调用 17 组 inspection、网页 Python/Node 测试、class_aware_metrics/localization_data/N03 两项，以及 BRAM 整网变体；arch-test 另有专项入口是已说明的边界。遗漏的 N03 测试已实际失败，说明统一入口 PASS 不代表仓库全部检查 PASS。应提供清晰的最终离板总入口或完整命令清单。watchdog 虽有独立入口，默认 network/conv 故障用例已执行，不应误报为完全漏测。 |
| F08 | P2 / 静态确认 | `src/pynq_host/vision_live_service.py:219`；网页 `autoRound` | status 的 hardware_connected 恒为 True，不查询捕获锁定/硬件健康；网页已连接且自动检查关闭时也不持续刷新 status。API 进程存活不能证明硬件仍健康，服务绿点可能长期保留。应区分服务在线与最近硬件健康，未知/故障要明确显示；本轮不进行板级断源试验。 |
| F09 | P2 / 运行风险 | `src/pynq_host/cop_product_service.py:101`；`vision_live_service.py:121` | 真实自动轮也全量归档 capture、ROI、trace、packet，目录无容量/保留上限；用 10/30 的 886727 B PNG 仅作估算，一轮一张原帧、每秒两轮就约 6.4 GB/小时，实际受处理耗时限制，不是实测速率。写满磁盘的 OSError 也不在 do_POST 的 ValueError/RuntimeError 映射内。应保留证据要求并增加容量门限/明确停止与错误记录，不能静默删除证据。 |
| F10 | P2 / 复现路径 | `build/README.md:33`；`build/build_soc.tcl:32` | README 将新构建的位流位置写成 `others/build/run/...`，脚本实际输出 `build/run/...`。移动过的历史包位置与新构建输出混写，照文档容易找错包。须明确旧产物迁移位置与脚本实际产物位置。 |
| F11 | P2 / 提交材料缺口 | `docs/tech-report/latex/main.tex`；`sections/07-status-metrics.tex:14`；`docs/poster/README.md:3` | LaTeX 仍为 v0.1/10月30日、源码基线 a631fd2，团队信息及网页实机截图待补；状态表仍把真机手动/CSV 收尾列未实现，与10/30证据不符；成品图2仍含Windows EXE，与网页正文不一致。DOCX/PDF旧稿与海报明确标历史10/27，本身不是造假，但没有明确哪份是最终交付稿；旧海报展示退役 EXE 与“多目标待上板”，不能直接当当前版本提交。 |
| F12 | P2 / 状态与计数 | `plan.md:100`；`docs/project-overview.md:214`；`src/pynq_host/README.md:39,62` | 同时存在视觉Python20/21/19、检查链14/17/19等“当前”统计。实际脚本列表为视觉19、inspection17、INT8 10；网页与额外测试另列。应按入口自动计数或只保留权威清单，避免旧数字继续复制。 |
| F13 | P2 / 门禁失败 | `hygiene.log`、`index.log` | check_repo_hygiene/index_runs 均因 data/logs 索引过期退出1。本轮新增审查目录也必然需要收尾更新索引，不能把这次失败都归因于旧内容；当前日志同时包含原有10/30未跟踪目录。按最终文件集合重建后再检查。 |
| F14 | P2 / 覆盖表述 | `docs/tech-report/latex/main.tex` 摘要；`report/module1-closure.md` | 摘要的“44项架构测试”没有写出它是11个测试（3个I类+8个M类）×4档配置的44次签名运行，容易被当成44种不同架构测试。应明确子集和配置矩阵，不据此声称完整ISA认证；本轮44次复跑也采用相同口径。 |
| F15 | P1 / 微架构描述 | `docs/tech-report/latex/sections/03-riscv-core.tex:14`；`src/riscv/core_top.v:150` | 报告将三级写成IF/ID、EX/MEM、MEM/WB，并直接描述三路集成转发。实际冻结流水为IF / ID+EX / MEM+WB；`design_v1.md` §8.1和顶层接线均说明只启用EX候选（来自唯一MEM+WB槽的非load寄存结果），MEM/WB候选固定无效。通用单元有三来源端口，不代表顶层三路均启用。须改正文及配图，不把通用接口能力当集成实现。 |
| F16 | P2 / 工具输入边界 | `sim/scripts/export_trained_payload.py:50` | checkpoint导出工具使用`torch.load(..., weights_only=False)`，元数据检查发生在反序列化之后；外来checkpoint可以在校验前执行pickle代码。现役`inspection_model.py`已使用weights_only=True，两处边界不一致。建议导出路径也限制为权重安全加载，或显式只允许已核验的本地受信checkpoint；本轮未执行外来文件。 |
| F17 | P2 / 部署工具信任 | `sim/scripts/board_ssh.py:20` | SSH helper默认口令回退且使用AutoAddPolicy，没有加载/核验已知主机密钥；IP被误配或冒用时仍会把登录凭据交给未知主机。属于开发工具的信任边界缺口，不是本轮发现凭据泄漏。建议已知主机校验、明确开发专用默认账户边界，并避免静默信任任意主机。 |
| F18 | P2 / 性能口径 | `docs/tech-report/latex/main.tex:66`；`sections/01-overview.tex:33` | 摘要直接写整网472593拍，未说明该数来自含“每7拍暂停1拍”的仿真（`src/coprocessor/README.md:39`已说明）。10/28板端numeric-pass的trace另记录perf_cycles=405080。须把CE停顿仿真、无停顿硬件计数与PS取帧/定位/HTTP整轮耗时分开，不能把472593/40MHz当实板端到端延迟。BRAM补跑中额外一拍也应随配置说明。 |
| F19 | P2 / 已复现 | `sim/tools/verify_rv32i.py`，decode的JAL分支 | J-type立即数拼装为21位，但符号判断用了`1<<19`，应判断最高位20。`decode(0x800000ef)`输出`jal x1, 1048576`，正确有符号偏移为-1048576；部分大正偏移也会被错判为负数。只影响此教学辅助解码器；核的decode.v是另一实现，不能混称核RTL失败。见`probe-codec.py`、`codec-probe.log`。 |
| F20 | P2 / 已复现 | `sim/tools/verify_rv32i.py` 末尾 | 自测ok=False时只打印HAS MISMATCH，没有非零退出；在内存中注入一条错误golden后确认脚本正常返回。其反汇编自测只检查重新编码能否回到原机器字，也抓不到F19这种错误有符号显示。应让错误非零退出，并加入独立期望文本/立即数边界判据。探针未改原文件/原golden。 |

## 复杂、冗余与不合适的维护结构

| 编号 | 级别 | 观察与建议 |
|---|---|---|
| C01 | P3 | `src/web_client/index.html` 1213行混合布局、CSS、模拟场景、真实HTTP状态机、UVC、快照、回放、批次导出。跨功能改动难定位；F01是状态交互中的实际风险。后续按UI/传输/状态/演示数据拆分，提交前只做必要缺陷修复，避免整页重写。 |
| C02 | P3 | `cop_driver.py` 707行；run 函数135行、统计到27个分支类AST节点。读取/校验/看门狗/判定/追踪/缓存职责集中；`CopEngine._fields`108行亦承担多个阶段。复杂度统计只是审查提示，不等于错误；建议拆成阶段函数并保留现在的边界测试。 |
| C03 | P3 | Python 的 rounds/records/export 与当前网页各有一套轮次/记录/导出逻辑，Python及JS又各维护协议校验。Python README已称参考实现，因此不是可直接删除的死代码；但协议D10仍按records v2写“当前”，网页仅内存记录和8列CSV，语义已分叉。须标明现役消费者、参考范围及一致性用例。 |
| C04 | P3 | plan/总览/各README/报告生成器/LaTeX/海报多份复制现状，现已出现F02/F06/F11/F12。建议一份当前事实表，其余链接；历史材料清楚标日期。 |
| C05 | P3 | 卫生检查只检查README存在、选定跟踪Markdown链接等；不会验证README六要素、全部源码引用夹具、所有manifest内容或预算总量。文档预算也没有在该脚本自动执行，不能把 hygiene PASS 当完整仓库复现证明。 |
| C06 | P3 | hygiene列出10组≥100KiB重复blob，包括异常截图、HDMI IP文档、板卡/前端素材与重复控制台日志。见hygiene.log。部分是冻结历史快照，有来源价值；应先区分快照与可生成副本，再用单一素材/重建入口去重，不直接删历史证据。 |
| C07 | P3 | all 的TBS列表与多段追加、独立专项入口、Python for列表分散，新增测试容易忘记接总入口。建议维护一份测试清单及显式的“未纳入/原因”，不要仅靠全量脚本这个名字判断覆盖。 |

## 已知未闭环事项（非本轮新发现）

F04可恢复来源：提交`6bcd997`，原文件blob `818d4e1025ab31331df3664a3dd424e687639158`；SHA256及原方法签名存在性见`fixture-history.log`。本轮没有恢复文件、没有更改该测试。

- 10/30 第5轮 TASK_ERROR 后续 DMA 超时，重启恢复，根因和连续稳定性未解决。
- 垫圈/螺母分类误差、纸边误框、换实物泛化、正式精度与阈值未验收；33/33是训练/校准一致，不是独立精度。
- 网页工单下发、持久批次/异常截图、逐帧关联、连续运动检查与工业整机验收未实现/未完成。
- 协议/结果槽16目标能力、真实DMA单包上限15、产品策略10是不同上限，不能宣传成实板16目标完整业务验收。
- 真实硬件各轮保存证据是现有约束；F09应通过容量把关处理，不能用关闭归档掩盖。

## 最终验证结果

原始命令与日志见本目录README及各日志。`probe-web.mjs` 的PASS表示成功观察到缺陷，不表示产品已修复。
初次web/tex日志打印包装遇到Windows GBK输出问题，已用UTF-8包装重跑；以web-node-final.log、tex-final.log为准，不能将包装异常误算为产品失败。
初次默认iverilog进程因Windows DLL路径退出，使用脚本相同的ucrt64 PATH后Verilog-2001检查退出0；以verilog2001-retry.log为准。
arch最初缺suite，已由仓库fetch入口获取历史相同commit `6f7f47bdc61c0c51c0cbf75789678a1235eeefc2`；Git Bash下缺make，mingw32-make再遇POSIX路径问题；最终使用文档要求的MSYS2 bash/make执行，保留失败尝试供环境诊断。

| 检查 | 命令/入口 | 当前结果与日志 |
|---|---|---|
| 统一回归覆盖 | `bash sim/scripts/run_iverilog.sh all`，随后分段补齐 | 该all进程完成核基础/CNN RTL及Python/四档benchmark/nofwd+fwd CoreMark后，主动结束已另行执行的重复BHT阶段，进程退出1；`intentional-stop.log`记录具体被停进程。all命令本身未完整结束，不能记为all PASS；其检查集合已按下面分段入口完成。 |
| 软件检查链 | `bash sim/scripts/run_inspection_python.sh` | 17组完成，进程退出0；`inspection.log` |
| 网页HTTP | `python sim/vision/test_web_server.py` | 3项通过，退出0；`web-server.log` |
| 网页JS | `node --test sim/vision/test_web_protocol.mjs sim/vision/test_web_refresh.mjs` | 13项通过，退出0；`web-node-final.log` |
| 额外Python | 依次运行 `sim/vision/test_{class_aware_metrics,localization_data,n03_board_capture,n03_buffer_lifecycle}.py` | 前3项退出0，lifecycle退出1；`extra-python.log` |
| 审查探针 | `node --test data/logs/2026-11-03-offboard-audit/probe-web.mjs` | 复用9项原测试+2项缺陷观察，11项通过；`probe-web.log`；F01/F05仍未修 |
| arch-test | MSYS2中 `bash sim/scripts/run_arch_test_matrix.sh`，设置新ARCH_TEST_LOG_DIR | 11×4签名全部匹配，退出0；`arch-msys.log`、`arch-msys/` |
| CNN补充 | `bash sim/scripts/run_coprocessor_iverilog.sh bram_network`，然后 `watchdog` | 两个模式均退出0，`cop-supplement.log` |
| 独立板级示例 | MSYS2中 `bash board/smoke_test/sim/run_iverilog.sh` | DIV_CYCLES=1/2/5/8均通过，退出0；`board-smoke.log` |
| 教学工具探针 | `python data/logs/2026-11-03-offboard-audit/probe-codec.py` | F19/F20均复现，探针退出0；`codec-probe.log`；不表示原工具已修复 |
| 核后续专项 | `run_iverilog.sh` 的v1_hazard_fwd/nofwd、v1_muldiv_fwd/nofwd、bht_flow_off/1、v1_flow、vision_gate | 8个模式各退出0；`tail-core-gates.log`；门禁自检故意注入的FAIL均按预期拒绝 |
| 视觉RTL | `bash sim/scripts/run_vision_iverilog.sh all` | 25个tb全部完成，退出0；`vision-rtl.log` |
| 视觉Python | `bash sim/scripts/run_vision_python.sh` | 脚本19组完成，退出0；`vision-python.log` |
| CoreMark BHT两档 | `python data/logs/2026-11-03-offboard-audit/run-coremark-profiles.py --output data/logs/2026-11-03-offboard-audit/coremark-parallel` | 相同仓库tb、从原入口提取黄金参数，独立产物并行；两档均退出0；`coremark-parallel/results.json`及各档原始log |
| 语法/结构 | `python data/logs/2026-11-03-offboard-audit/audit-static.py` | 225个Python解析通过；`static-final.json` |
| Shell | `git ls-files -z '*.sh' \| xargs -0 -n 1 bash -n` | 退出0；`bash-syntax.log` |
| PowerShell | 对 `git ls-files '*.ps1'` 调用 `System.Management.Automation.Language.Parser.ParseFile` | 19个文件，未返回解析错误；未执行上板脚本 |
| Verilog-2001 | ucrt64优先PATH下 `iverilog -g2001 -tnull -i src/riscv/*.v src/vision/*.v src/coprocessor/*.v` | 退出0；`verilog2001-retry.log`；`-i`允许未解析外部模块，只证明解析/展开，不是综合/DRC |
| LaTeX静态 | `python docs/tech-report/latex/check_tex.py` | 10文件，ERROR 0、WARN 8（未引用章节label）；退出0，`tex-final.log`；没有新编译 |
| 卫生/索引 | `python sim/scripts/check_repo_hygiene.py --json`；`python sim/scripts/index_runs.py --check` | 均退出1（索引过期）；`hygiene.log`、`index.log` |
| 快照概览 | `python sim/scripts/snapshot_manifest.py --json` | 退出0；`snapshot.log`；概览不是恢复验证 |
| 恢复源校验 | 对5个 `data/logs/*/SNAPSHOT-MANIFEST.json` 各运行 `python sim/scripts/restore_snapshot.py --run <目录名> --check --json` | 全部退出0，无problem；`restore-checks.log`；只check，没有restore写回 |

arch正式复跑环境：`C:/msys64/usr/bin/bash.exe`，`PATH=/c/msys64/ucrt64/bin:/usr/bin:$PATH`，`ARCH_TEST_LOG_DIR=E:/Projects/FPGA-Alittle-Design/data/logs/2026-11-03-offboard-audit/arch-msys`。Git Bash的make失败是环境前提不满足，不算RTL签名失败。
`test-inventory.json`核对sim/vision下41个Python测试文件已全部分配到本轮实际执行的命令；其中40个脚本退出0，N03生命周期脚本因F04退出1。sim/coprocessor下15个Python测试文件由统一回归中的整数参考与各门禁函数覆盖。
预算补查：跟踪工作区131115130字节（约125 MiB），最大日志目录268文件，未超175MB与600文件预算；10组较大重复blob的完整路径见`budget-duplicates.json`。预算满足不消除F13索引失败。

CoreMark四档完成：nofwd=19057438、fwd=17114141、BHT1=16335562、BHT2=16232079周期；retired均为10106386，tohost=34713、exit=0，五个CRC均匹配。周期数与`report/module1-closure.md`一致；结构化结果见`coremark-results.json`。观察块的`errors_raw=1`是既有官方短测时长检查口径，收口报告已明确保留；本次没有把它改为0，也不声称官方认证分数。

结论：没有新增核/视觉/CNN分段仿真失败；不能给出“全仓无问题/全部检查PASS”结论。N03测试仍失败、卫生索引门禁仍失败，F01/F05/F19/F20的缺陷探针仍成功复现，提交材料与未跟踪文件仍待处置。
收尾：`git diff --check`退出0，原始空输出在`diff-check.log`；`final-status.log`显示原有改动之外只新增本审查目录。没有修业务代码、没有git add/commit、没有上板。源文件SHA256最终复核退出0。

## 成品文档预览范围

以PyMuPDF渲染现有18页旧稿、19页LaTeX稿和1页海报的全页联系图，另放大检查LaTeX PDF第4/6/7/16页。清单在`pdf-inventory.json`，预览生成物在`sim/build/offboard-audit-pdf/`（不入库）。联系图用于全局检查，不能等同于38页逐字高清人工校阅；本轮没有修改PDF，也没有重跑LaTeX排版。
放大页确认了F15正文与图4的转发描述问题；联系图中的图2仍为旧EXE架构，归F11。未发现需要另外立项的明显整页裁切；内容更新后仍须重新生成并检查最终成品。
