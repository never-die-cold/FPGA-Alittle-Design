# EXE HUD v4「应用外壳」Web 化原型（2026-10-27）

`index.html` 是 Windows EXE 前端（`src/vision_client/`，HUD v4「EdgeSight 应用外壳」）
的 **纯前端 Web 化设计原型**：把 HUD v4 的信息架构与状态语义搬进浏览器，
页面骨架、交互思路与视觉语言借鉴 Project Mozart 控制中心前端
（顶栏状态条 + 三栏布局 + 设计令牌 + 亮暗主题 + 终端式日志）。
**单文件、零依赖、无构建步骤**，浏览器直接打开即可运行。

## 打开方式

直接双击 `index.html`，或：

```powershell
start docs\exe-web-hud\index.html
```

字体复用仓库内 `src/vision_client/assets/fonts/InterVariable.ttf`（OFL），
因此请在仓库内原位打开；单独拷走时回退系统字体，仍可正常显示。
默认暗色主题，右上角按钮切换亮/暗（localStorage `edgesight-theme`）。

## 信息架构映射（EXE HUD v4 → Web）

| EXE HUD v4 定稿 | Web 原型 |
|:---|:---|
| 顶栏（徽标 / 状态 / 分辨率·FPS·session / 时钟） | 顶部状态条（徽标 + 判定文字 + RES/FPS/SESSION 仪表组 + SYSTEM ONLINE + 时钟） |
| 视频圆角视口（无面板遮挡，角括号，绿框 + T 序号片） | 中栏视频舞台（角括号 + 绿框 + T 片 + 判定横幅 + WAITING 深色衬底） |
| 识别范围表「INSPECTION SCOPE」右栏置顶 | 右栏置顶卡片：勾选框 / 类别 / 计数，行悬停高亮 |
| FRESHNESS 条 + RUN INSPECTION 三态按钮 | 并入范围表内：青 IDLE → 琥珀 QUEUED·WAITING → 暗底 RUNNING |
| DETECTED OBJECTS（3 卡片 + +N more） | 右栏第二卡片（缩略图 / T 序号 / XYWH） |
| EdgeSight 品牌块 | 顶栏品牌 + 左上 logo |
| 终端式日志（EXE 无，参考前端有） | 中栏底部终端日志（标签过滤，演示轮次/状态/链路事件） |
| —（EXE 用命令行参数） | 左栏表单：自动轮询开关、interval、max-age、数据源三模式、演示事件注入 |

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

## 边界（勿过度解读）

- **纯前端模拟**：合成数据、合成场景循环（PASS → FAIL → RECHECK），不访问相机、板端服务或 records 目录；
  不代表板上识别效果，不得作为板端证据。
- 不是 EXE 发布物，也不改动 `src/vision_client/` 任何源码；EXE 仍以 Pillow HUD 为准。
- 未实现（原型范围内明确不做）：真实数据源接入、勾选下发服务端（待 C04 §6）、多会话/权限、国际化。
