# 人工按键测试运行记录（2026-10-08 22:54–22:59）

操作：watercopper 在本机运行 mock 服务 + `vision_preview.exe --mock --endpoint http://127.0.0.1:8765
--records-dir sim\build\records-manual-check`，窗口内按 `c` 两次、按 `q` 退出。

## 结果 1：按键记录路径通过（① 完成）

- `records.jsonl` = **2 行**（records.jsonl 本目录留档）：check 261（22:57:09）与 check 267（22:57:12），
  各一条批次记录 + 截图（`mock_6e5f2f16_000261/267.png`，实测含框画面）。
- 行内 `target_count=2`、半开区间 bbox、`mode=MOCK`、`result_age_s≈0.05`（EXE 接收时基）。

## 结果 2：暴露 flap 缺陷（本次修复对象）

- 同一运行的 `anomalies.jsonl` 在 ~2.5 分钟内记录 **576 条** `overlay_stale`/`overlay_ok` 往返
  （留档 `anomalies-before-fix.jsonl`）：每轮自动轮询产生 stale→ok 各一条。
- 根因：EXE 用"请求前取的钟"评估"请求处理时盖的服务端 created_at"，年龄为负（≈-3ms），
  被 `0<=age` 判为超龄；下一帧又正常 → 每 0.5s 翻转；窗口模式下表现为横幅每轮闪一帧"等待结果"。
- 该缺陷在老代码即存在（表现为静默闪帧），异常事件日志上线后立即显形——由人工实操先于
  自动化测试发现。

## 结果 3：修复后复核（同日 22:59，新 EXE）

- 同命令 4000 帧离屏运行，跨越 **22 轮自动轮询**（服务端 check_id 270→292）：
  `anomalies.jsonl` 仅 **1 条**初始 `overlay_ok`（留档 `anomalies-after-fix.jsonl`），
  **零 stale 翻转**；自动轮次仍未产生任何批次记录（records.jsonl 不存在 ✓）。
- 修复内容：新鲜度改按 **EXE 接收时刻**（received_at）计量，去掉跨机时钟比较与负年龄误判；
  overlay 用接收后新取的时刻评估（preview.py）。回归断言见 `test_vision_rounds.py`
  （"请求前的 now 评估刚采纳报文不得判超龄"）。

## 运行环境

session `6e5f2f16-255c-474e-ade2-495602fbe81c`（mock 服务）；EXE stdout 见 `exe-stdout.log`。
