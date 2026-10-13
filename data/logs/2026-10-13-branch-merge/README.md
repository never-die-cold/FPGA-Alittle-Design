# 三分支 PR 合并与合并后回归（2026-10-13）

用户指令：为各分支开 PR 合并、同步各分支、拉回本地。本目录保存合并后的回归证据。

## PR 与合并

| PR | 分支 | 内容 | 结果 |
| --- | --- | --- | --- |
| #72 | dev/riscv | J01 审计决策 + Conv/GAP/FC 与整网/结果 INT8 参考（8 项 Python 测试） | admin--merge，main=1fc12ad |
| #73 | dev/exe | 真引擎服务、联合回归、G0 样例报文（服务/EXE 链） | admin--merge，main=8725cbb |
| #74 | dev/model | CNN 算子/整网/OOC + C01 DDR 单帧 + 10-13 证据链等 19 笔 | 见推送后合并记录 |

dev/vision 与 main 相同（3e2e1c9），无可合并内容，不开 PR。

## 冲突解决（origin/main 并入 dev/model，合并提交 12fe250）

| 文件 | 解决方式 |
| --- | --- |
| sim/scripts/run_coprocessor_python.sh | 测试列表取并集：model 的 network + riscv 的 conv_layer/gap_fc/result/model_schema/model_trace（保留 model 的 PY/COPROCESSOR_PYTHON 入口） |
| sim/scripts/run_vision_python.sh | 并集：exe 的 vision_joint + model 的 c01_build_inputs/c01_capture |
| docs/coprocessor-integration-v0.md | C03-P6 行合并：10/16 分层已由 JL 正文冻结 + C04 应用层评审待完成 |
| docs/module3-model-training.md | 变更记录保留 10-12/10-13 两行；阵列/黄金/收口表双方改动自动合并 |

冲突标记清零、`bash -n` 两个脚本通过；本次合并未改任何 RTL。

## 合并后回归（本目录原始输出）

| 套件 | 命令 | 结果 |
| --- | --- | --- |
| 协处理器 Python | `bash sim/scripts/run_coprocessor_python.sh all` | [coprocessor-python.txt](coprocessor-python.txt) / exit=[exit](coprocessor-python.exit.txt) 0；9 组 PASS |
| 视觉 Python | `bash sim/scripts/run_vision_python.sh` | [vision-python.txt](vision-python.txt) / exit 0；16 组 PASS（含 vision_joint、c01_build_inputs、c01_capture） |
| 离板检查 Python | `bash sim/scripts/run_inspection_python.sh` | [inspection-python.txt](inspection-python.txt) / exit 0；14 组 PASS（含 service_engine） |
| RTL 全量 | `bash sim/scripts/run_iverilog.sh all` | [rtl-all.txt](rtl-all.txt) / [exit](rtl-all.exit.txt) 0；123 项 PASS；四档 bench 周期 2850/2423/2380/2351，CoreMark 19057438/17114141/16335562/16232079（CPI 1.886/1.693/1.616/1.606，与黄金一致）；日志中 FAIL/FATAL 行均为 vision_gate 门禁自检注入的预期拒绝 |

运行环境：MSYS2 `C:/msys64/usr/bin/bash.exe`，PATH 优先 `/ucrt64/bin:/usr/bin`，`TMP=/c/Users/ASUS/AppData/Local/Temp`，`VISION_PYTHON=/c/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe`。

## 边界

本目录只证明合并后的三个 Python 入口与 RTL 回归在当次工作树通过；不等于板端验收，不改变各任务原有未验收状态。
