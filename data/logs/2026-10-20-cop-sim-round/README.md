# 2026-10-20 COP_SIM：服务 + EXE 一轮与异常矩阵

> **历史语义**：本目录是 C03 A1/A2（消费握手）之前的实现。现行 submit/consume 语义、
> 两个软件看门狗与证据见 [2026-10-21-cop-a2-round](../2026-10-21-cop-a2-round/README.md)。

> 基线：`dev/exe` @ `fc57cf2` + JL K1/K2 合并 `f540a38`；本轮改动提交见
> `git log -- data/logs/2026-10-20-cop-sim-round`。
> 结论：**模拟跑通 + 软件跑通**。计算后端是 C03 寄存器模型与合成分类器，
> **不是板上跑通，也不是识别精度证据**。板端链路仍等 JL 的固件重复作业/数据面与 NC 的实机。

本目录的 PNG 均由 `sim/scripts/run_cop_sim_round.sh` / 测试重建：`run/screen.png` 为 1600×900
EXE 画布（SHA256 见 §3）；`run/service/.../capture.png` 为本轮权威快照（SHA256 `bb9e…`，
与 `capture.sha256` 一致）；`run/records/screenshots/proto_*.png` 为 EXE 记录截图；
其余为异常矩阵的 trace/失败轮证据。`anomalies/` 与 `engine-matrix/` 是测试输出的原样副本，
可由 `run_inspection_python.sh` 重新生成。

## 1. 这一轮做了什么

按 C03 §13 的 WC 条款，把 PS 侧从“没有驱动”接到“可替换数据面”：

| 件 | 文件 | 作用 |
|---|---|---|
| 寄存器契约常量 | `src/pynq_host/cop_regs.py` | C03 §4 offset/STATUS/CTRL、`cop_judge` 镜像、`FW_DECISION` 编解码 |
| 模拟硬件 | `src/pynq_host/cop_mmio_sim.py` | 配置原子提交、busy 拒 commit、sticky/W1C、结果窗、watchdog、ABORT/SOFT_RESET、CRC/短包/旧结果注入 |
| PS 驱动 | `src/pynq_host/cop_driver.py` | 提交、等 DONE/ERROR/TIMEOUT、`RESULT_SEQ` 双读、`FW_DECISION` 复算、PS 判定不得更宽松、同 JOB_ID 去重、恢复重试；正常轮不写 `CTRL` |
| 服务引擎 | `src/pynq_host/cop_engine.py` | 定位 → 共享 ROI → sim INT8 → 驱动 → 规则 → `cop_trace.json` |
| 服务接入 | `src/pynq_host/vision_live_service.py` | `--engine cop-sim`、`/v1/status` 的 `engine`、`trigger_ref` 16 条回放 |
| EXE 异常语义 | `src/vision_client/rounds.py`、`preview.py` | 手动失败立即撤旧 PASS；同 ref 重试；`--image` 静态图联调 |
| 追溯 | `src/pynq_host/round_artifacts.py` | 快照核对新增 `cop_trace.json` 帧/ROI 哈希链 |

接口口径与 JL 待办单独成文：[PS 驱动使用档](../../../docs/contracts/coprocessor-ps-driver-v0.md)。
K1 对齐（并入 `f540a38` 后修正）：正常轮次 PS **不写** `CTRL`，成功 DONE/RESULT_VALID
由固件下一轮 START 前清（C03 §3.2）；`PynqMmio` 强制 Address Editor 的 PS base，
不默认核侧 `0x8001_0000`；READY 窗口与“消费后清 DONE”回执两项已登记，待 JL 确认。

## 2. 复现命令（仓库内，原始退出码）

```bash
# 全检查链（19 组；本轮 exit 0）
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_inspection_python.sh

# 单独一轮：服务（COP_SIM）+ EXE 无头，显示/保存/追溯
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_cop_sim_round.sh
```

原始输出：[inspection-gate.log](inspection-gate.log)、[inspection-gate.exit](inspection-gate.exit)（0）、
[vision-gate.log](vision-gate.log)、[vision-gate.exit](vision-gate.exit)（0）；
各组日志在 [logs/](logs/)。`cop_service.log` 里有一条 `WARN: check failed (1/3): HTTP Error 503`
是**故意注入 stale 结果**的预期分支，随后重试 PASS；整链退出码为 0。

服务 CLI 入口另行冒烟（独立进程，非只测 `make_server`）：
[cli-smoke-client.log](logs/cli-smoke-client.log) 显示 `STATUS COP_SIM True`、
`CHECK CHECK_PASS 3 {'bolt': 1, 'nut': 1, 'washer': 1}`，退出码 0；
启动行见 [cli-smoke-service.log](logs/cli-smoke-service.log)。

## 3. 一轮结果

[run/summary.json](run/summary.json)：

| 项 | 值 |
|---|---|
| session | `2daf0ed0-5283-40cf-af25-d85b0280e591` |
| check | 1（手动轮） |
| status | `CHECK_PASS`，actual/expected = 1/1/1，reasons=[] |
| targets | 3（bolt/nut/washer，bbox 与夹具同帧） |
| 硬件序号 | `cfg_seq=1`、`result_seq=1`；`FW_DECISION` verdict=CHECK_PASS、reasons=0 |
| capture SHA256 | `bb9e05f3893353de880d310ecdbfbf603b529407a1c503c17e2213358ff0d73b` |
| 显示截图 | [run/screen.png](run/screen.png)，1600×900，`PROTOTYPE` 徽标 + `CHECK_PASS` + 三目标框；SHA256 `d048c2ebe1803d2730d59249ae495fb5fba15ddf4112df7b2c4e42d4774511eb` |
| 记录 | [run/records/records.jsonl](run/records/records.jsonl)（1 条，`prototype=true`，截图前缀 `proto_`） |
| 追溯 | [run/service/2daf0ed0/check-000001/cop_trace.json](run/service/2daf0ed0/check-000001/cop_trace.json) |

ROI 字节哈希（可直接与 trace 对）：

```text
5facf3f3fc3cb9c9f9084538295bfbd6adc3fba2a4594fad8a230be3d3933b41  cop/roi_000.bin
380c6b13c649f9fab9680eb67ff1e5cbfb9c2441c100873852823a3ef01bf23e  cop/roi_001.bin
46e4e5b3fe2549da0ecfcf8d067ac060b3b8fd132981043eeb66c7c3be875848  cop/roi_002.bin
```

核对链：`capture.png` 字节哈希 == `capture.sha256` → 解码像素哈希 == trace.frame.pixel_sha256
→ trace.decision == packet.json/records 的 decision → 三个 ROI 文件字节哈希 == trace.rois。
`round_artifacts.load_snapshot` 任一处被篡改都会抛 `SnapshotError`（测试已覆盖 ROI 篡改）。

## 4. 异常矩阵（都是离板、可一键复跑）

| 情况 | 注入 | 期望 | 证据 |
|---|---|---|---|
| 配置原子性 / busy 拒 commit | 第二笔 commit 在 BUSY 中 | `CopBusError`，无副作用 | `test_cop_mmio` PASS |
| 超时 | `TIMEOUT_CYCLES=1000` + 每目标延时 | `ERROR+TIMEOUT`、无 RESULT_VALID；驱动清状态后重试成功 | `test_cop_mmio`、`test_cop_driver` PASS |
| ABORT / 空闲 ABORT | CTRL.ABORT | busy 中终止；空闲置 ERROR（OPEN-10）；W1C 可恢复 | `test_cop_mmio` PASS |
| 模型 CRC / 短包 | `crc_mismatch` / `short_payload` | MODEL_VALID=0、配置不应用；重载后成功 | `test_cop_mmio`、`test_cop_driver` PASS |
| 旧结果 | 结果完成但 `RESULT_SEQ` 不递增 | 驱动拒绝（`RESULT_SEQ 2 after 2`），不发布 PASS | `test_cop_driver`、[anomalies/check-000003](anomalies/service/030ec869/check-000003/cop_trace.json) |
| 重复 JOB_ID | 同键不同目标 | `CopProtocolError`，不重复发布 | `test_cop_driver` PASS |
| 重复请求 | 同 `trigger_ref` 两次 POST | 同 check_id/frame_id/created_at，只一个轮次目录 | `test_cop_service` PASS；[check-000002](anomalies/service/030ec869/check-000002/packet.json) |
| 运行失败 | stale 结果 | 服务 503、无 packet.json、写失败 trace；EXE 立即撤旧 PASS | [check-000003](anomalies/service/030ec869/check-000003/cop_trace.json)（无 packet.json） |
| 失败后重试 | 清除故障，同 ref 再 POST | 新 check_id 正常 PASS，只记一条 | [check-000004](anomalies/service/030ec869/check-000004/packet.json)、[records](anomalies/records/records.jsonl) |
| 边界/低置信/目标错误/超 10/空场景 | 引擎矩阵 | border/低置信/错误→RECHECK；>10→target_limit；空→PS 本地 CHECK_FAIL | [engine-matrix/](engine-matrix/)、`test_cop_engine` PASS |

UI 约束的落点：`RemoteRounds._state` 在 `manual_failed` 时返回 `error`，`overlay` 返回
`WAITING`，`preview.endpoint_state` 显示红色 `NO VALID RESULT | check failed`——旧 PASS
不会继续挂在画面上；只有新成功轮才会重新进入 `ok`。服务侧失败不会生成 `packet.json`，
EXE 也没有可采纳的新报文。

## 5. 三件事（按交接口径）

**做成了什么**

- PS↔JL 的提交/完成/取结果/恢复口径写成可执行文档，并有与 C03 逐条对应的驱动；
- 模拟硬件覆盖 C03 §4 的状态机与 J04 固件流程，故障可注入；
- 服务与 EXE 完成一轮：显示（截图）、保存（records + 截图）、追溯（capture→packet→trace→ROI 哈希链）；
- 超时、重复请求、旧结果、运行失败都有测试和“绝不显示成 PASS”的断言。

**拿什么证明**

- `run_inspection_python.sh` 19 组、exit 0（原始日志与退出码在本目录）；
- 上面的一轮 summary/截图/记录/trace 与 ROI 哈希；
- 异常矩阵的失败 trace 与重试记录（本目录 `anomalies/`、`engine-matrix/`）。

**还差什么、谁接手**

- **JL（阻断）**：固件目前只跑一次作业，需按新 `CFG_APPLIED` 循环；预启动判定的
  完成通知（count 0/>16/>10、wait_ready 失败）没有 DONE/RESULT_VALID，PS 无法区分
  “没跑”和“已判 RECHECK”；`FW_DECISION` 布局、`touch_border`、描述符 flags 位仍需冻结。
  详见 [PS 驱动使用档 §6](../../../docs/contracts/coprocessor-ps-driver-v0.md)。
- **JL/J08**：物理 bank/结果 DMA/真实地址与 `WEIGHT_CRC32` payload；当前 `PynqDmaPlane`
  故意未实现，不能假装已接。
- **NC**：整机 bitstream/上板、真实 HDMI 输入、板端服务与 EXE 联调；本轮全部是离板。
- **JL J05/J06**：正式 INT8 模型与 manifest（`S_input`）；当前 sim 用 `S_input=1/127`
  和脚本/图像派生分类器，不能写成识别精度。

## 6. 边界（必须一起读）

- 这是 **模拟跑通**（寄存器模型 + 合成计算）和 **软件跑通**（服务/EXE/记录/追溯）；
  **不是板上跑通**。`prototype=true` 是必须的，不能关。
- `cop_mmio_sim.py` 的 `VERSION/CAPABILITY/ERROR_CODE` 按 J04 读 0（OPEN-9）；
  sim-only 的错误名、描述符 flag 位、`S_input` 都不是冻结契约。
- `--image` 用夹具静态图驱动 EXE，证明的是软件链路；真实 UVC/HDMI 帧率与对齐仍待板端。
- 模拟硬件的“通过”不改变 J04b/J08 状态，也不替代 C03 §11.2 的板级验收。
