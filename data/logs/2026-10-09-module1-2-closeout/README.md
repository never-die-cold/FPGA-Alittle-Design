# 2026-10-09 模块一／二文档收口复跑证据

本轮整理文档／已授权注释，并应用用户批准的B07帮助文字／B13默认路径修复；未修改核RTL、测试判据或历史数据。未commit／push。
被检查 HEAD：`051aefaae9841e16237cc65a004b2c5ee5ec995d`（main）；工作区文档有未提交改动。
完整改动及待办见[收口工作报告](../../../report/llm_log/2026-10-09-module1-2-closeout.md)。

## 命令与原始证据

| 命令／检查 | 日志 | 状态 |
|:---|:---|:---|
| `bash sim/scripts/run_iverilog.sh all`（B13后完整重跑） | [all-b13.log](all-b13.log)、[all-b13.exit.txt](all-b13.exit.txt) | exit=0；57个tb运行块均有PASS，23视觉tb＋7 Python检查通过 |
| 同一 all 的第二次沙箱外运行 | [all-host.log](all-host.log)、[all-host.exit.txt](all-host.exit.txt) | 依用户停工请求中断，exit=143；未完成 |
| 同一 all 的首次沙箱内运行 | [all.log](all.log)、[all.exit.txt](all.exit.txt) | 主动中断，exit=143；不能作完整 PASS |
| `bash sim/scripts/run_iverilog.sh vision_python`（沙箱内） | [vision-python-precheck.log](vision-python-precheck.log) | exit=1；HTTP socket 被沙箱拒绝 |
| 同一 vision_python（沙箱外） | [vision-python-host.log](vision-python-host.log) | exit=0；7 项 PASS；未改测试 |
| `ARCH_TEST_LOG_DIR=data/logs/2026-10-09-module1-2-closeout/arch-matrix bash sim/scripts/run_arch_test_matrix.sh` | [arch.log](arch.log)、[arch.exit.txt](arch.exit.txt) | exit=0，11 测试×4档，44/44 |
| `iverilog -g2001 -Wall -tnull -s core_top src/riscv/*.v` | [core-g2001.log](core-g2001.log) | exit=0，无输出 |
| `grep -rn '(\.\*)' src/` | [implicit-ports.log](implicit-ports.log) | exit=1，无匹配（符合静态门） |
| `git diff --check` | [diff-check-final.log](diff-check-final.log) | exit=0，无输出；此前diff-check为历史快照 |
| `bash -n sim/scripts/run_iverilog.sh` | [b13-bash-syntax.log](b13-bash-syntax.log) | exit=0，无输出 |
| B13源码范围核对／无效模式帮助入口 | [b13-scope-guard.log](b13-scope-guard.log)、[b13-help.log](b13-help.log) | runner流程与continue不变；帮助测试exit=1符合预期；Windows待验证 |

完整 all 从头重新执行，未使用沙箱内已跑部分拼接为 PASS。
首次中断原因：协议预检已确认沙箱不能建立本地 HTTP socket，避免继续长跑后再遇相同失败。
vvp 收到 TERM 后可返回 0；因此另停止父 all，记录 exit=143，并核对重跑的各项 PASS。

## 索引、指纹与工具差异

- [file-index.txt](file-index.txt)：修改前 5,978 项，逐路径作用、字节数与 SHA256。
- [inventory-command.txt](inventory-command.txt) 从 [read-snapshot.tsv](read-snapshot.tsv) 可复建该初始索引；[索引指纹](file-index.sha256)不代表修改后源码。
- [environment.json](environment.json)：本机 Icarus 11.0／GCC 10.2.0／Python 3.10.12；历史验收 Icarus 13.0／GCC 14.2.0 分开记录。
- [rtl-fingerprint.log](rtl-fingerprint.log)：16 份核 RTL 与 10/07 manifest 一致；[doc-static.log](doc-static.log)：vision_top 去注释后 HDL 不变、24份引用核 tb 均在库。
- [arch-matrix/environment.txt](arch-matrix/environment.txt)：arch 套件完整 commit、工具版本及工作区 diff 指纹。
- [inventory-links.txt](inventory-links.txt)、[tag-status.log](tag-status.log)：Q06 缺失链接／Q03 本地 tag；未查询远端。
- [proposed-script-changes.patch](proposed-script-changes.patch)：18增删行，用户批准后已应用；默认40MHz／fwd／BHT关不变。
- [最新续工记录](../../../docs/resume-2026-10-09-module1-2-closeout.md)保留停工快照并追加恢复状态，旧scope-guard／documentation.patch为B13前快照；原diff归档改扩展名，字节未变。
- [本次运行源码指纹](b13-run-source-manifest.json)记录44项源码／tb／脚本／hex及dirty状态；[复核日志](b13-run-source-recheck.log)确认运行期间未变，diff范围为`src/riscv sim`。
- [最终Verilog-2001静态门](core-g2001-final.log)exit=0、零输出；[隐式端口扫描](implicit-ports-final.log)无匹配，命令exit=1为预期。
- 本机没有 Vivado／XSim／tclsh；本轮没有新增 WNS、Fmax、资源、bitstream 或上板证据。
- 原始 timescale／readmemh 提示均保留，不以静态门零输出冒充所有回归日志无 Warning。
- [matrix-summary.json](matrix-summary.json)与[matrix-check.log](matrix-check.log)：同次all四档CoreMark／benchmark，CRC／退休数一致、分类与周期差对账通过；复跑：`bash data/logs/2026-10-09-module1-2-closeout/matrix-check-command.txt`。
- vision_gate中的FAIL／ERROR／FATAL是预期故障注入；8例逐项核对accept／reject，不能把这些负例当DUT失败或删掉。
