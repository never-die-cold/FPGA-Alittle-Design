# 2026-10-10 离板检查验证记录

基线 `dev/exe @ aa23206`；未提交，不使用板卡。实现与复现说明见
[offline-inspection.md](../../../docs/offline-inspection.md)。

| 仓库入口 | 原始日志 | 结果 |
|---|---|---|
| `bash sim/scripts/run_inspection_python.sh` | [inspection-all.log](inspection-all.log)，各组同名日志 | 6 组 PASS，退出 0 |
| `bash sim/scripts/run_vision_python.sh` | [vision-all.log](vision-all.log)，各组同名日志 | 8 组 PASS，退出 0 |
| `powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1` | [exe-build.log](exe-build.log) | 固定依赖打包、MOCK 自测、HTTP 联调 PASS，退出 0 |
| `python sim/vision/test_inspection_viewer.py --exe sim/build/vision-client/dist/vision_preview/vision_preview.exe` | [exe-replay-test.log](exe-replay-test.log) | EXE 回放和冲突选项拒绝 PASS，退出 0 |
| 说明文档的合成图运行命令 | [cli-synthetic.log](cli-synthetic.log) | 3 目标，CHECK_FAIL，处理退出 0 |
| EXE `--replay ... --headless --save ...` | [exe-replay-demo.log](exe-replay-demo.log) | 完整性检查与截图 PASS，退出 0 |

MSYS2 入口需 `/usr/bin` 在 PATH；本机经 `C:/msys64/usr/bin/bash.exe` 调用。
HTTP 测试在允许本地回环网络的环境执行。原八组回归中的 timeout/re-handshake WARN
来自主动断联负例，最终自检 PASS，不省略这些原始输出。

ROI 测试从交付原函数快照取参考，24 组逐像素一致，另含 BGR 通道与 8 个非法输入；
模型测试加载真实 FP32 权重，检查重复推理、元数据和非法输入拒绝；
规则与回放覆盖空场景、缺/多/错料、低分、触边、目标超限、重试、参数冲突和产物篡改。
规则测试的分类器替身明确标注 TEST STUB ONLY；实际推理测试和示例另用真实交付权重。
界面测试覆盖正常/未知数量、离线标记及篡改拒绝，不宣称设备连接或工业识别准确率。

早期单步日志 `roi-before-extraction`、`model-test`、`rules`、`artifacts`、`replay`
保留过程记录；`replay-empty` 仅为开发冒烟，不作为独立验收依据，正式空场景用例已入仓库回放测试。
各主入口的退出码保存在同名 `.exit.txt`；单组 shell 日志由统一入口保存，统一入口执行状态同时检查进程、PASS 和失败文本。
交付 48/48 完整性检查、换行检查分别见 `handoff-integrity.log`、`diff-check.log`。

未实现/未验证清单：真实数据集训练/精度、可信 INT8 导出、PYNQ 延迟、板端取帧、
LIVE 类别服务、CNN 硬件、RISC-V 工单规则、真实工业闭环。
CPU 合成图结果与计时不能替代这些验收。
