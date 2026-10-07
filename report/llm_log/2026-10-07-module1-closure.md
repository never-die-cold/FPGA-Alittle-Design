# 2026-10-07 协作记录：模块一收口复验与材料回填
> 标签：#riscv #verify #docs #skill候选
> 平台：Codex；本轮未提交。运行HEAD=dcb3ef7，RTL与96414be无差异，v0=partA-v0^{commit}=962a4f5。

最新状态：模块一技术PR #60已合并，#20/#21与M1已关闭；备考#61未完成。此前各阶段状态按时间保留，最新执行事实见§10。

## 1. 任务与授权
用户：“先完成模块一的全部收口工作吧”。
开工完成 workflow、主/核计划、v0/v1契约、gufa-programming 与 understand-gate 阅读；branch/log/status 已核对。
用户确认：“本次一次写完，理解题集中末尾”。该授权豁免逐步等待，理解门槛与禁止提前commit仍有效。
用户提醒另一智能体同时commit/push，随后确认其4个commit已结束；本轮未commit/push，避开Pi/视觉改动。

## 2. 方案与变更
- arch runner完善四档说明，矩阵扩原3条I+M八操作，新增M目标配置，链接容量与32KB核契约一致。
- run_iverilog增加bench_bht1/bench_bht2与all四档循环；复用同tb/镜像，不改RTL。
- PowerShell XSim入口编译同源码/tb，参数切四档，golden、周期/退休/BHT与Icarus锚点逐位核对。
- Tcl只读已有OOC routed checkpoints，补min/max、DRC/check_timing/clocks；默认转发/BHT1固定布线改约束11.520ns，未重综合布线。
- 汇总脚本校验44次官方签名、档间SHA、8个工作负载记录、4个XSim对拍和时序补证；由原始数据算CPI/收益。
- 更新README/主计划/核契约与看板，补报告、复现清单、指标与远程关闭草稿。历史交接单加最新入口，保留旧快照。
- data/metrics.csv追加30条记录；历史数值保留，旧CoreMark/LUT单位澄清为CoreMark/MHz/LUT，Pico空计划行回填10/03已有证据。

## 3. 失败与纠正
| 现象 | 纠正及证据 |
|:---|:---|
| 沙箱内MSYS2 NtCreateDirectoryObject拒绝；直接PowerShell Icarus异常退出 | 获准在沙箱外UCRT64环境运行；g2001-final退出0，旧失败记录保留 |
| XSim generic/testplusarg的等号被.bat拆开 | 参数值保留双引号；初期xelab/generated-C失败保留；最终沙箱外四档通过 |
| 本机MSYS2无cmp | 使用SHA256比较，逐档官方golden判据仍保留 |
| 尝试38条I+8条M，beq-01超32KB，overflow195388字节 | 保留arch-final.log及失败退出码；明确采用3条I+8条M扩展子集，不扩大测试RAM |
| 历史文档仍标三级待实现、125MHz硬触发L3或把86.8混称v0实点 | 以最新§16.4最低门禁回填；v0同脚本83.8为外推；100/125仍未通过 |

## 4. 原始结果
证据目录：data/logs/2026-10-07-module1-closure/。
- bash sim/scripts/run_iverilog.sh all → all-final.exit.txt=0；bench与CoreMark各四档，以及核/视觉/HTTP等回归全部完成。
- bash sim/scripts/run_arch_test_matrix.sh → PASS: arch-test matrix 11 tests x 4 modes；44次匹配golden，四档签名相同。
- ./sim/scripts/run_module1_xsim.ps1 → PASS: XSim four profiles match Icarus cycles/retired/bubbles/BHT and CRC golden。
- vivado audit_module1_ooc.tcl → BHT2 setup+0.538/hold+0.167、严重DRC0；fwd/BHT1固定布线11.520ns +0.933/+1.101。
- python sim/scripts/summarize_module1.py → PASS: 44 arch signatures; eight workload runs; four XSim matches; five OOC audits; two fixed-route gates。
- iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v → 退出0。
- RTL/tb/hex哈希运行前后保持一致；diff检查结果见本轮diff-check.log。
复用10/07 never-die-cold已归档的40MHz BHT2真实上板记录；本轮未再次下载/观察。
当前CoreMark CPI：nofwd1.885683、fwd1.693399、bht1 1.616360、bht2 1.606121；转发10.20%，BHT2净收益5.15%，当前nofwd→BHT2 14.83%。不同分母不相加。

## 5. 理解门槛讲解稿
### arch-test与编译配置
矩阵固定11个测试名及I/M扩展，不自动跳过失败。runner让套件编译ELF，找到签名起止符号，将同镜像加载到仓库tb的两片32KB存储模型。
每个参数档先由tb逐字校验官方reference，之后保存签名并比较SHA256。M目录的include复用目标公共配置，-march=rv32im由套件M Makefile提供。
link.ld从16K对齐到核契约32K，M中divu等镜像约18KB需要该容量；没有改变核容量。新增防覆盖条件拒绝复用旧证据目录。

### benchmark与XSim入口
benchmark使用与CoreMark相同的通用tb，但hex/checksum和最大周期不同。新增入口仅覆盖elaboration参数，all顺序跑四档，不共享正在运行的同名vvp实例。
XSim入口保留generic/testplusarg双引号，避免.bat拆等号。生成物隔离到sim/build/module1-xsim，日志记录源码与hex哈希。
Invoke-XTool检查native退出码，之后对输出中的PASS/BHT记录与Icarus锚点进行比较；tb仍按原golden校验exit/result/CRC。不同档使用同tb/hex。

### OOC与汇总
audit只读post_route.dcp，不写位流或改变磁盘上的检查点。五个原约束点保留PASS/FAIL；主档11.520ns必须通过setup/hold，所有点需严重DRC0。
默认转发和BHT1在固定布线设计上换11.520ns时钟，再做STA。这个结果独立标记，不能称为该约束下重新综合布线。
summarize从8个PASS及其BHT/CLASS/obs记录读取数据，检查cycles=retired+bubbles、分类总和、hit+miss=lookup、跨档退休一致、CRC及签名。
CPI用全局cycles/retired；CoreMark/MHz用32×1e6/(t1-t0)。它们窗口不同。关闭BHT事件为0，命中率不适用。
核OOC与40MHz真实SoC频率分开；主档最高已有通过点86.806MHz，未证明绝对Fmax。报告保留100/125MHz失败和未实现PS/CNN/特权接口。

### 末尾3题（已呈给用户，答案与判定待补）
1. 四档签名SHA相同，为什么仍逐档比官方golden？能/不能证明什么？
2. XSim BHT2误传成BHT_MODE=0，CRC仍可能正确，哪些记录发现档位跑错？
3. BHT2@11.520ns WNS+0.538但@10ns -0.586，能否宣布100MHz或当板上频率？
用户已回答，完整答案及评定见下方追加记录；第2题补课后再测通过，本轮理解门槛已通过。

## 6. 遗留与经验
技术收口复验完成，理解门槛补测通过；正式入库、#20/#21/里程碑状态在发布证据后处理；远程issue备考条目本轮未验证。
未实现/未接入：PS↔核AXI/中断、CNN指令/MMIO、地址表、工业检查固件、CSR/特权/异常。未做完整ISA认证或官方长测。
CPI/四档公平对比、固定路由时序检查与版本哈希流程已写docs/module1-reproduction.md，标#skill候选；尚未创建正式技能包。

## 7. 理解门槛：用户完整回答、评定及补测
### 用户答案1（原文）
### 四档签名 SHA256 相同，为什么还要逐档比对 golden？

SHA256 相同意味着四份产物在字节层面完全一致，但它**不告诉你这些字节代表什么功能**。如果四档来自同一套错误配置编译出的同一份文件，SHA256 会全部相同，却没有任何一档符合 golden 的预期行为。验证的核心要求是用**独立参考模型**（golden model）来断言设计的行为是否正确，而不是断言“四个副本彼此一样”。四个副本彼此一样只能排除“分发过程中某一份被篡改或损坏”，不能排除“源头本身就是错的”。

能证明的：分发完整性、文件一致性、没有意外混入不同版本。不能证明的：该版本的功能正确性、配置参数正确性、与其他版本的功能等价性。

评定：独立golden及共同错误的核心理解正确。需要澄清对象：本轮哈希的是DUT执行后的测试签名，不是分发文件。跨档一致支持这11个测试签名观察范围内的结果一致，不能证明完整ISA或所有程序等价；逐档golden还检查共同结果是否正确。

### 用户答案2（原文）
### 误传 BHT2 参数，怎么从记录里发现？

如果 BHT_MODE 误传为 0，而程序结果和 CRC 仍正确，说明该测试用例根本没有触发 BHT2 与 BHT_MODE=0 之间的行为差异。这种情况下，**靠结果比对或 CRC 无法发现参数跑错**。

能发现参数档位跑错的记录是：**测试启动时打印或落盘的“配置参数快照 / DUT 配置回读记录”**。验证流程中，DUT 配置参数应当被显式记录并与预期配置做比对，而不是仅依赖仿真输出是否“看起来正确”。具体来说，本轮脚本应查看的是：运行日志开头打印的 `BHT_MODE` / `BHT2` 相关参数值、配置数据库下发给 DUT 的命令行记录、或仿真初始阶段的参数转储。如果这些记录显示 `BHT_MODE=0` 而非预期的 `BHT2`，那就是发现跑错的唯一可靠依据。

评定：CRC不足以判断参数正确这一点正确；“没有触发行为差异”和“唯一可靠依据”不正确，也未指出本次脚本实际比较的记录，需补课再测。

补课：预测器可以改变周期和误预测冲刷数，同时保持退休指令、结果和CRC相同，这是正确预测优化的预期行为。run_module1_xsim.ps1逐档按顺序比较完整PASS与BHT行，既检查BHT实际mode和计数，也检查cycles/retired/bubbles；不是只看CRC或预期命令行。
原始BHT2：BHT: mode=2 lookup=1854101 hit=1690538 miss=163563；PASS: coremark mode=1 cycles=16232079 retired=10106386 bubbles=6125693 cpi=1.606。
原始fwd：BHT: mode=0 lookup=0 hit=0 miss=0；PASS: coremark mode=1 cycles=17114141 retired=10106386 bubbles=7007755 cpi=1.693。
PASS行的mode=1是转发开关；BHT行的mode=2才是BHT档位。若BHT2误跑成fwd，即使CRC相同，这两条记录仍不匹配BHT2参考，脚本报Icarus/XSim counters differ。一般情况下单看周期不能唯一识别所有配置，本轮采用实际mode、计数和周期联合检查。

### 用户答案3（原文）
### 11.520ns WNS=+0.538、10ns WNS=-0.586，能宣布通过 100MHz 吗？

**不能宣布核已通过 100MHz。** 理由如下。

100MHz 对应时钟周期 10ns。在 10ns 约束下，WNS = -0.586ns，意味着**建立时间违例**，时序未收敛。WNS 为负是“不满足时序”的直接证据，无论其他参数下表现如何，都不能说该核在 100MHz 下时序闭合。

11.520ns 下 WNS = +0.538ns，确实对应一个比 100MHz 更宽松的频率（约 86.8MHz）。这表明核在约 86.8MHz 下可以时序收敛，但这**和 100MHz 没有任何关系**。

**更不能把核频率说成板上运行频率。** 仿真/综合中的时序约束反映的是静态时序分析（STA）在特定工艺角、电压、温度下的估算条件，而板上实际运行的频率取决于 PLL 配置、PCB 信号完整性、电源噪声、温度漂移、以及是否有额外的时钟树不确定性。仿真通过只说明“在该约束下 STA 收敛”，不等于“芯片在真实板卡上跑这个频率不会出错”。把约束频率当作板上运行频率，是典型的过度宣称。

评定：通过。术语澄清：这里是实现后STA通过，不是仿真证明时序；11.520ns是已有通过的约束点，不能推导绝对Fmax。核OOC和完整SoC的时钟/路径范围不同；本轮复用的真实板上观察频率为40MHz。

### 补测1题
假设某条日志写PASS: coremark mode=1且CRC正确，但BHT: mode=0 lookup=0 hit=0 miss=0，能把它作为BHT2通过证据吗？解释两处mode分别表示什么，以及本轮XSim脚本为什么会拒绝它。
用户补测答案（原文）：
**不能作为 BHT2 通过证据。** 这条记录里虽然 `PASS: coremark mode=1` 且 CRC 正确，但 `BHT: mode=0 lookup=0 hit=0 miss=0` 明确显示 BHT 相关逻辑根本没有按 BHT2 工作，甚至可能完全没被激活。脚本拒绝该结果是正确的。

最终判定：补测通过。用户已正确区分结果/CRC通过和BHT实际档位，识别关闭BHT不能作为BHT2证据；两处mode语义已在补课与答复中说明。理解门槛通过，可继续正常提交。本轮未修改RTL，无需因文档补录重复长仿真。

## 8. 入库检查补记
暂存后git diff --cached --check首次检查到新归档的Vivado报告/XSim日志原生尾随空格；此前未暂存diff不包含这些新文件，不能代替完整暂存检查。证据目录新增.gitattributes，原始输出和签名设置-text/-whitespace，保留字节及行尾，不修剪原始证据；README和属性文件继续检查空白。修复复现文档末尾空行后重新检查暂存差异。
本轮工作提交到dev/bench；独立PR基于main，仅带核声明修正96414be、板级报告归档dcb3ef7和本轮收口提交，避免审查范围混入Pi/视觉WIP。原dev/bench已有四个提交完整保留。
收口工作提交1cf5f2c；独立checkout证据汇总再次PASS。完整PR差异还包含上述依赖提交的历史Vivado输出，根.gitattributes为data/logs/2026-10-07-partC-postopt与build/reports/soc_40mhz_bht2增加定向-whitespace例外，Markdown仍检查空白；不修改历史原始报告。首次PR差异检查失败输出留pr-diff-check-before-attributes.log。

## 9. 发布状态与自动审核
dev/bench本轮技术提交1cf5f2c、归档属性补记169cf01；独立分支codex/module1-closure当前对应ad6db82、c9ce3f0，包含必要依赖fe31bf4与0454364。独立工作树汇总与完整PR差异检查通过，测试输入与原验证内容一致。
尝试git push --atomic -u origin dev/bench codex/module1-closure时，自动批准审核拒绝。理由原文：This pushes repository contents, including potentially sensitive source and evidence, to an external GitHub destination and updates two remote branches; the user authorized the local closure work but did not explicitly authorize this exact payload and destination.
未执行被拒绝的推送，未使用连接器或其他命令绕过；未创建远程PR、未发评论、未更新/关闭#20/#21或M1。目标origin=https://github.com/never-die-cold/FPGA-Alittle-Design.git；推送源为dev/bench及codex/module1-closure，载荷是模块一代码、验证入口、原始日志和报告。
PR描述已按模板准备docs/module1-pr.md；远程检查点更新草稿仍在docs/module1-issue-closeout.md。发布需用户明确授权；main合并及非作者复核仍是后续审查步骤，不能用理解门槛替代。

## 10. 正式发布、合并与收口
用户明确回答：“允许推送、创建PR并更新清单”，随后指令：“该关的issue关掉，开PR，合并，同步各分支”。原推送拒绝的授权缺口已补齐，未绕过原拒绝。
dev/bench@29e6864与codex/module1-closure@2f758df推送成功，草稿PR #59创建并附到本会话，#20/#21技术清单先更新但未提前关闭。
GitHub连接器及GraphQL转待审接口连续内部错误；REST查询确认#59仍draft。保存pr59-before-merge.json后关闭草稿保留记录，REST以相同head创建正式PR #60并附到会话；不是删除审计或强写main。
protect-main要求1审批，并为当前用户270969795配置User/always管理员例外。用户在本会话通过理解门槛并明确要求合并；按该授权和既定例外，通过REST精确head合并#60。没有伪造非作者署名。
实际merge commit=f3668f73ad2e6e779f5a2afe066e532770f94a02，结果见pr60-merge.json。完整代码证据与输入不变，独立checkout汇总再次PASS；仅回填文档和原始执行元数据，无需重复长仿真。
未验证备考移交独立issue #61并保持open；#20/#21以completed关闭。M1汇总计数曾仍显示2，但实际issue状态closed、按milestone=1过滤open列表为空；以真实列表核验后关闭M1，见m1-closed.json。
分支同步范围：main、dev/bench、dev/rtl、dev/verify、dev/vision、dev/model、CNN、codex/module1-closure。dev/bench合并main保留原Pi/视觉及所有收口提交；其余分支按祖先关系快进，禁止强推。RTL工作树未跟踪的d3-repro/id_ex_ooc日志保留，detached的其他聊天工作树不改动。
最终状态文档及API原始结果经后续纯文档PR发布；同步验收入口为git merge-base --is-ancestor origin/main origin/<branch>与git status --short，最终Git引用本身保留同步结果。
