# 2026-10-08 EXE 轮次叠加：bbox 半开对齐 + 状态机抽离与撤框/断联测试

环境：Windows 11（10.0.26200）｜ Python 3.13.5（py 启动器）｜ Windows PowerShell 5.1
分支：dev/exe（worktree sim/build/exe-wt）；契约依据 docs/vision-sync-protocol-decisions.md

## 步骤 1：bbox 端点语义改半开区间（commit c037273）

- 对齐 docs/outsource/localization-requirements.md L2：`[x0,x1)×[y0,y1)`，宽=x1-x0，
  右下端点可恰为 w/h；退化/反向/越界拒绝；preview 画框右下取 x1-1/y1-1。
- 验证：test_vision_protocol.log（含端点/退化/反向新用例）；preview_selftest_bbox.log。

## 步骤 2：轮次状态机 rounds.py 抽离 + 离线测试（本目录）

```
py sim/vision/test_vision_rounds.py
  → PASS: round overlay trigger/throttle/stale/config-change/outage/session-recovery
  （输出含预期 WARN 序列：断联 check failed 1/3..3/3 → re-handshake failed → 会话变化重握手）
```

全量 Python 回归 6/6 PASS（本目录 test_*.log）：
vision_regs / localize / vision_protocol / vision_rounds / arm_localize / arm_localize_package

EXE 重建（build_exe_rounds.log）：
`powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1 -Python py`
→ `PASS: preview mock renderer packaged runtime`
→ `PASS: packaged EXE HTTP mock preview + unreachable route rejects, no UVC/board access`（含新增内容断言）
→ `PASS: Windows M2 preview EXE build + packaged renderer test`

## 本轮发现并修复的真 bug（test_vision_rounds 首跑暴露）

`/v1/check` 误发 **GET**（`http_json` 以"有无 body"区分 GET/POST，poll 未传 body）→ mock 仅注册
POST → 404 → **端点模式叠框从未生效**。旧打包测试只验"跑通+出图"，未验画面内容，未能发现；
已在 `sim/vision/test_vision_client.py` 补"绿色目标框像素"内容断言（本次重建起生效）。

另修两处状态机缺口（设计审查发现，测试覆盖）：重握手失败异常外泄导致崩溃（服务重启窗口期）；
服务重启后新会话不触发重握手导致永久 WAITING（违反 D5）。

## 边界声明

- 全部为离板验证（mock 服务 + 合成场景）；UVC 采集卡 + `--endpoint` 实测待板卡/采集卡在位。
- 真实 PS 服务未实现（决策单 D7，NC 负责）；EXE 对 MOCK 报文恒标 MOCK ONLY。
