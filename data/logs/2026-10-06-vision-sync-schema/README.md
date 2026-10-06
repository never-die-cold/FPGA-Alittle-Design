# 2026-10-06 视频/结果同步协议落码证据（schema v1.1 + EXE 轮次叠加）

环境：Windows 11（10.0.26200）｜ Python 3.13.5（py 启动器）｜ Windows PowerShell 5.1
分支：dev/bench（contract 基线 b51caaf）；契约依据 docs/vision-sync-protocol-decisions.md D1–D7

## 步骤 A：契约层 schema v1.1（commit 0c1fbf2）

等价 `run_vision_python.sh` 口径（本机无 MSYS2，py 直跑）：

```
py sim/vision/test_vision_regs.py            → PASS（test_vision_regs.log）
py sim/vision/test_localize.py               → PASS（test_localize.log）
py sim/vision/test_vision_protocol.py        → PASS（test_vision_protocol.log，新增 check_id/trigger_ref/判据用例）
py sim/vision/test_arm_localize.py           → PASS（test_arm_localize.log）
py sim/vision/test_arm_localize_package.py   → PASS（test_arm_localize_package.log）
```

改动：vision_protocol.py（check_id 必填、trigger_ref 可选、is_current 删 frame_id 匹配）、
vision_mock_service.py（POST /v1/check，check_id 单调回绕）、test_vision_protocol.py（用例同步）。

## 步骤 B：EXE 轮次级叠加（本目录 build_exe_round.log）

```
powershell -ExecutionPolicy Bypass -File sim/scripts/build_vision_client.ps1 -Python py
  → PASS: preview mock renderer packaged runtime
  → PASS: packaged EXE HTTP mock preview + unreachable route rejects, no UVC/board access
  → PASS: Windows M2 preview EXE build + packaged renderer test
```

test_vision_client.py 未修改即通过——CLI 契约（--mock/--headless/--frames/--endpoint/--save）保持兼容。

interval 启动守卫（PYTHONPATH=sim/build/vision-client-deps）：

```
py src/vision_client/preview.py --interval 2 --max-age 1
  → preview.py: error: --interval must be < --max-age, otherwise each round expires before the next（退出码 2，拒绝）
py src/vision_client/preview.py --interval 0.5 --max-age 1 --selftest
  → PASS: preview mock renderer packaged runtime
```

5 项 Python 回归重跑全 PASS（日志为本目录同名文件，步骤 B 时间戳覆盖）。

## 边界声明

- 本轮全部为离板验证（mock 服务 + 合成场景）；UVC 真实采集卡 + mock 结果叠加模式
  （`--source 0 --endpoint ...`）待板卡/采集卡在位时实测，不据此声明端到端完成。
- 真实 PS 结果服务未实现（D7，NC 负责）；EXE 对 MOCK 报文恒标 MOCK ONLY。
