# ARM 文件定位/裁剪：最终交付与实测

日期：2026-10-03；开发起点 8a2384c，三题已通过，本次按功能与证据拆分提交。
文件运行器、PGM/hex、独立便携包和三场景 ARM 基线全部完成。
五项 Python 回归通过；PC/ARM 三场景 15 个采样的框、像素、导出文件与哈希完全一致。

## ARM 实测

Linux / armv7l（32 位 ARM）/ Python 3.10.4。每场景预热一次、采样五次，输出 64×64，单位 ms。

| 场景 | 定位中位数 | 裁剪中位数 | total_call 中位数 | total_call p95 |
|:---|---:|---:|---:|---:|
| 12×8 双目标 | 1.260 | 262.419 | 410.329 | 427.138 |
| 720p 空场景 | 4209.353 | 0.044 | 6231.567 | 6284.926 |
| 720p 六目标 | 4702.640 | 849.070 | 7894.935 | 7963.697 |

空场景 crop 是分支开销。720p 六目标中位数约 7.895 s，当前纯 Python 参考不能承诺实时处理。

## PC 对照

| 场景 | 定位中位数 ms | 裁剪中位数 ms | total_call 中位数 ms |
|:---|---:|---:|---:|
| 12×8 双目标 | 0.063 | 6.359 | 21.850 |
| 720p 空场景 | 126.617 | 0.007 | 221.854 |
| 720p 六目标 | 127.529 | 20.513 | 269.305 |

## 计时与限制

- locate/crop 仅覆盖计算；total_call 另含输入读取、验证、图片导出及 JSON 发布。
- 进程启动、组包、SSH、图案生成、显示及相机/采集卡延迟均不计入。
- p95 用最近秩；五样本 p95 等于 max，不表示长期稳定性。
- 合成场景不能替代真实紧固件精度与实际相机条件。
- 板端墙钟实测为 2026-09-21，未同步；报告采用会话日期，耗时采用单调钟。
- 精确验收源版本以 final-package-manifest.json 的逐文件 SHA256 为准；其中 base_commit 是开发起点，不表示这些新增文件已经存在于该 commit。

## 交付入口

- 包：data/evidence/2026-10-03-arm-localize-baseline/arm-localize-package.tar.gz。
- 操作：docs/arm-localize-runbook.md；集中讲解/三题：docs/arm-localize-walkthrough.md。
- PC 样本：data/evidence/2026-10-03-arm-localize-baseline/pc-benchmark/summary.json 及引用目录。
- ARM 样本：data/evidence/2026-10-03-arm-localize-baseline/arm-board-final/arm_localize/benchmark/summary.json 及引用目录。
- 最终板端目录：/home/xilinx/arm_localize_final_v3/arm_localize。
- 完整归档：data/evidence/2026-10-03-arm-localize-baseline/arm-results-final.tar.gz。

PC/ARM 包清单 SHA256 相同：4cb56d8dae28bd01701f789f893b611a34b9234e619b572906d70b86e873b842。
便携包 SHA256：5e5b7373342b5a1592b7d30f72e368beeeb5d295f3f6d641c0d1455c1e8a05c8。
板端归档 SHA256：334e83722faff96bf71428b512410f8fbccc82d2a0d09ad51d4e476c34fd4a0a。

## 复现与原始结果

运行 bash sim/scripts/run_iverilog.sh vision_python。
对比：python sim/vision/compare_arm_localize_bench.py data/evidence/2026-10-03-arm-localize-baseline/pc-benchmark data/evidence/2026-10-03-arm-localize-baseline/arm-board-final/arm_localize/benchmark。

    PASS: portable package hashes, exact localization/crops and PGM/hex
    PASS: synthetic benchmark 3 cases, warmup=1, repeats=5
    PASS: PC/ARM benchmark 3 cases, 15 samples, exact boxes/pixels/PGM/hex/hashes

日志：final-python-regression.log、final-arm-benchmark.log、final-benchmark-compare.log、final-arm-pc-compare.log。
修复前日志保留为 attempt 文件；最终结论只引用最终包与 final 数据。

## 未实现 / 未接入

实时 HDMI/PL 读取、真实相机识别、正式模型、CNN 协处理器和工业检查服务未实现/未接入。
本轮没有修改 JL 的核、视觉 RTL 或板上 Overlay。最终集中三题已通过；用户已授权多个 commit 提交。
