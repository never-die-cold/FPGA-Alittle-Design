# 2026-10-12 文档/实现核对证据

基线dev/model@3e2e1c9；之前的NC离板脚本、测试与恢复包已经暂存，本轮未更动这些生产代码/证据。当前新增差异为Markdown与本目录核对入口，不提交、不推送。

## 复现

仓库根目录、真实Python解释器执行；输出必须使用新文件名，避免覆写原始结果：

```powershell
python data/logs/2026-10-12-document-audit/check_documents.py --output sim/build/document-audit-new.txt
git diff --check
git diff --cached --check
```

实际解释器为C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe。
初次结果见[checks.txt](checks.txt)，修正文档边界后结果见[checks-final.txt](checks-final.txt)，补齐新增文件空白检查的最终结果见[checks-complete.txt](checks-complete.txt)：23份文档的247个本地链接目标存在，新增Markdown/检查器无尾随空白，源码入口包含25 RTL tb与14 Python组，两种diff空白检查退出0。链接检查不访问外网、不验证历史图片内容或Markdown锚点。

检查脚本是核对证据入口，不执行产品功能测试；功能结果仍引用[三PR原始回归](../2026-10-12-pr-review/README.md)和[前序离板回归](../2026-10-12-nc-offline/README.md)。
当前14组中的c01_build_inputs未提交；不能把当前工作区数量写成合并时已通过的数量。

## 人工核对

源码/契约/证据映射见[核对清单](../../../docs/implementation-document-audit-2026-10-12.md)。
重点核实State.check每次创建新轮次、BatchRecords.keys仅进程内、FILE/config无真实MMIO、C02/C03冻结而RTL未接入、原vision与C01来源证据分开。

历史日志/llm_log/外包原文/图像未改写。未实现项保留：真实安全DDR取帧、正式INT8整网包、CNN/核应用固件、硬件LIVE与完整工业发布验收。
