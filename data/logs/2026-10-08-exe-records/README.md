# 2026-10-08 EXE 批次记录（D8–D10）离板实现与验证

环境：Windows 11（10.0.26200）｜Python 3.13.5（py 启动器）
分支：dev/exe（worktree sim/build/exe-wt）；契约依据 docs/vision-sync-protocol-decisions.md D8–D10

## 实现

- `rounds.py`：`trigger(now)` 手动触发立即发起 + 0.3s 防抖 + `last_round_manual` 标记（D8）
- `records.py`：`BatchRecords`——键 (session_id, check_id) 去重 / records.jsonl 追加 /
  截图经注入回调（缺省惰性导入 cv2）/ MOCK 前缀（D9/D10）
- `preview.py`：`--records-dir` 开启；仅"手动触发且当前有效"的轮次落记录，横幅追加 `| REC n`；
  `c` 键改走 `trigger()`

## 验证

- 全量 Python 回归 **7/7 PASS**（本目录 test_*.log）：regs / localize / protocol / rounds /
  records / arm_localize / arm_localize_package
- 打包 EXE 重建三关 PASS（build_exe_records.log）。打包联调断言（test_vision_client.py）：
  自动轮次运行 3 帧后 **records.jsonl 不存在**——"重复帧不增加批次计数"的离板证据。
- 单元覆盖：键去重 / MOCK 前缀 / 字段完整性 / 追加（test_vision_records）；
  手动触发立即发起 + 防抖 + 标记（test_vision_rounds）。

## 未覆盖（待人工/上板）

- 按键→记录的真实交互（headless 无法注入按键）：实操按一次 `c`，确认 records.jsonl 新增一行、
  截图出现在 screenshots/。
- 真实板端结果 + UVC 画面上的记录（待 NC 服务落地与采集卡在位）。

## 边界声明

MOCK 记录截图带 `mock_` 前缀且 mode=MOCK，不得用作板上识别证据（plan.md §3.4）；
本目录全部为离板验证。
