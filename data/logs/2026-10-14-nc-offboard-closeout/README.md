# NC扩展离板交付与Windows候选验收

2026-10-14，`dev/model@5654eb5`；用户要求“不局限于现在，快点做”。前序C04/N03改动保留，不新增生产代码/RTL，不操作板卡/UVC，不提交/推送。

## 实际完成与原始结果

| 命令 | 原始输出 / 退出码 |
|---|---|
| powershell -File sim/scripts/build_vision_client.ps1 -Python C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe | build-exe.txt/exit=0；selftest、MOCK HTTP、LIVE桩引擎联合、FILE回放/冲突/篡改拒绝全部PASS |
| sim/build/nc-offboard-release-20261014/vision_preview/vision_preview.exe --selftest | portable-selftest.txt/exit=0；完整复制包，清除PYTHONPATH/PYTHONHOME/VIRTUAL_ENV，PATH仅System32 |
| 同EXE --replay sim/build/nc-offboard-release-20261014/replay-example/result.json --headless --save <仓库内新PNG> | portable-replay.txt/exit=0；portable-replay.png已目视核对FILE REPLAY/PROTOTYPE标识 |
| python src/vision_client/export_records.py sim/build/vision-client/service-e2e/records --out <仓库内新CSV> | prototype-export.txt/exit=0；1条PROTOTYPE记录，原JSONL/CSV/preview截图另存 |
| PowerShell执行verify-zip.command.txt | verify-zip.txt/exit=0；139个payload文件及manifest均核对ZIP内容/字节SHA |

依赖已齐全，未安装新依赖。允许本机回环进行既有HTTP门禁，不访问外部服务；构建日志保存工具/OS/Python版本。
首次ZIP校验输出记录包装语法错误保存在verify-zip-first-recording-failed.txt（exit=1），随后用ScriptBlock执行原校验命令并成功留痕，未据首轮命令退出1宣称通过。

## 候选包与指纹

完整候选目录：sim/build/nc-offboard-release-20261014/，含EXE完整_internal、合成FP32回放样例、使用README及三份执行文档。
ZIP：sim/build/nc-offboard-release-20261014.zip，78,183,698 bytes，SHA256见candidate-package.json；文件清单与SHA见package-manifest.json，构建源码/资源/tb指纹见build-input-sha256.json。
复验ZIP：`& ([ScriptBlock]::Create((Get-Content -Raw data/logs/2026-10-14-nc-offboard-closeout/verify-zip.command.txt)))`；不创建工作区外临时文件。
原exe指纹保存在previous-exe-sha256.json；本轮从当前源码重建。完整复制包自测不等于独立无开发环境目标机、真实UVC/网络/板卡或最终发布验收。

## 文档交付与边界

[工作板](../../../docs/nc-offboard-workboard-2026-10-14.md)、[采集准备](../../../docs/nc-collection-preflight.md)、[25例工业/故障及指标口径](../../../docs/nc-industrial-acceptance-v0.md)、[发布/演示/提交](../../../docs/nc-release-demo-preflight.md)；现场用例均保持未测。
两张新渲染图已目视核对，未把合成目标/FP32原型当真实识别。正式模型/CNN存储/MMIO/DMA/核工业固件/真实LIVE未实现或未接入；Q5修复/JL一致与完整实机验收仍待完成。
前序文档字节保持检查见prior-documents-check.txt；新Markdown链接/空白及git diff --check见document-check.txt和diff-check.txt/exit文件；不重复无关RTL全量回归。
