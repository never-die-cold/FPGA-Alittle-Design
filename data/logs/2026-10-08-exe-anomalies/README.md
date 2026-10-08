# 2026-10-08 EXE 批次记录加固：采纳点语义修复 + 异常事件日志（D11）

环境：Windows 11｜Python 3.13.5（py 启动器）｜分支 dev/exe（worktree sim/build/exe-wt）
契约依据：docs/vision-sync-protocol-decisions.md D8（补充）/ D11

## 修复：断联中手动轮残包不得冒充记录（D8 采纳点语义）

- 问题：`last_round_manual` 原先在"发动请求"时标记——断联中按 c 触发失败后，
  残留旧报文（仍在显示窗内）会被当成这次手动检查写入批次档案。
- 修复：标记移到"报文被采纳"之后（rounds.py poll）。
- 定向测试：test_vision_rounds.log——断联中手动触发→失败轮→`not last_round_manual`。

## 新增：异常事件日志（D11）

- `RemoteRounds._state()` 把 D3 判定拆为带原因状态（no_result/outage/session/config/stale/
  offline/ok）；overlay 在**状态迁移沿**push 事件（含恢复 ok），poll/rehandshake 各补
  session_changed / rehandshake_failed。
- `records.AnomalyLog` 落盘 `anomalies.jsonl` + `screenshots/anomaly_*.png`（MOCK 前缀同批次）。
- 测试：test_vision_records.log（AnomalyLog 字段/编号/前缀）；
  test_vision_rounds.log（事件集合覆盖 6 类迁移）；test_vision_client（打包断言 anomalies.jsonl 存在）。

## 验证入口与结果

```
py sim/vision/test_vision_*.py ...（全 7 项，本目录 test_*.log）→ 全 PASS
powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1 -Python py
  → PASS: preview mock renderer packaged runtime
  → PASS: packaged EXE HTTP mock preview + unreachable route rejects ...（含：自动轮不落记录、
    --trigger-frame 手动轮恰好一条批次记录 + 截图 + anomalies.jsonl 存在、绿框内容断言）
  → PASS: Windows M2 preview EXE build + packaged renderer test
```

## 人工待办（1 分钟）

真实按键路径：`vision_mock_service.py` + `vision_preview.exe --source 0 --endpoint ... --records-dir <目录>`，
按一次 `c`（≈0.5s 后）确认横幅出现 `| REC 1`、目录出现 records.jsonl 一行 + 截图；
再按一次确认 `REC 2`。headless 无法注入按键，故此步保留人工。

## 边界声明

离板验证；MOCK 记录带 `mock_` 前缀不得用作板上识别证据；真实板端服务待 NC（D7）。
