# 2026-10-09 HUD v4（Step 1：Pillow 文本引擎 + 布局定稿图，待评审）

用户方向（2026-10-09）：在 v3.1 基础上走"**性价比子集**"升级——Pillow 真字体（同时解锁
M3 中文能力）+ 圆角面板 + 顶栏 + 检测对象列表 + 检查按钮；**不换技术栈**；
目标是参考设计图约 70% 观感（辉光/真阴影/侧边导航不做）。

## 本步交付

- `src/vision_client/hud_text.py`：**TextEngine**——Pillow 文本 → RGBA 贴图缓存 +
  alpha 混合贴图（每帧性能与 Hershey 相当）；变量字体按名取字重（InterVariable，
  Regular/SemiBold/Bold）；`asset_path()` 统一源码/打包（PyInstaller `_MEIPASS`）寻径
- `src/vision_client/assets/fonts/`：`InterVariable.ttf`（OFL 开源协议）+ `OFL.txt`（873 KB）
- `requirements.txt` / `build_vision_client.ps1`：新增 `pillow==12.3.0` 依赖与自检断言
- `render_v4_mockup.py` + `v4_mockup.png`：**1600×900 布局定稿图**（本步评审对象）

## 布局（定稿图对应，坐标为 1600×900 画布）

顶栏 64px：logo/标题/字距副标题/SYSTEM ONLINE/时钟｜视频视口 (24,88,1288,799)：
圆角 14 + 细边框 + 四角标（源 1280×720 映射比例 0.9875）｜右上指标面板
(712,108,1272,222)：三格 + 图标位 + FRESHNESS 内嵌条｜右列
(1312,88,1576,799)：DETECTED OBJECTS n/n 徽标 + 卡片（缩略图/T序号/XYWH）+
RUN INSPECTION 渐变按钮｜左下状态块 (24,823)。

## 性能方案（Step 2 实施要点）

静态外壳（顶栏/面板/细边框/静态文字）**启动渲染一次存底图**（2× 超采样保证圆角/描边
平滑）；每帧 = 底图拷贝（~1ms）+ 视频缩放进视口（~2-3ms）+ 动态元素（框/数字/条，
~2ms）+ 文本缓存贴图（~1ms）≈ **6-8ms/帧**，30fps 预算占用约 20-25%。

## 状态

Step 1 完成（引擎可运行、定稿图目检通过）；**待用户评审布局** → Step 2 接入
`preview.py`（含字体随包打包 `--add-data`、打包/回归验证、实机窗口复验）。

## 边界

mock 场景与 mock 数据；本步未接产品代码，帧率/端到端指标不受影响（无行为变更）。
