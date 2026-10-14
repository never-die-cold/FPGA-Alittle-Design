# C04 NC离板复核证据

2026-10-14，`dev/model@5654eb5`；Python 3.12，完整HEAD见head.txt，被测文件/模型/夹具SHA256见source-input-sha256.json。
范围：Q1/Q3/Q5静态评审及四项仓库既有专项；无生产代码/RTL改动，无串口/UVC/板卡访问。

## 命令与结果

仓库根目录，解释器 `C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe`：

| 命令（python -u） | 本目录输出 | 退出码 |
|---|---|---|
| sim/vision/test_vision_live_service.py | live-service-localhost.txt | 0 |
| sim/vision/test_service_engine.py | service-engine-localhost.txt | 0 |
| sim/vision/test_vision_joint.py | vision-joint-localhost.txt | 0 |
| sim/vision/test_inspection_rules.py | inspection-rules.txt | 0 |

对应*.exit.txt逐项保留。前两项首次沙箱运行WinError 10013，live-service.txt/service-engine.txt及退出码1保留；允许本机回环后重跑。joint日志WARN为损坏报文/断联负例，最终PASS且退出0。
测试输出仅在已核查绝对路径且非链接的仓库sim/build/vision/{service,engine,joint}-test；使用既有合成/FILE夹具，不计入真实数据或硬件验收。
service-excerpts.txt、policy-excerpts.txt、artifact-record-excerpts.txt记录源码行号与上下文；结果对应本轮SHA256，不修改历史证据。
git diff --check结果见diff-check.txt/diff-check.exit.txt；新文档链接核对见document-links.txt。
当前评审结论与未实现清单见[评审单](../../../docs/c04-nc-review-2026-10-14.md)，不据专项PASS代签C04冻结。
后续NC明确确认Q1/Q3及Q5的NC原则，授权与JL对齐；已创建并指派LibJiang的[#75](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/75)请求和返回保存在issue-75.json。JL一致及修复验收仍待完成。
