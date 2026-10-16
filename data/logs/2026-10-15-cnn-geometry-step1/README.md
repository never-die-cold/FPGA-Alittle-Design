# CNN 输出尺寸位宽优化：第 1 步（2026-10-15）

基线 `dev/model@891cba2`，本步未提交。只修改 `conv_engine.output_size` 的算术位宽，
不修改算子接口、存储延迟、状态机或重量化并行度。

## 设计与测试

- 原有 32 位有符号 integer 计算改为 8 位无符号 span，stride=2 用逻辑右移。
- 启动处保留 `size+2*padding<kernel` 和输出大于 64 的拒绝条件；无符号减法不能替代前者。
- 既有 `tb_conv_engine` 增加 528 组真实 start 检查：宽 0…65、高 65-width、
  kernel=1/3、stride=1/2、padding=0/1。期望值独立采用 integer 除法计算。
- 验证启动接受/拒绝、锁存的宽高，以及配置阶段没有存储访问或写入；每组之后复位。
- 既有 `coprocessor conv` 和 `all` 入口自动执行，无需新增脚本分支。

## 原始记录

- `conv-baseline.txt` / `.exit.txt`：新 tb + 原 RTL，六组卷积/FC 与 528 组边界 PASS，退出 0。
- `baseline-ooc-input-check.json`：改 RTL 前，九个 CNN RTL 与历史 OOC 输入逐文件 SHA256 一致。
- `verification-inputs.json`：本步修改后的源码、tb 和入口脚本 SHA256。
- `rtl-all-after.txt` / `.exit.txt`：优化后的全量回归 PASS，退出 0；含六组卷积/FC、
  528 组尺寸边界、两组整网及恢复、九组 CNN Python、四档 benchmark/CoreMark、视觉 RTL/Python。
  CoreMark 四档周期为 19,057,438 / 17,114,141 / 16,335,562 / 16,232,079，与原基线一致。
- `ooc-wrapper-host.txt` / `.exit.txt`：正常用户环境 OOC PASS，退出 0；报告与精确 RTL/Tcl
  快照在 `../cnn-ooc-da63cadcd3db4a9e9f826cf2e4949e68/`。
- `conv-cycle-comparison.txt`：六组卷积/FC 的逐元素结果、读写次数及周期数与基线逐行一致。
- `iverilog-version-msys.txt` / `.exit.txt`：Icarus Verilog 13.0 stable，退出 0。
- `git-diff-check.txt` / `.exit.txt`：无输出，退出 0；`source-stability-check.txt` 核对输入未变。
- 首次 MSYS PATH 配置失败见 `conv-before.txt` / `.exit.txt`；无仿真执行。
- 沙箱内 Vivado 启动因许可证环境失败，见 `ooc-wrapper.txt` / `.exit.txt`，退出 42；
  输入及原始失败保留于 `../cnn-ooc-106904d01e0045089b9d1688ddce6e85/`。

## 复现

```text
bash sim/scripts/run_iverilog.sh coprocessor conv
bash sim/scripts/run_iverilog.sh all
powershell.exe -NoProfile -File sim/scripts/run_cnn_ooc.ps1
```

Windows 使用 MSYS2 Bash，PATH 优先 `/ucrt64/bin:/usr/bin`；全量回归使用
`VISION_PYTHON` / `COPROCESSOR_PYTHON` 指定已有 Python 3.12.10（NumPy 2.5.1、OpenCV 5.0.0）。
所有 tb、向量、日志和构建产物位于仓库内。本步证据目录的局部 `.gitattributes`
保留输入快照与原始日志字节，防止 Windows/Git 行尾转换破坏 SHA256。

## OOC 实测与边界

相同 Vivado 2026.1、xc7z020clg400-1、10ns 时钟及 1ns 输入/输出延迟假设：

| 指标 | 历史原 RTL OOC | 本步 OOC |
| --- | ---: | ---: |
| WNS / ns | +0.058 | +0.118 |
| WHS / ns | +0.049 | +0.051 |
| LUT | 10,100 | 9,955 |
| FF | 6,940 | 6,940 |
| DSP | 192 | 192 |
| BRAM | 0 | 0 |
| 严重 DRC | 0 | 0 |

最差路径由 layer→输出尺寸校验转为 limit→accumulators CE，12 级逻辑、6 个 CARRY4。
本次单点 WNS 改善 0.060ns、LUT 减少 145；不外推为整机主频、板端性能或所有实现种子的保证。
OOC 未包含实体存储或 SoC，192 DSP 也尚未满足全芯片至少 20% 余量的目标。
超时比较、参数缓存、重量化复用、C01 驱动修复尚未实施；实体 BRAM、MMIO/DMA、
核工业固件及整机硬件 LIVE 仍未实现/未接入。理解确认前不 commit。

当前代码/tb 为 42 行新增、3 行删除，共 45 行增删。先交付专项/OOC 时全量仍在运行；
本次恢复已读取最终退出码 0。用户三题回答通过，完整答案与判定存于对应 llm_log；未 commit。
