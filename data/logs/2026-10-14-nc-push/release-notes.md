# NC离板候选包（2026-10-14）

当前源码的Windows便携候选；恒标FILE/PROTOTYPE，不代表正式模型、硬件识别或M2/M3验收。
包含完整EXE/_internal、合成FP32回放样例、运行README及采集/工业/发布执行件。解压后保留目录结构。

- 计算与应用源码基线：5654eb5；本轮交付文档/证据提交：eeff74f302367f5063dd1d790222f84eeffc1884。
- ZIP：nc-offboard-release-20261014.zip，78,183,698 bytes。
- SHA256：AED1205E470C0CAC2B819D758BBB05B2131A0858D439EF53165AB812AB7F0393。
- 已通过：既有打包门禁、清除Python环境变量后的完整目录自测/FILE回放、PROTOTYPE记录导出、139个payload文件及manifest的ZIP指纹核对。
- 待完成：独立无开发环境目标机、完整custom DDR实机、正式模型/CNN集成/核工业固件/真实LIVE及工业验收；Q5交GitHub #75与JL对齐并修复后验收。

运行：`vision_preview/vision_preview.exe --selftest`；回放：`vision_preview/vision_preview.exe --replay replay-example/result.json --headless --save replay.png`。
上板续工：[N03执行单](https://github.com/never-die-cold/FPGA-Alittle-Design/blob/eeff74f302367f5063dd1d790222f84eeffc1884/docs/n03-custom-return-runbook-2026-10-14.md)。
