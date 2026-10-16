# C01 入口端到端替身（第 2–3 步，2026-10-15）

基线 `dev/model@891cba2` + 各会话未提交改动。本目录只新增测试与门禁清单项，**未改任何生产代码**。

## 解决什么

返板执行单 §3 写明："入口main仅做离板语法检查；现有tb覆盖驱动及helper，完整main/PNG失败/进程保活的
端到端替身覆盖仍缺"。本目录把 `c01_ddr_onboard.py` 的 main 在不接板的情况下**真实执行**：

- `pynq` / `cv2` / `fcntl` / `m2_onboard` / `c01_status_onboard` 全部换成有状态假件；
- `/proc/sys/kernel/random/boot_id` 与 `/home/xilinx/vision_m2` 映射到 `sim/build/vision/python/onboard-fake`；
- 按板端布局把同目录三件套暂存到 `c01-board/`（入口用 `root / 'c01_capture.py'` 算 `driver_sha256`）。

## 覆盖的 11 条路径

| 用例 | 判据 |
|---|---|
| 成功路径 | `ok=True`、`restored=True`、boot 不变、PNG/像素哈希落盘，且 **`result.driver_sha256` == N03 冻结哈希 `1f11aefd…`** |
| PNG 写失败 | `ok=False`、`main_error='PNG write failed'`、仍恢复原 vision、无 `unsafe_stop` |
| PNG 回读不一致 | `ok=False`、`main_error='PNG round-trip mismatch'`、仍恢复 |
| 首次 NOVIDEO → 有界重试 | 第二次 smoke 成功并继续取帧（候选 smoke 2 次 + 恢复期 1 次） |
| 连续两次 NOVIDEO | `SystemExit(3)` 传出、未分配缓冲、未写 RUN、仍恢复原 vision |
| 候选 DMA 已活动 | 拒绝接管，且**不**对未知 owner 恢复覆盖（无 `restore` 事件） |
| 恢复失败 | 取帧成功但 `restore_error` 记录，并以该错误抛出 |
| boot_id 变化 | `RuntimeError('board rebooted during capture')` |
| UNSAFE-STOP | 四缓冲 `frees=0` 全保持、打印 UNSAFE-STOP 并进入保活循环、**不**重载 overlay |
| `C01_CAPTURE_MODE` 非法 | 任何硬件访问前抛 `ValueError` |
| `C01_CAPTURE_MODE=park` | 入口选择 park 驱动并记录 `park_driver_sha256` |

## 原始结果

| 记录 | 结果 |
|---|---|
| `tests-after.txt` | 11 tests OK，`EXIT=0`（约 9.2 s，其中约 6 s 来自 UNSAFE-STOP 的两条真实 3 s 超时） |
| `vision-gate.txt` / `vision-gate.exit.txt` | 视觉 Python 门禁全绿 |
| `git-diff-check.txt` | 一条 CRLF 提示 + `EXIT=0`：仓库 `* text=auto eol=lf`，工作区本就全为 CRLF（未改动的兄弟文件同样如此），该行是提交时归一化的正常提示，不是新增空白错误 |
| `input-hashes.txt` | 本步文件与三件套哈希现状 |

复现：

```bash
python sim/vision/test_c01_ddr_onboard.py
bash sim/scripts/run_vision_python.sh
```

## 漂移与协作声明（重要）

| 文件 | 10-14 记录 | 现在 | 结论 |
|---|---|---|---|
| `src/pynq_host/c01_capture.py` | `1f11aefd…` | `1f11aefd…` | 未变 |
| `sim/scripts/c01_ddr_onboard.py` | `e822a708…` | **`54dd5d64…`** | **被并行快速改进会话修改**（+11 行，新增 `C01_CAPTURE_MODE` 开关） |
| `sim/scripts/c01_status_onboard.py` | `894bf7dc…` | `894bf7dc…` | 未变 |

由此：

1. 本替身测试的是**当前工作区**的入口；我在入口被改后复跑，11/11 通过，默认 `single` 路径行为未变。
2. **返板包的三件套哈希口径已不再自洽**：若返板要按 10-14 已评审的字节执行，必须使用归档快照
   `data/logs/2026-10-14-n03-return-review/inputs/c01_ddr_onboard.py`（仍为 `e822a708…`）；
   否则需在改后重新记录哈希并重做兼容评审。
3. park 模式是并行会话的成果，本目录只覆盖入口的**模式选择与守卫**，不覆盖 park 驱动语义。

## 边界（未做）

未接板；假件不等于 VDMA 硬件语义，实机行为仍待 NC 返板。未覆盖：连续多轮长测、UVC/HDMI OUT 共存、
软件断源恢复、overlay 重载、冷启动。未提交。
