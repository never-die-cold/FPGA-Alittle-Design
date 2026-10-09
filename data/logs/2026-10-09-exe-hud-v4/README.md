# 2026-10-09 HUD v4（Pillow 文本引擎 + 布局定稿 + 接入产品）

用户方向（2026-10-09）：在 v3.1 基础上走"**性价比子集**"升级——Pillow 真字体（同时解锁
M3 中文能力）+ 圆角面板 + 顶栏 + 检测对象列表 + 检查按钮；**不换技术栈**；
目标是参考设计图约 70% 观感（辉光/真阴影/侧边导航不做）。

## Step 1 交付（字体引擎与布局定稿）

- `src/vision_client/hud_text.py`：**TextEngine**——Pillow 文本 → RGBA 贴图缓存 +
  alpha 混合贴图；变量字体按名取字重（InterVariable，Regular/SemiBold/Bold）；
  `asset_path()` 统一源码/打包（PyInstaller `_MEIPASS`）寻径；`draw_cy()` 按**墨迹中心**
  垂直对齐（符号/短横线专用）
- `src/vision_client/assets/fonts/`：`InterVariable.ttf`（OFL 开源协议）+ `OFL.txt`（873 KB）
- `render_v4_mockup.py` + `v4_mockup.png`：1600×900 布局定稿图（三轮评审修订版）

## Step 2：接入产品（2026-10-09 完成）

- **新模块 `src/vision_client/hud.py`**（Hud 渲染器）：静态基座（背景渐变/顶栏底线/品牌块/
  SYSTEM ONLINE/时钟图标）启动预渲染一次，每帧仅 `base.copy()`；面板/卡片/RUN 按钮/徽标
  药丸等固定形状元素预渲染 RGBA 贴图缓存；动态文本走 `hud_text` 引擎贴图缓存；缩略图按
  轮次缓存（bbox 键）。
- **`preview.py` 状态字典化改造**：主循环 = 源帧 → 状态字典（endpoint / LOCAL DEMO /
  UVC-only 三种组装）→ `hud.render` → 1600×900 画布；`RUN INSPECTION` **鼠标可点击**
  （`cv2.setMouseCallback`，与 `c` 键双通道触发）；FPS 实测与时钟进顶栏。
- **字体随包**：`--add-data`（绝对路径——`--specpath` 下相对路径以 spec 目录为基准，
  已踩坑）；selftest 构建完整 Hud 对象 = 等效验证打包字体的运行期寻径。
- 修复记录：药丸贴片合成错误（底色被文字缓冲替换，徽标文字消失）——详见 llm_log。

### 验证

- **四态实渲染**（本目录）：`02_endpoint_ok.png` / `03_local_demo.png`（真实运行保存）/
  `04_waiting_state.png` / `05_uvc_only.png`（render_hud_states.py 以产品 Hud 渲染）
- **打包三关 PASS**（build_exe_v4.log）：selftest（含视口区绿色断言）+ 打包 HTTP 联调
  （绿色内容断言只看视频视口 24,88,1288,799，防 RUN 按钮渐变混入计数）+ 记录 E2E
- **回归 7/7 PASS**（test_*.log）
- **字体入包核对**：`dist/vision_preview/_internal/assets/fonts/{InterVariable.ttf, OFL.txt}`

### 性能

每帧 ≈ 底图拷贝 1-2ms + 视频缩放 2-3ms + 圆角遮罩贴合 2-3ms + 动态绘制 ~2ms ≈ **8-10ms**，
30fps 预算（33ms）占用约 30%。静态预渲染 + 贴图缓存保证外挂全套外壳后帧率不受影响。

## 边界

mock 场景与 mock 数据；UVC 真实画面上的观感待采集卡实测；帧率读数在 headless 保存模式下
无意义（真实窗口 ~30fps）。
