# 数据集审计：原始验证记录

所有测试临时目录位于仓库 sim/build/vision/inspection；最终夹具在 data/evidence。

| 仓库入口 | 原始日志 | 结果 |
| --- | --- | --- |
| python sim/vision/test_dataset_manifest.py | rows.log、frames.log、manifest.log、manifest-final.log | 行/帧/路径/编号/框/格式/遗漏/上限拒绝 PASS |
| python sim/vision/test_dataset_audit.py | leakage.log、leakage-final.log、cli-tests.log、audit-final.log | 泄漏、覆盖、隔离 CLI、覆盖/中断/非法数据拒绝 PASS |
| bash sim/scripts/run_inspection_python.sh | inspection-all.log、inspection-final.log | 修复前/最终十三组均 PASS，退出 0 |
| python sim/vision/generate_dataset_audit_fixture.py ... | fixture.log | 四帧/三虚构目标夹具生成 PASS |
| python -I sim/vision/audit_fastener_dataset.py ... | report.log、report-final.log | 初次 CRLF/最终 LF 夹具分别审计通过，退出 0 |
| 归档夹具重新审计到新文件 + SHA256 对照 | reproduce.log、bytes.log | 与最终报告逐字节一致，Git filter 保持证据原字节 PASS |
| git diff --check + 新增文本检查 | diff-check.log、new-text-check.log | 退出 0；末尾空白/合并标记检查 PASS |

对应命令退出码保存在同名 .exit.txt；负例子进程的失败由测试检查，不计作正例通过。
首次 CSV 默认 CRLF，归档前发现 Git 文本换行转换会改变摘要；夹具写入显式改 LF，
原始 CSV 字节保留为 initial-manifest.bin，首次报告保留为 initial-report.json。
修复后新增两组和最终十三组重新通过；已有十一组实现未改。
最终复算/字节与换行检查通过，不把 TEST_FIXTURE 的结构 PASS 当作真实数据或精度验收。
