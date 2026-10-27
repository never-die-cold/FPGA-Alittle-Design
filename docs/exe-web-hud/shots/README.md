# 评审截图存档（shots/）

2026-10-27/28 浏览器实渲染评审的截图存档（1600×900 视口拍摄，归档时缩放至 1280×720，
Pillow `optimize=True` 无损重压；总 3.6 MB，单文件 ≤0.53 MB，未超 5 MB allowlist 线）。
对应「视觉改动先出渲染图评审」纪律；纯前端合成画面，**不代表板端识别效果，不得作为板端证据**。

## 清单（repo-hygiene 规则 6：用途 / sha256 / 重建方式）

| 文件 | 用途 | sha256 |
|:---|:---|:---|
| 01-default-dark.png | 暗色默认态：CHECK_PASS 横幅、FRESHNESS 充能、三栏布局基准 | `9759D488…C821F8` |
| 02-run-queued.png | RUN 按钮琥珀 QUEUED · WAITING 态 | `0E5FF528…E53E8` |
| 03-run-running.png | RUN 按钮暗底 RUNNING 态（旋转指示） | `A2D8CBFE…4EF4ED` |
| 04-recheck-target-limit.png | target_limit 轮：RECHECK 未完整计数、计数列 `--`、unclassified 目标 | `83BEBD25…4C6AAC` |
| 05-scope-filter-washer-off.png | 取消勾选 washer：框消失、计数灰显保留、T 序号不重排 | `4A67B48A…13A2` |
| 06-theme-light.png | 亮色主题（视频区外阴影层次） | `1B3255CC…A4A48D` |
| 07-replay-readonly.png | FILE REPLAY 只读：OFFLINE FILE 徽标、无勾选框、「实际 / 工单」计数 | `D1F9B81D…4CDEF` |
| 08-disconnected-reconnecting.png | 断联：SERVICE LOST、撤框、RECONNECTING 衬底、失败 1/3 日志 | `A97D2E03…28BD1` |
| 09-responsive-1366.png | 1366×768 响应式不破版 | `B02B4CD5…359350` |

sha256 为完整哈希（表中截断显示前 8 位 + 后 6 位）；完整值以 `Get-FileHash -Algorithm SHA256` 复核为准。

## 重建方式

1. 仓库内打开 `docs/exe-web-hud/index.html`（浏览器窗口 1600×900，暗色主题）；
2. 按下表操作触发对应状态：

| 文件 | 操作 |
|:---|:---|
| 01 | 等待约 1.5s（首条自动轮 CHECK_PASS 场景） |
| 02 / 03 | 点击 RUN INSPECTION 后约 0.45s / 1.1s |
| 04 | 演示控制 → target_limit 轮，再点击 RUN INSPECTION，等待约 2.6s |
| 05 | 在识别范围表点击 washer 行取消勾选 |
| 06 | 点击右上角主题切换按钮 |
| 07 | 数据源 → 打开 FILE REPLAY |
| 08 | 演示控制 → 模拟断联，等待约 0.9s |
| 09 | 浏览器窗口缩至 1366×768 |

截图为手工评审产物（ZCode 内侧浏览器拍摄）；未入库自动化截图脚本，
复现以页面交互为准，截图文件本身仅作评审存证。
