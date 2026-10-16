# C01 停机期粘滞错误位：含桩覆盖（第 1 步，2026-10-15）

基线 `dev/model@891cba2`。本步只动测试与门禁清单；**N03 冻结三件套逐字节未变**（见 `input-hashes.txt`）。

## 这一步解决什么

板端 2026-10-12 首次实验以 `CaptureError('DMA reset/clear not clean')` 失败，记录 `sr=0x14811`
（[onboard-first.txt](../2026-10-13-ddr-single-frame/onboard-first.txt)）。被驱动判据 `ERRORS|IRQ`
覆盖的粘滞位恰好是 **0x4810**（Err_Irq | bit11 | DMAIntErr）。

修复方案是"先配置非零几何、再清粘滞错误"（改动见 `src/pynq_host/c01_capture.py:118-125` 的注释与顺序），
但第二次实验在 DMA 启动前就因 NOVIDEO 停止，**这条修复从未上板复测**；
而当时的桩不模拟"停机期错误位反复出现"，所以该修复此前**没有任何离线覆盖**。

## 本步改动

| 文件 | 改动 | 说明 |
|---|---:|---|
| `sim/vision/test_c01_capture.py` | +39 / −2 | 桩新增停机期粘滞模型（`IDLE_FAULTS=0x4810`）+ 两组用例 |
| `sim/vision/test_c01_capture_ordering.py` | 新增 52 行 | 变异检验：把驱动顺序改回旧顺序，套件必须以板端原报错失败 |
| `sim/scripts/run_vision_python.sh` | 清单 +1 | 门禁新增 `c01_capture_ordering` |

## 判据

1. **记录到的错误位模式**在几何配置后必须可见（`configured_idle`）、被 WD1C 掩码覆盖（`ERRORS|IRQ|0x2000`）、
   并在 RUN 前清到 0 —— 把"先配几何再清错误"这条未复测修复钉在含桩上（`test_recorded_idle_faults_reach_clean_state_after_geometry`）。
2. **错误位持续复现**（真实源故障）时必须拒绝启动：不写 RUN、不 invalidate/不复制、四缓冲各释放一次、
   不被隔离（`may_write=False`）、证据保留 `configured_idle`/`cleared_idle`（`test_persistent_idle_faults_refuse_run_before_start`）。
3. **测试要有牙**：旧顺序（先清后配几何）必须让套件失败，且失败串与板端一致 —— 变异检验独立证明第 1 条不是空断言。

## 原始结果

| 记录 | 内容 |
|---|---|
| `tests-after.txt` | 9 组 OK，`EXIT=0` |
| `mutant-check.txt` | `PASS`，`EXIT=0`；旧顺序下套件报 `DMA configured idle reset/clear not clean` |
| `vision-gate.txt` / `vision-gate.exit.txt` | 视觉 Python 门禁全绿，`GATE_EXIT=0` |
| `git-diff-check.txt` | 无输出，`EXIT=0` |
| `input-hashes.txt` | 冻结三件套与 2026-10-14 `runner-inputs.json` 逐字节一致 |
| `pre-change-test-file.txt` | 改动前的测试文件快照，SHA `b60b592c…`（= 10-14 复核输入记录值） |

复现命令：

```bash
python sim/vision/test_c01_capture.py
python sim/vision/test_c01_capture_ordering.py
bash sim/scripts/run_vision_python.sh
```

## 漂移声明

`sim/vision/test_c01_capture.py` 是 2026-10-14 记录的 12 份复核输入之一（原 SHA `b60b592c…`）。
本步修改后 SHA 变为 `f2804d98…`，成为继两个包装脚本之后的第 3 项漂移；
**冻结三件套（`runner-inputs.json`）未动**，返板包不受影响。

## 边界

- 入口 main 的端到端替身（PNG 写失败/回读不一致、UNSAFE-STOP 保活、NOVIDEO 重试、模式守卫）
  已在 `../2026-10-15-c01-entry-surrogate-step2/` 完成（11 组）。
- 桩模拟的是**记录到的位模式**，不是 VDMA 硬件语义；实机行为仍须 NC 返板复测。
- 未提交、未上板；`sim/coprocessor/` 的改动属于另一会话，本步未涉。
