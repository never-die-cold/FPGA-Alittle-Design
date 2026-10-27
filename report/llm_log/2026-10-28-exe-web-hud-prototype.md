# 2026-10-28 EXE HUD v4 Web 化原型（docs/exe-web-hud）

> 请求：全面阅读 EXE 前端相关文档后，把 EXE 前端改成 HTML 前端；仿
> `D:\Desktop\contests\2026fpga\frontend`（Project Mozart 控制中心，Vue3+Tailwind）的
> 页面布局/交互思路/界面外形；配色自选，要求简洁大气精美。

## 读了什么（输入）

- `src/vision_client/README.md`、`hud.py`（布局常量与调色板的权威来源）、
  `data/logs/2026-10-08-exe-ui-design/`（NASA declutter 原则、状态语义色、等待三重冗余）、
  `data/logs/2026-10-09-exe-hud-v4/`（应用外壳定稿、性能优化、DPI 适配）、
  `data/logs/2026-10-17-exe-scope-redesign/`（识别范围表交互定稿、绿色专属约束）
- 参考前端：`frontend/src/App.vue`、`styles.css`、`index.html`（设计令牌、亮暗主题、
  顶栏 hardware-stat、终端日志、toast、toggle 体系）

## 关键设计决策

1. **骨架借参考、信息架构留 EXE**：顶栏状态条 + 三栏（左控制/中视频/右结果）来自 Mozart；
   识别范围表置右栏顶部、DETECTED OBJECTS 随其下、画面无遮挡、RUN 按钮三态并入范围表，
   全部维持 10-09/10-17 两次评审定稿不变。
2. **配色沿用 hud.py 色板**（BG 14,19,28 系、CYAN 0,210,255、GREEN 0,230,130、
   AMBER 255,176,32、RED 255,77,79）并补亮色变体；绿色专属目标框/T 片/判定 PASS，
   面板控件一律品牌青（延续 10-17 约束）。
3. **状态语义按 rounds.py 对外行为演示**：D3 有效性（会话+配置号+年龄窗）三重冗余撤框、
   手动轮才 REC+1、手动失败立即撤旧 PASS、3 次失败重握手换 session（D5）、
   target_limit 轮计数 `--` 不映射零值、勾选仅本地过滤且 T 序号不重排、
   interval ≥ max-age 拒绝（启动校验）。
4. **单文件零依赖**：不引 CDN，字体复用仓库内 InterVariable.ttf（相对路径，拷走则回退系统字体）；
   与「可复现性」红线一致——打开即用、无构建步骤。
5. 不做「固定 1600×900 画布模式」：transform 缩放与 CSS 媒体查询语义冲突，为不引入
   半成品特性而放弃；自适应布局已实测 1366×768 不破版。

## 过程中发现并修复的 bug（浏览器实测发现）

- `.overlay-center{display:flex}` 覆盖 `hidden` 的 UA 样式 → WAITING 遮罩常显；
  补全局 `[hidden]{display:none!important}`。
- `freshnessLoop` 定义后未启动定时器 → FRESHNESS 条恒空；补 `setInterval(180ms)`。
- 演示注入的强制场景被并发自动轮消费 → 注入改为仅由手动轮消费。
- toast 顶部居中与判定横幅叠压、半透明底在视频上发虚 → 改底部居中实底卡片。
- 断联时左栏服务状态未联动 → renderTopbar 统一回写。
- 手动轮入队日志预测 check 号会被自动轮占用 → 改为完成时分配。

## 验证

- 浏览器实渲染截图走查 11 个状态：暗色默认/QUEUED/RUNNING/RECHECK(计数--)/
  勾选过滤/亮色主题/FILE REPLAY 只读/断联 RECONNECTING/max-age 拒绝 toast/
  CSV 导出日志/1366×768 响应式，全部通过（截图在本会话存档，未入库）。
- 复现入口：`start docs\exe-web-hud\index.html`（或任意静态服务器指向仓库根）。
- 纯前端模拟，无板端依赖，不产生板端证据（README 边界已声明）。

## 边界

未接真实数据源；勾选不下发（待 C04 §6）；EXE 发布物仍以 Pillow HUD 为准，
本原型不改动 `src/vision_client/` 任何源码。

## 用户反馈驱动的修复（2026-10-28 补）

- owner 实测「数据源开关点了没反应」：`.toggle` 的视觉层 track/knob 叠在透明
  `<input>` 之上拦截了全部点击（自动轮询开关同病）→ 两者加 `pointer-events:none`
  让事件落到 input；当前模式关断改为回弹 + toast 说明（三种组装互斥、恒有其一）。
- 提示语「与 EXE 组装模式对应」改为「对应 EXE 三种启动方式」，README 补齐
  `--endpoint` / `--mock` / `--replay` 映射说明。
- 评审截图 9 张按 repo-hygiene 规则 6 入库 `shots/`（用途 + sha256 + 重建方式；
  1280 宽 + Pillow optimize，共 3.6 MB）。
