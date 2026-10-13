# CNN 整数计算链离板证据（2026-10-13）

基线 `3e2e1c9`，分支 `dev/model`，新增未提交。用户指定先 CNN MAC，明确快速模式、理解题最后做；最新要求只推进离板事项。

## 当前结论

实现标量/8×16 阵列、分拍乘法与加法树、bias/ReLU/requant、GAP、FC、卷积寻址与固定四 Conv→GAP→FC 控制器。整数软件参考包含模型校验和完整诊断逐层黄金。**诊断权重未经训练；实体 BRAM、C03 MMIO/DMA、核接入、正式模型和板端输出未实现/验收。**

完整仓库回归 `bash sim/scripts/run_iverilog.sh all` **PASS，退出0**：`rtl-full-final.txt`、`rtl-full-final.exit.txt`。包含CNN算子/两组整网、四组协处理器Python、原核与四档CoreMark、25个视觉RTL和15组视觉Python。最终DDR七组也在该入口通过。日志里的候选加载/恢复STAGE来自离板fake回调，本轮没有设备下载或串口操作。
最终[汇总](final-summary.json)记录原始日志SHA、两组整网各1,123,109拍和65文件复核。四档CoreMark CPI=1.885683/1.693399/1.616360/1.606121，与原基线一致。`git diff --check`与cached检查均无输出、退出0，原始空输出/退出文件保留。

## 独立验证与综合

| 记录 | 结果 |
| --- | --- |
| `rtl-arithmetic-golden.txt` | 五个组合算子通过；MAC 65,035、阵列4,272、requant8,075、GAP32,515、logits2,814向量 |
| `pipeline-boundaries.txt` | 4,272 MAC lane与8,075 requant黄金通过；持续输入/暂停/取消 |
| `conv-address-pipeline.txt` | 所有固定层、CI1/CO17尾通道、padding以及错误/溢出/复位/超时恢复 PASS，退出0 |
| `python-all-final.txt` | 四组 Python，独立常量整网黄金、参数/范围与INT32累加界拒绝门 PASS，退出0 |
| `ooc-wrapper-final.txt` | 一键 OOC setup/hold、DSP、严重DRC门 PASS，退出0 |

最终 OOC 原始报告在[完整目录](../cnn-ooc-5c9bc74c61e7445ca8c56b2f49389102/)。Vivado2026.1、xc7z020clg400-1、10 ns 时钟、输入/输出1 ns假设：WNS **+0.058 ns**、WHS **+0.049 ns**、DSP **192/220**、LUT **10,100**、FF **6,940**、BRAM **0**、严重DRC0。源码与执行Tcl/入口均存档，manifest 有 SHA256。

OOC未包含实体存储、视频与SoC；存在未指定 `HD.CLK_SRC` 和 `HD.PARTPIN_LOCS` 的OOC边界警告，外部端口路径/时钟偏斜仍是估计。裕量很小，不能代替整机100 MHz时序或板端性能验收。

## 失败与中间结果保留

- `conv-operators.txt`：初次 cases.txt CRLF 导致文件名含 CR；退出1。修正为LF后 `conv-operators-lf.txt` 通过。
- `ooc-baseline/`：初始组合实现 WNS=-19.892 ns；脚本错误使用不支持的redirect，退出1，报告保留。
- `ooc-pipeline/`：拆运算后 WNS=-5.271 ns、194 DSP，时序门失败；精确输入见[快照](../../evidence/2026-10-13-cnn-pipeline-ooc-inputs/)。
- `ooc-address/`：地址分拍后 WNS=+0.058 ns、192 DSP，退出0；随后用存档Tcl的一键入口复核setup/hold/资源门。
- `python-all.txt`：新增测试误将类型错误期待为值错误；保留失败，修正期望后 `python-all-final.txt` 通过。
- `rtl-pipeline-all.txt`：上一轮运行只留到pattern与恢复PASS、没有配对完成退出码，不当作全量PASS证据。

当前代码与两组诊断黄金65文件已[最终归档](../../evidence/cnn-ddr-offline-0635d33e8e274f88a88cd2a6a90464b2/manifest.json)，文件/源码哈希均复核；前一快照保留，差异仅DDR追溯字段及其断言，CNN运算源码未变。整网每个正常输入检查9,225个packed word / 73,795个有效元素，并核对103,432次读和101,384次权重组读，不仅比较argmax。

## 复现入口

```text
bash sim/scripts/run_iverilog.sh coprocessor all
bash sim/scripts/run_coprocessor_python.sh all
bash sim/scripts/run_iverilog.sh all
powershell.exe -NoProfile -File sim/scripts/run_cnn_ooc.ps1
powershell.exe -NoProfile -File sim/scripts/archive_cnn_ddr_offline.ps1
```

需Icarus/MSYS2、NumPy及Vivado；Windows可用 `VISION_PYTHON` / `COPROCESSOR_PYTHON` 指定真实解释器。
MAC发射工作量101,384不等于实际控制器总周期；仿真周期另含读/寻址/流水等待和TB的1/7停顿，不作为板端延迟。理解确认前不commit/push。
