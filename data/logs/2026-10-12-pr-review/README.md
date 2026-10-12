# 2026-10-12 PR #69/#70/#71 审查证据

用户要求：审查、合并并同步各分支。被审 head 见 reviewed-heads.txt（顺序 #69/#70/#71）。

## 本轮验证

环境：Windows，MSYS2 UCRT64 Icarus，Python 3.12 / NumPy 2.5.1。
MSYS2 必须使用 C:/msys64/usr/bin/bash.exe，PATH 以 /ucrt64/bin:/usr/bin 开头；系统 bash/python3 应用别名不可用。
VISION_PYTHON=/c/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe。
协处理器统一入口的 python3 使用 sim/build/pr-review/tools/python3 两行启动适配，exec 上述 Python；未改产品源码。

| 命令/对象 | 原始输出 | 结果 |
|---|---|---|
| bash sim/scripts/run_iverilog.sh vision all（#69） | pr69-vision-rtl.txt | 25 tb PASS，exit=0 |
| bash sim/scripts/run_vision_python.sh（#69） | pr69-python.txt | 11组 PASS，exit=0 |
| iverilog -g2001 -tnull -s capture_status_axi src/vision/capture_status_axi.v src/vision/capture_stream_monitor.v src/vision/capture_fault_cdc.v src/vision/reset_sync.v | pr69-verilog2001.txt | 默认 Verilog-2001 解析 exit=0 |
| python -u sim/vision/test_n03_board_capture.py / test_n03_buffer_lifecycle.py | pr69-n03.txt | 5类假驱动/释放生命周期 PASS，exit=0；不证明板上根因 |
| bash sim/scripts/run_vision_python.sh（#70精确源码快照） | pr70-python.txt | 10组 PASS，exit=0 |
| bash sim/scripts/run_coprocessor_python.sh all（#71精确源码快照） | pr71-python.txt | 标量/张量/卷积3组 PASS，exit=0 |
| 预演三PR合并，保留双方回归名单 | integration-python.txt | 13视觉+3协处理器 PASS，exit=0 |
| 实际dev/exe解决名单冲突后 bash sim/scripts/run_vision_python.sh | pr70-integrated-python.txt | 13组 PASS，exit=0 |

快照在仓库内 sim/build/pr-review/，由 git archive 精确 ref 生成；#70 包含 src、sim/scripts、sim/vision、data/golden、docs 及 data/evidence/2026-10-03-arm-localize-baseline；#71 包含 src/coprocessor、sim/coprocessor 与两个统一入口脚本。不得使用工作区外临时文件替代这些输入。
初次 #70 快照漏带 ARM 既有测试数据导致失败，补齐后全量通过；初次 Bash 使用登录/系统别名、Python3 应用别名、沙箱原生进程限制均不是产品 FAIL。当前有效原始结果为表中所列最终运行。

## 完整 all 回归证据及重复运行边界

既有 data/logs/2026-10-11-c01-capture-rtl/full-regression.txt 与 full-regression-exit.txt=0 保留完整四档 CoreMark、核、视觉和当时Python全量原始输出。
当前 src/vision/*.v 与该目录 final-inputs/src/vision/*.v 哈希逐项一致；src/riscv/ 相对 c292038 无变更。新增视觉/最终Python另由本轮入口复验。
本轮还启动了 bash sim/scripts/run_iverilog.sh all，nofwd CoreMark PASS（cycles=19057438、retired=10106386）后，为避免重复未修改核心的长计算主动停止。pr69-rtl-all.txt 及 pr69-rtl-all-cancelled.txt 如实保留，**此取消运行不是完整 PASS**。后续被停止的进程只限本次已核查命令行的进程。

## 差异及合并预演

PR69 源码/脚本/tb/文档差异 git diff --check=0；#70/#71完整PR差异=0，原始结果在 *diff-check*。
PR69完整差异 git diff --check=2，原因是历史原始证据的CRLF/尾随空格；完整诊断保留 pr69-full-diff-check.txt，未修剪历史字节。本目录 *.txt 定向保留原字节/禁用空白告警，Markdown仍检查。
git merge-tree 预演：#69+#70 仅 sim/scripts/run_vision_python.sh 冲突；#69+#71 无冲突。解决方式为保留双方全部新增测试，共13组。

理解题、用户全文回答、判定/状态校正见 report/llm_log/2026-10-12-three-pr-review.md。

## 未实现/未接入

CNN RTL、首网硬件结果、C01 DDR帧槽所有权/真实颜色对拍、N03长测、正式硬件LIVE、工业闭环均未完成。C04未决项不因合并自动冻结。当前候选CDC的8 Critical仍按原报告披露。
