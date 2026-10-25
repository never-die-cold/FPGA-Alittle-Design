# 2026-10-21 COP_SIM A1/A2：消费握手、一轮与异常矩阵

> 基线：`dev/exe` @ `fbf8ad3` + JL `origin/dev/riscv` `4a57ef4`（合并 `17427ce`）。
> 结论：**模拟跑通 + 软件跑通**，不是板上跑通，也不是识别精度证据。
> 计算后端仍是 C03 寄存器模型与脚本/图像派生分类器；`prototype=true`。

## 1. 这一轮对齐了什么（C03 §14 A1/A2）

JL 把上轮两项待确认正式裁决，并同步改了固件/RTL/K1：

- **A1 READY**：`READY = !BUSY`，只是建议性诊断；PS 不等待、不作失败判据。
  配置回执只认 `CFG_APPLIED`，命令受理认 sticky `ACCEPTED[11]`。
- **A2 消费**：`CTRL[6]=CONSUME`（PS 独占）；`STATUS[12]=UNCONSUMED=DONE|ERROR|TIMEOUT`；
  终态互斥（TIMEOUT>ERROR>DONE，TIMEOUT 不再置 ERROR）；一笔 CONSUME 原子清
  `DONE/ERROR/TIMEOUT/RESULT_VALID/ACCEPTED/ERROR_CODE`，不清 `RESULT_SEQ`。
- **两个 PS 软件看门狗**：等 ACCEPTED 超时 = `NO_ACK`；已 ACCEPTED 等终态超时 =
  `HW_TIMEOUT`，不依赖硬件 timeout 位。
- **落盘后消费**：`读结果→校验→持久化成功→CONSUME`；落盘失败禁止清灯。
- **序号**：每轮成功结果 `RESULT_SEQ` 单调 +1；CONSUME/软复位不回退；PS 必须校验
  `expected = last_consumed + 1`。

WC 侧改动：`cop_regs.py`（新位/错误码）、`cop_mmio_sim.py`（ACCEPTED/UNCONSUMED/CONSUME/
互斥终态/NO_ACK/HW_TIMEOUT 故障）、`cop_driver.py`（ACCEPTED 等待、两个看门狗、CONSUME、
期望序号、旧终态 **STALE_RESULT**）、`cop_engine.py`（服务落盘后 `consume()`，trace 记录
consume 状态）、`vision_live_service.py`（packet/latest 落盘后调用 `engine.consume()`）。
接口口径：[PS 驱动使用档](../../../docs/contracts/coprocessor-ps-driver-v0.md)。

## 2. 复现

```bash
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_inspection_python.sh
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_vision_python.sh
VISION_PYTHON=sim/build/vision-venv/Scripts/python.exe bash sim/scripts/run_cop_sim_round.sh data/logs/2026-10-21-cop-a2-round/run

# JL 的 A1/A2 RTL（不依赖 host gcc）
export PATH=/ucrt64/bin:/usr/bin:$PATH
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh decision_ab
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh cop_top
COPROCESSOR_PYTHON=sim/build/vision-venv/Scripts/python.exe RISCV_CROSS=riscv32-unknown-elf- \
  bash sim/scripts/run_coprocessor_iverilog.sh bram_network
```

结果：

| 入口 | 退出码 | 关键输出 |
|---|---:|---|
| `run_inspection_python.sh` | 0 | 19 组 PASS；[inspection-gate.log](inspection-gate.log) |
| `run_vision_python.sh` | 0 | 21 组 PASS；[vision-gate.log](vision-gate.log) |
| `decision_ab` | 0 | T1–T7 PASS；[rtl/decision_ab.log](rtl/decision_ab.log) |
| `cop_top` | 0 | AXI/J02/DMA error/ABORT/SOFT_RESET/CFG_VALID PASS；[rtl/cop_top.log](rtl/cop_top.log) |
| `bram_network` | 0 | pattern/zero 各 73,795 元素匹配；cycles=472594；[rtl/bram_network.log](rtl/bram_network.log) |
| `firmware` | 环境失败 | RISC-V ELF 构建成功，但主机规则测试需要 `gcc`；本机 MSYS 无 host gcc，**未声称该入口 PASS** |

JL 的 A2 改了 `src/riscv_fw/cop_job.c`，但 `cop_job.hex/dis` 仍是旧固件（`50838e3`）产物；
上述 RTL TB 不加载该 hex，整机固件镜像需 JL 在交付时重建。

## 3. 一轮结果

[run/summary.json](run/summary.json)：

| 项 | 值 |
|---|---|
| session | `76d4d652-1769-4ee2-a2fc-b4a130b34c20` |
| check | 1（手动轮） |
| status | `CHECK_PASS`，actual/expected=1/1/1，reasons=[] |
| targets | 3（bolt/nut/washer，bbox 与夹具同帧） |
| 硬件序号 | `cfg_seq=1`、`result_seq=1`；`ACCEPTED=1`、`UNCONSUMED=1` 在读取时 |
| 消费 | trace.consume：`result_seq=1`、`status_after=97`（READY+CFG_VALID+MODEL_VALID）、`unconsumed=false` |
| capture SHA256 | `bb9e05f3893353de880d310ecdbfbf603b529407a1c503c17e2213358ff0d73b` |
| 显示截图 | [run/screen.png](run/screen.png)，SHA256 `00abd43346f12ba97907dde8fed822b82713c00ea800d7138b632fc13dc070dd` |
| 记录 | [run/records/records.jsonl](run/records/records.jsonl)，1 条，`prototype=true` |
| 追溯 | [run/service/76d4d652/check-000001/cop_trace.json](run/service/76d4d652/check-000001/cop_trace.json) |

ROI 字节哈希：

```text
5facf3f3fc3cb9c9f9084538295bfbd6adc3fba2a4594fad8a230be3d3933b41  cop/roi_000.bin
380c6b13c649f9fab9680eb67ff1e5cbfb9c2441c100873852823a3ef01bf23e  cop/roi_001.bin
46e4e5b3fe2549da0ecfcf8d067ac060b3b8fd132981043eeb66c7c3be875848  cop/roi_002.bin
```

核对链：capture 字节哈希 → trace 帧像素哈希 → trace decision == packet/records →
ROI 字节哈希 → `consume` 记录。`round_artifacts.load_snapshot` 可验证；ROI 篡改被拒。

## 4. 异常矩阵（A2 口径）

| 情况 | 注入/断言 | 证据 |
|---|---|---|
| 正常消费 | 读结果→落盘→CONSUME；ACCEPTED/UNCONSUMED/ERROR_CODE 清零，RESULT_SEQ 保留 | `test_cop_mmio`/`test_cop_driver`；本轮 trace.consume |
| 提交前 UNCONSUMED | 返回 `STALE_RESULT`，不写新命令 | `test_cop_driver` |
| NO_ACK | 服务端看门狗等不到 ACCEPTED；ABORT→消费→503 | `test_cop_driver`（sim `no_ack`） |
| HW_TIMEOUT | 已 ACCEPTED 无终态；ABORT→消费→503 | `test_cop_driver`（sim `hang`） |
| 硬件 TIMEOUT | 只置 TIMEOUT（不置 ERROR），ERROR_CODE=13；读码+CONSUME | `test_cop_mmio`/`driver` |
| ABORT | ERROR_CODE=12；ACCEPTED 保持到 CONSUME | `test_cop_mmio`/`driver` |
| 旧结果 | `RESULT_SEQ 2; expected 3 (last consumed 2)` → 503、无 packet、失败 trace；同 ref 重试成功 | [anomalies/check-000003](anomalies/service/85d38442/check-000003/cop_trace.json) |
| 重复请求 | 同 trigger_ref 同 check_id/frame_id/created_at，只一个轮次目录 | [check-000002](anomalies/service/85d38442/check-000002/packet.json) |
| CRC/短包/描述符 | 配置不应用、ERROR_CODE=1；消费后重载成功 | `test_cop_mmio`/`driver` |
| 重复 JOB_ID | 同键不同目标 → `CopProtocolError`，不重复发布 | `test_cop_driver` |
| 目标错误/低置信/边界/超 10/空场景 | RECHECK / target_limit / PS 本地空帧门 | [engine-matrix/](engine-matrix/) |

UI 约束仍成立：失败轮不产生 packet；`manual_failed` 立即撤旧 PASS；同 ref 重试复用
`trigger_ref`。服务在 packet/latest 落盘成功后才 CONSUME；落盘失败不清灯。

## 5. 三件事（交接）

**做成了什么**

- C03 A1/A2 已落到 PS 模拟硬件/驱动/引擎/服务：ACCEPTED、UNCONSUMED、CONSUME、
  终态互斥、两个软件看门狗、期望序号、落盘后消费；
- 服务+EXE 完成一轮，trace 里能看到 `consume` 之后的干净状态；
- JL 的 A1/A2 RTL（T1–T7、cop_top）与 K3 BRAM 网络回归复跑通过。

**拿什么证明**

- 19 组 inspection + 21 组 vision，exit 0；
- `decision_ab`/`cop_top`/`bram_network` exit 0（原始日志/退出码在 [rtl/](rtl/)）；
- 一轮 summary/截图/records/packet/trace/ROI 哈希 + consume 记录。

**还差什么、谁接手**

- **JL**：固件重复作业循环；预启动判定（count 0/>16/>10）的完成通知；`FW_DECISION`
  布局、`touch_border`、描述符 flags 位冻结；A2 改动后的 `cop_job.hex/dis` 重建；
  J08 物理 bank/结果 DMA/实际地址。`firmware` 主机规则测试需在有 host gcc 的环境复跑。
- **NC**：整机 bitstream、真实 HDMI/UVC、板端服务与 EXE 联调。
- **JL J05/J06**：正式 INT8 模型/manifest（`S_input`）。本轮仍是 sim-only 量化与合成分类器。

## 6. 边界

- **模拟跑通 + 软件跑通**，不是板上跑通；`prototype=true` 不可关。
- `S_input=1/127`、脚本/图像派生分类器不是正式模型/精度证据。
- `cop_top`/`decision_ab`/`bram_network` 是 Icarus 离板回归；BRAM 推断、整机时序、
  位流与板级仍 UNVERIFIED。
- 旧 [2026-10-20 证据](../2026-10-20-cop-sim-round/README.md) 是 A1/A2 之前的语义，
  保留作历史；现行以本目录为准。
