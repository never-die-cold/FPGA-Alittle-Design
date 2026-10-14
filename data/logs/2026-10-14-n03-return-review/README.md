# N03返板包离板复核

2026-10-14，HEAD见head.txt；保留上一轮C04文档改动。本轮无生产代码/RTL修改，无硬件访问、提交或推送。
inputs/保存三份执行源码原始字节，runner-inputs.json为SHA256/长度；局部.gitattributes禁止行尾转换。板端实际上传仍未执行。

## 仓库根目录复现（python）

| 命令 | 本目录结果 / 退出码 |
|---|---|
| python -u sim/vision/test_c01_capture.py | c01-capture.txt / exit=0；七组OK |
| python -u sim/vision/test_c01_status_onboard.py | c01-status.txt / exit=0；正常及故障替身/下载前检查/恢复重试PASS |
| python -u sim/vision/test_c01_artifacts.py | c01-reset.txt / exit=0；八个复位负例PASS |
| python sim/scripts/check_c01_artifacts.py sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.bit --output <仓库内新JSON> | candidate-artifacts.json/txt / exit=0；offline_candidate_only |
| python sim/scripts/audit_c01_build_inputs.py data/evidence/2026-10-12-c01-exact-build-inputs/manifest.json --output <仓库内新JSON> | build-inputs.json/txt / exit=0；98项匹配、changed=2/missing=0 |

PowerShell语法检查：`python -c (Get-Content -Raw data/logs/2026-10-14-n03-return-review/runner-syntax.command.txt)`；runner-syntax.txt/exit=0，只compile不import/执行板端入口。
解释器为C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe；每项*.exit.txt原样保留，状态日志MAIN-FAIL为预期注入。
上述三项tb已接入run_vision_python.sh；无RTL改动，未重复全量RTL。inputs与当前源码哈希一致不证明板端依赖或实机通过。
源码关键边界见runner-excerpts.txt；被测tb/审计器/本机依赖指纹见review-input-sha256.json。prior-docs-sha256.json记录开工时C04状态，随后依NC明确确认更新，不声称其字节未变。
git diff --check见diff-check.txt/exit文件，新文档链接/空白核对见document-check.txt；[返板执行单](../../../docs/n03-custom-return-runbook-2026-10-14.md)列未验收项与实验边界。
