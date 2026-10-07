# 2026-10-07 模块一收口复验
运行HEAD=dcb3ef7；RTL与96414be无差异。当前源文件与版本信息见source-manifest.json、source-stability.log及xsim-pass/environment.json。
最终技术结论见../../../report/module1-closure.md；用户理解门槛补测通过，完整问答及判定见../../../report/llm_log/2026-10-07-module1-closure.md。运行HEAD是验证时版本，收口脚本和证据由包含本文件的提交发布。

| 证据 | 原始结果 |
|:---|:---|
| all-final.log / all-final.exit.txt | 完整all退出0；新增benchmark四档及CoreMark四档，各结果一致 |
| arch-complete.log / arch-final.exit.txt / arch-complete/ | 11条I/M子集×4档，44/44 golden及SHA256一致，退出0 |
| xsim-pass/ | 优化后四档与Icarus cycles/retired/BHT/CRC一致 |
| ooc-complete.log / ooc-complete/ | 五个原约束点hold/严重DRC通过；BHT2@11.520ns setup+0.538/hold+0.167 |
| ooc-complete/固定布线补证 | fwd/BHT1@11.520ns +0.933/+1.101；未重综合布线 |
| summary.json / summary.log | 八个工作负载、44签名、4对拍、5审计及2固定布线门禁交叉核对PASS |
| verilog2001-final.log | iverilog -g2001，退出0 |
| source-stability.log / checkpoints.sha256.json | 源码输入稳定；被审计的DCP哈希留存 |
| diff-check.log | 最终git diff --check原始输出 |

## 复现入口
- bash sim/scripts/run_iverilog.sh all
- ARCH_TEST_LOG_DIR=<新目录> bash sim/scripts/run_arch_test_matrix.sh
- ./sim/scripts/run_module1_xsim.ps1 -LogDir <新目录>
- vivado -mode batch -source sim/scripts/audit_module1_ooc.tcl -tclargs <新目录>
- python sim/scripts/summarize_module1.py data/logs/2026-10-07-module1-closure
完整环境、全新checkout的checkpoint构建前置与日志命名约定见../../../docs/module1-reproduction.md。
本目录.gitattributes保留原始工具日志和签名的字节及行尾，关闭生成文件的空白格式检查；README与属性文件仍检查空白。不得修剪原始报告来迎合代码格式检查。

## 保留的失败与边界
- arch-matrix.log：首轮无cmp，停在add-01四档后；改为SHA256。
- arch-final.log / arch-capacity-fail.exit.txt：扩大38I+8M时beq-01超32KB（overflow195388字节），总退出2。最终声明子集11条，不冒充上游全套。
- xsim/、xsim-retry/、xsim-final/：初期等号拆参、沙箱C编译/启动失败；最终xsim-pass成功。
- ooc-audit.log：沙箱内Vivado启动失败；ooc-final是第一轮五点审计；ooc-complete增加固定路由两点。
- verilog2001.log：直接PowerShell调用异常退出；UCRT64最终入口成功。
- arch-preserve-gate.log：旧证据目录防覆盖的预期拒绝，非功能失败。
- all中FAIL: injected是既有vision门禁的预期注入，最终总退出0；其他真实失败不被忽略。
- 100MHz的fwd/bht1/bht2 setup失败保留；v0的83.8MHz是外推，本轮86.806MHz是约束点，SoC真实上板仍为40MHz。
- 本轮复用../2026-10-07-partC-postopt/的真实上板观察；未重新下载。CoreMark短仿真不构成官方≥10s分数。
