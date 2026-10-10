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

### 性能（实测与优化，2026-10-09）

- **首版实测 124.7 ms/帧（≈8fps）**（bench_hud.py 渲染计时循环）——"静态预渲染保 30fps"
  的事前估算与实测严重不符；实机复验截图 FPS 读数 6 暴露此问题。
- **定位**：两个"整幅级 float32 混合"是主凶——视频遮罩贴合与视口边框 RGBA 整幅粘贴，
  各在 270 万像素上做多轮浮点运算。
- **优化三步（只处理真正需要混合的像素）**：
  1. 视频贴合 = 直拷 + 仅四角小块混合（PIL 圆角为硬边，约 99% 区域掩码=1）；
  2. 视口边框拆成四条边缘带粘贴（中部透明区不逐帧处理）；
  3. 大面板（右列面板/卡片/RUN 按钮）改**不透明直拷 + 圆角外像素布尔恢复**（`_blit`，
     memcpy 级）；混合公式统一 uint16 整数（`>>8` 代除法）。
- **优化后 16.3 ms/帧（7.6× 提速，bench_hud.py 实测）**；显示循环改 30fps 精确节流
  （`waitKey(1)` + 余量 sleep，`preview.py`）。视觉输出与优化前逐像素一致（02/03/04/05 复查）。

### 高分屏适配（2026-10-09 追加）

用户全屏截图暴露：2880×1800@200% 屏幕下 DPI-不感知窗口被系统放大 2 倍 → 右侧切割且发虚。
修复：启动声明 PerMonitorV2 DPI 感知 + 工作区等比缩放（本机 2880×1704 → scale 1.8 →
显示 2880×1620）；鼠标坐标反变换；`--save` 仍输出原生 1600×900（build_exe_v4_dpi.log）。

**实机复验（manual-dpi-run/）**：修复后用户操作窗口触发 **6 次**（全部记录，REC 6）、
截帧 FPS 读数 **28**（性能优化 + DPI 适配后实际窗口帧率）；异常日志仅 1 条初始事件。

## 边界

mock 场景与 mock 数据；UVC 真实画面上的观感待采集卡实测；帧率读数在 headless 保存模式下
无意义（真实窗口 ~30fps）。
