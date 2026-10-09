# 2026-10-09 EXE HUD v3 实装（preview.py 绘制层重写）

环境：Windows 11｜Python 3.13.5（py 启动器）｜分支 dev/exe（worktree sim/build/exe-wt）
设计依据：`data/logs/2026-10-08-exe-ui-design/README.md`（v3 冻结）

## 改动

- `src/vision_client/preview.py` 绘制层重写：左状态框（半透明衬底 + 细边框 + 模式徽标 +
  状态行）、右上四格指标面板（ROUND / TARGETS / REC / AGE 大数字 + 新鲜度条）、目标实线绿方框
  + T 序号片、语义色三态（绿 = 有效 / 深琥珀 = 等待 / 红 = 过期）
- 四模式共用 `draw_hud`：端点有效 / 等待过期 / 本地演示（LOCAL DEMO）/ UVC-only
  （**隐藏指标面板**，用户 2026-10-09 拍板）
- mock 合成场景升级：冷灰台面 + 细网格 + 椭圆"零件"（与设计稿一致）
- `sim/vision/test_vision_client.py`：绿色像素判据适配 v3 调色板——改"通道相对差"式并对
  numpy 运算先 `astype(int16)`（uint8 差值会回绕、把浅灰背景误判成绿色）

## 验证

- **四种模式出图目检**（本目录 PNG）：`02_endpoint_ok.png`（真实运行，端点有效）/
  `03_local_demo.png`（真实运行，本地演示）/ `04_waiting_state.png`（等待过期）/
  `05_uvc_only.png`（UVC-only）。后两张由 `render_hud_states.py` 以产品 `draw_hud` 渲染
  （值字典与 preview.main 组装一致，属近似校验；真机 UVC 画面观感待采集卡）
- **打包重建三关 PASS**（build_exe_hud.log）：selftest（新增"绿框像素 >500"断言）+ 打包
  HTTP 联调（内容断言 / 自动轮不记录 / 手动轮恰好一条记录 + 异常日志 / 坏端点拒绝）
- **全量 Python 回归 7/7 PASS**（本目录 test_*.log）

## 实机人工目检（2026-10-09，用户操作打包 EXE 窗口）

命令：`vision_preview.exe --mock --endpoint http://127.0.0.1:8765 --records-dir <dir>`，
用户按 `c` **4 次**、`q` 退出：

- `records.jsonl` **4 行**（check 27/40/84/87，留档于 `manual-hud-run/`）——按键记录路径在新
  HUD 下正常；`rec4_frame.png` 为第 4 次按键时截帧：面板显示 **REC 4** / ROUND 87 /
  TARGETS 2 / AGE 0.0s + 满格新鲜度条
- `anomalies.jsonl` **仅 1 条**初始 `overlay_ok`——flap 未复发（全程无 stale 翻转）
- stdout 无 WARN（仅 libpng iCCP 提示，无害）

## 边界声明

MOCK 数据；真实 UVC 画面上 HUD 的观感（对比度/遮挡）待采集卡在位实测；中文类别名（M3）
需 Pillow 预渲染，未做。
