# [2026-10-27] 协处理器合并回归与 A/B 变体收口

> 分支 `dev/riscv`；本地不 push；本轮未运行 Vivado，当前源码的综合/时序/板级均
> **UNVERIFIED**。

## 1. 合并与 RTL 影响

- `87cba27` 完成 origin 合并；唯一冲突 `tools/cop_payload_loader.py` 同时保留 direct 精确
  40 MHz/首次 STATUS 守卫，以及 HWH MMCM 输入时钟方案。
- `cop_axi_lite_cdc.v` 的 AXI 控制 toggle/ack 从两级改为三级，载荷仍两级；
  `w_ack/r_ack/w_active/r_active` 在首个 always 前，四个 hold 有显式复位。
- `cop_task_ctrl.v` 新增 `COMMIT_RESULT`：每个非末目标增加一拍，N 目标整轮净增 N−1 拍；
  三目标夹具从 18 拍变为实测 20 拍，现有 TB 已固定精确断言。
- 视频集成变更文件完整清单见 `docs/coprocessor-build-variants.md`；A 默认不装视频源，
  B 仅在 `COP_WITH_VIDEO=1` 时装入。

## 2. 回归证据

首次裸命令 `bash sim/scripts/run_coprocessor_iverilog.sh all` 退出 1：系统 `python3`
缺 `numpy`，失败发生在网络向量生成，不是 RTL/TB 红项。可复现环境命令：

```bash
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh all
COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python \
  bash sim/scripts/run_coprocessor_iverilog.sh bram_network
bash sim/scripts/run_iverilog.sh cop_multitarget_commit
```

三条依次退出 0；关键 PASS：

- `PASS: firmware_e2e delayed CFG/model/ROI; two CPU jobs + PS CONSUME without reset; no duplicate configuration`
- `PASS: three distinct ROI results committed once in matching slots 0/1/2 cycles=20`
- `PASS: cnn_sequencer .../zero all 9225 packed words/73795 elements match integer network`

| 模式 | 旧期望 | 新实测 | 差异原因 |
|:---|:---|:---|:---|
| `all` / network pattern | 472593 | 472593 | 无变化 |
| `all` / network zero | 472593 | 472593 | 无变化 |
| `all` / payload_network zero | 472594 | 472594 | 无变化 |
| `bram_network` pattern | 472594 | 472594 | 无变化 |
| `bram_network` zero | 472594 | 472594 | 无变化 |
| 三目标 task control | 18 | 20 | 两个非末目标各经过 1 拍 `COMMIT_RESULT` |

单目标 `result_cycles` 来自 CNN sequencer，故不包含任务控制提交隔离拍；没有修改 J02
`EXPECTED_OUTPUTS.tsv`，没有删除/放宽断言或跳过模式。

## 3. CDC 与门禁准备

合入的 routed 报告仍为 CDC-3=12、CDC-6=7、CDC-15=73。三级同步改变 CDC-3 报告中的
同步深度（AXI req/ack 为 3），跨域起点仍落第一阶段，路径与数量均未变化，因此没有新增条目、
没有扩大上限；只修正 `single_sync` 的理由文字。门禁仍要求路径正则、ID/Severity、分项上限和
ID 总上限同时命中，解析失败保持 fail-closed。

## 4. 变体与包状态

- A：不设置 `COP_WITH_VIDEO`，只含核+协处理器，等待 JL Windows 门禁后用于 NC 首包。
- B：`COP_WITH_VIDEO=1`，加入 HDMI/视觉/VDMA/HP1，是 J07 实验变体；所有结果 UNVERIFIED，
  bit/hwh/xsa 不得混入 A 包。
- `f856d5861db0`、`759744b99891`、`5653d5911b76` 均因 RTL 合并作废；旧目录保留，不删除。
- `COP_BUILD_NAME` 每次必须是全新名称；不得删除旧目录后复用名称回放旧报告。

## 5. JL 下一条命令

```powershell
$env:COP_PYTHON="C:\Microsoft VS Code\anaconda\python.exe"
$env:COP_BUILD_NAME="pynq_cop_a_20261027_r1"
Remove-Item Env:COP_WITH_VIDEO -ErrorAction SilentlyContinue
& "D:\vivado\2026.1\Vivado\bin\vivado.bat" -mode batch `
  -source build\build_pynq_cop_gate.tcl
```

门禁 PASS 后才允许重打 A 包；本检查点不预填 WNS/DSP/BRAM/CDC/DRC 数字。
