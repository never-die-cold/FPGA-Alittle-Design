# 最终离板检查

当前产品状态以[主计划](../../plan.md)为准，审查原始问题见[完整审查](../../data/logs/2026-11-03-offboard-audit/AUDIT.md)，修复结果见[处置清单](../../data/logs/2026-11-03-offboard-fixes/RESOLUTION.md)。最终技术文档与海报由队友在其本地完成，仓库旧稿不作为其成品验收依据。

## 环境与入口

从仓库根目录运行。Python需已有视觉/训练依赖（NumPy、OpenCV、torch、paramiko），网页测试需Node.js；使用`VISION_PYTHON`指定解释器。纯软件模式不访问板卡，也不重跑RTL：

```bash
bash sim/scripts/run_offboard.sh software
```

完整模式额外需要iverilog/vvp、MSYS2 make、RISC-V交叉工具链、已获取的arch-test固定版本：

```bash
bash sim/scripts/fetch_arch_test.sh
bash sim/scripts/run_offboard.sh all
```

Windows上完整模式应使用`C:/msys64/usr/bin/bash.exe`，并将`/c/msys64/ucrt64/bin:/usr/bin`置于PATH前部，避免Git Bash自带make与MSYS2环境混用。工具链细节见[arch-test入口](../../sim/scripts/run_arch_test.sh)。日志先写仓库内`sim/build/`，结束后选取归档到`data/logs/`并重建索引；不要让日志在卫生检查期间继续改变被索引目录的大小。用`tee`时启用`set -o pipefail`保留真实退出码。

`all`调用核/视觉/协处理器回归与四档CoreMark，补充v1_flow、BRAM整网、watchdog、板级smoke、arch矩阵；两种模式都执行检查链、独立数据/生命周期测试、网页/服务保护、SSH信任策略、当前r6安全加载、教程解码/退出码、仓库卫生和diff检查。XSim、Vivado综合/时序不在此入口，仍需专项环境。

## 本次证据边界

11/03审查已分开运行四档CoreMark和RTL专项。原始`run_iverilog.sh all`在重复BHT阶段被主动中断，不能写为该命令全程PASS；分项日志和CoreMark结果留在审查目录。本轮未改RTL，软件修复后的运行记录另存修复目录；新增汇总入口的`all`模式尚未整条执行。

原审查`probe-web.mjs`/`probe-codec.py`用于证明修复前缺陷，保留原样；修复后的判据由`sim/vision/test_web_*.mjs`和`sim/tools/test_verify_rv32i.py`承担。审查快照与哈希不随修复覆盖。

## 上板及录像前仍需完成

部署配套新网页与服务，确认启动配置、双页面恢复、暂停检查时断源/恢复、低磁盘503和实际检查错误均撤除旧结果；这些离板替身结果不能冒充实板证据。再按[网页操作](../../src/web_client/README.md)核对UVC、本轮快照、手动记录与CSV。

拍摄固定机位下的一轮正常检查、一次缺件/错料或低置信度复检、断联撤框和CSV导出；保留真实RECHECK和误分类边界。当前连续TASK_ERROR/DMA故障、纸边误检、独立精度与整机长测仍未闭环，视频不得宣称已验收通过。
