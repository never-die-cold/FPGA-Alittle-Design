# EdgeSight 网页端（HUD v4「应用外壳」，2026-10-27 起）

`index.html` 是 EdgeSight 的 **HTML 网页端前端**（HUD v4「EdgeSight 应用外壳」）：
页面骨架、交互思路与视觉语言借鉴 Project Mozart 控制中心前端
（顶栏状态条 + 三栏布局 + 设计令牌 + 亮暗主题 + 终端式日志），
信息架构与状态语义沿用 HUD v4 定稿。
**单文件、零依赖、无构建步骤**，浏览器直接打开即可运行。当前为纯前端原型（合成数据），真实数据源接入为待接入项。

## 打开方式

直接双击 `index.html`，或：

```powershell
start src\web_client\index.html
```

字体在本目录 `assets/fonts/InterVariable.ttf`（OFL）；
单独拷走 `index.html` 时回退系统字体，仍可正常显示。
默认暗色主题，右上角按钮切换亮/暗（localStorage `edgesight-theme`）。

## 信息架构映射（HUD v4 → 网页端）

| HUD v4 定稿（原 EXE 形态） | 网页端 |
|:---|:---|
| 顶栏（徽标 / 状态 / 分辨率·FPS·session / 时钟） | 顶部状态条（徽标 + 判定文字 + RES/FPS/SESSION 仪表组 + SYSTEM ONLINE + 时钟） |
| 视频圆角视口（无面板遮挡，角括号，绿框 + T 序号片） | 中栏视频舞台（角括号 + 绿框 + T 片 + 判定横幅 + WAITING 深色衬底） |
| 识别范围表「INSPECTION SCOPE」右栏置顶 | 右栏置顶卡片：勾选框 / 类别 / 计数，行悬停高亮 |
| FRESHNESS 条 + RUN INSPECTION 三态按钮 | 并入范围表内：青 IDLE → 琥珀 QUEUED·WAITING → 暗底 RUNNING |
| DETECTED OBJECTS（3 卡片 + +N more） | 右栏第二卡片（缩略图 / T 序号 / XYWH） |
| EdgeSight 品牌块 | 顶栏品牌 + 左上 logo |
| 终端式日志（参考前端引入） | 中栏底部终端日志（标签过滤，演示轮次/状态/链路事件） |
| —（原视口形态用命令行参数） | 左栏表单：自动轮询开关、interval、max-age、数据源三模式、演示事件注入 |

数据源三行的含义（单选互斥，同一时刻只运行一种）：
`LIVE` = 采集卡视频 + 板端 `:8765` 轮次叠加（真实数据接线待完成）；
`LOCAL DEMO` = 本地合成数据（MOCK ONLY 徽标，不得作为板端证据）；
`FILE REPLAY` = `result.json` 离线回放（只读：无触发按钮、无勾选框、计数为「实际/工单」）。
服务不可达时隐藏面板并进入重连，原型中以断联演示近似表达。

## 状态语义（对 `rounds.py` 对外语义的演示）

- 结果有效性 = 会话 + 配置号 + 年龄窗（D3）：过期 / 断联 / 配置变化即**撤框 + 计数置 -- + 状态文字**三重冗余；
- 手动轮（按钮 / `C` 键）成功才 REC+1 并落记录；自动间隔轮永不记录；
- 手动轮失败立即 `NO VALID RESULT | check failed` 并撤旧 PASS，不等 max-age（2026-10-20 语义）；
- 断联连续 3 次 HTTP 失败自动重新握手（D5），恢复后更换 session；
- target_limit 轮：RECHECK 未完整计数，计数列显示 `--`，不映射零值；
- 勾选只作用于本地显示/跟踪：未勾选类别不画框、不进列表，**T 序号保留原始编号不重排**，计数灰显保留（不隐瞒）；
- interval ≥ max-age 的参数组合按启动校验语义拒绝（防止周期性空窗）。

## 配色纪律（沿用 HUD v4 定稿）

- 面板区 UI 控件一律**品牌青**（勾选态、RUN 按钮、FRESHNESS、REC 计数）；
- **绿色专属**目标框 / T 序号片 / 判定 PASS / 对象计数徽标，不与普通 UI 混用；
- 琥珀 = 等待（QUEUED / WAITING / RECHECK），红 = FAIL / PROTOTYPE / 故障；
- 等待文字置于深色衬底框内（避免亮琥珀落在浅底发虚，10-08 定稿要点）。

## 评审截图

9 张实渲染截图（2026-10-27/28 评审，各状态基准图，含 sha256 与重建步骤）存档于
[data/evidence/2026-10-28-web-hud-shots](../../data/evidence/2026-10-28-web-hud-shots/README.md)。

## 边界（勿过度解读）

- **纯前端模拟**：合成数据、合成场景循环（PASS → FAIL → RECHECK），不访问相机、板端服务或 records 目录；
  不代表板上识别效果，不得作为板端证据。
- 网页端即前端形态；真实数据源接入与勾选下发服务端（待 C04 §6）为待接入项。
- 未实现：勾选下发服务端（待 C04 §6）、多会话/权限、国际化。
