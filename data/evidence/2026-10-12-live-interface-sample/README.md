# LIVE 接口样例（G0 互交件）

2026-10-12 | watercopper（离板应用链）
给 NC（板端正式服务实现对照）与 JL（C03 结果字段衔接）的第一份接口样例。
**全部为合成/离线数据，非板上识别证据**（plan.md §3.4）。

## 文件

| 文件 | 来源 | 说明 |
|:--|:--|:--|
| `packet-check_fail.json` | 打包门禁 `test_vision_service_e2e`（桩引擎场景） | v1.2 LIVE 报文：CHECK_FAIL、3 目标（bolt/nut/washer）、missing 各 1、prototype=true |
| `preview-check_fail.png` | 同一门禁 | EXE 对同类报文的期望显示（1600×900 HUD） |
| `packet-real-engine.json` | `sim/vision/test_service_engine.py`（真引擎：FP32 原型 + 合成夹具） | 实际模型输出报文：CHECK_FAIL、actual 2 bolt / 0 nut / 1 washer |

## 复现

```powershell
powershell -ExecutionPolicy Bypass -File sim\scripts\build_vision_client.ps1 -Python py   # 前两件
py sim\vision\test_service_engine.py                                                      # 第三件
```

打包门禁产物在 `sim/build/vision-client/service-e2e/`；引擎测试产物在 `sim/build/vision/engine-test/`。

## 报文 → 显示映射（实现对照）

| 报文字段 | EXE 期望显示 |
|:--|:--|
| mode=LIVE + prototype=true | 顶栏 `LIVE` + `PROTOTYPE`（红，恒显不可关） |
| status=CHECK_FAIL + decision.missing/extra | 横幅 `CHECK_FAIL -boltx1 -nutx1 -washerx1`（红）；缺/多摘要 |
| decision.actual 合计 / expected 合计 | TARGETS 格 `3/6`（实际/工单） |
| targets[].class / score | 右列对象行 `T0 bolt 0.97`；class=null → unclassified；score 缺 → `--` |
| status=RECHECK（低分/未知类/触边/超限） | 琥珀横幅；超限时计数按报文内目标重算（见 C04 §2.2 注记） |
| 年龄超窗 / 会话不符 / 配置不符 / 断联 | 撤框显示 `WAITING FOR RESULT`；不留旧框 |
| 手动触发且被采纳的轮次 | `records.jsonl` 恰一条（键 session+check_id；截图前缀 `proto_`） |

## 三类场景与契约出处

- PASS/FAIL/RECHECK 循环报文：`sim/vision/test_vision_live_standin.py`（`--live` 替身服务）。
- 字段语义与边界（含 Q1–Q6 待确认项）：[docs/vision-live-semantics.md](../../../docs/vision-live-semantics.md)。
- 板端服务实现要求：(session_id, check_id) 唯一定位产物 + 原子落盘（C04 §2.3）。
