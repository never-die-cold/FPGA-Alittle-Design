# PYNQ 预处理诊断显示方案（2026-10-07）

状态：用户要求“十步一口气完成，最后出三道题”；十项已完成，RTL、控制脚本、bit、实机四视图及完整统一回归均通过，未提交。

## 已有证据与本次目标

- 分支 main，HEAD 0669960；此前相机/服务/串口记录等未提交改动保留。
- 相机 → Pi → PYNQ → USB Video 抓帧已通；电脑采集 1280×720/约 30fps。
- HDMI 显示目前保留 raw RGB/VS/HS/DE；分析流包含灰度、高斯、Sobel 等。
- 本轮原始基线：`data/logs/2026-10-07-hdmi-diagnostic/vision-baseline.log`。
- 命令 `bash sim/scripts/run_iverilog.sh vision all` 退出 0，23 个 tb，24 行 PASS。
  既有灰度 tb 的浮空标记警告与 scaler 数组敏感列表警告保留，未静默修改。
- 新目标：同一 HDMI 输出选择原图、灰度、高斯、边缘四种诊断画面。
- 不将诊断图或 OSD 当作物体定位/CNN 结果；本次不改 RISC-V 核接口。

## 设计

1. 复用分析支路，新增 R0 bit4 `diagnostic_display_en`；默认 0，显示原图。
   bit0/bit3 继续选择高斯/Sobel，bit1 快照与 bit2 OSD 保持既有语义。
   模式与分析开关仍通过 R11 原子提交，R12 确认，帧首应用。
2. 软件视图：COLOR 清 bit4；GRAY 设置 bit4、关闭高斯/Sobel；GAUSS 设置
   bit4/bit0、关闭 Sobel；EDGE 设置 bit4/bit0/bit3。切回 COLOR 保留分析配置。
   后三种模式的画面来自 FPGA 分析流，不在电脑上用 OpenCV 仿造处理效果。
3. `video_pipeline` 导出实际分析像素流与已应用的诊断显示位；复用 rgb2gray、
   gaussian_3x3、sobel 的结果，不新增一套算法。
4. 分析输出的单拍 VS/HS 不能直接驱动 rgb2dvi。新增显示适配：
   延迟完整 raw RGB/VS/HS/DE，并用少量循环行缓存保存分析像素，按延迟后的
   有效像素位置读出灰度值，将 `{Y,Y,Y}` 作为诊断 RGB 输出。
5. 对当前标准 720p60，以 H_TOTAL=1650、三行加少量流水拍作为候选统一显示延迟；
   灰度、高斯、双窗口链均在读出前完成所需行数据。最后一行冲刷亦需逐像素验算。
   所有视图共用该延迟，避免切换路径时改变同步脉冲相位；新增显示延迟约 67 微秒，
   精确拍数由 tb 和实现确定，不能把此值当作已测端到端延迟。
6. 循环行缓存带行/来源帧有效标记，处理结果未就绪时输出受控黑像素，禁止读陈旧数据。
   显示模式与来源帧标记随像素延迟，复位/失锁后等待完整帧，禁止半帧数据上屏。
7. 新诊断路径用参数启用：通用模块默认保留旧路径，物理 HDMI 工程显式启用。
   新模式在 1650×750、1280×720 有效区域下验收；不承诺其他输入格式。
8. 全部新增综合 RTL 使用 Verilog-2001；保持 AXI 域复位独立于视频锁定。

## 拆步清单（每项包括必要 tb/脚本，不含纯文档与日志）

| 步 | 交付物和主要文件 | 预计有效代码行数 | 验证 |
|:---|:---|:---|:---|
| 1 | 完整同步/彩色流延迟模块、单元 tb、回归入口；src/vision、sim/vision、sim/scripts | 90–100 | 固定延迟、宽同步脉冲、复位与整帧启动 |
| 2 | 分析流循环行缓存、单元 tb；src/vision、sim/vision | 90–100 | 行回绕、帧标记、未就绪、读写冲突 |
| 3 | 显示适配读出/选择、单元 tb；src/vision、sim/vision | 90–100 | 彩色/灰度逐像素、DE/VS/HS 完整 |
| 4 | R0 bit4 与帧首应用接口、配置 tb；vision_top.v、sim/vision；同步 design_v0.md | 70–95 | 暂存不生效、提交确认、帧内不变 |
| 5 | 接入真实分析流与参数分支；video_pipeline.v、vision_axi.v、集成 tb | 80–100 | 原图/灰度、旧路径兼容、失锁复位 |
| 6 | 四视图非恒定图案逐像素回归；sim/vision、sim/scripts | 80–100 | 灰度/高斯/边缘对照现有黄金参考 |
| 7 | 720p 完整时序、切换与末行测试；sim/vision、sim/scripts | 80–100 | 连续帧、行/像素数、冲刷、无撕裂 |
| 8 | 板端显示控制 API 与 mock 自测；src/pynq_host、sim/vision | 70–95 | 位域保留、四模式、超时与 busy |
| 9 | 串口可用的显示切换 CLI、物理工程启用、部署包入口；src/pynq_host、sim/scripts | 70–95 | 参数错误、旧命令兼容、Verilog-2001 编译 |
| 10 | 全回归、XSim、Vivado 布线/bit 构建与板端四视图；data/logs、docs | 无新增功能代码 | PASS、时序/DRC、实机原图/灰度/高斯/边缘采集 |

本轮按用户后续明确要求，十步连续执行，末尾统一三道理解题；未确认理解前不 commit。
统一入口为 `sim/scripts/run_iverilog.sh vision <单项>`，新 tb 接入 vision/all；收尾跑统一 all。
视觉 28 个 tb（29 行 PASS）、新显示/复位/AXI 失锁 XSim 6 项、Verilog-2001 解析已通过。
720p 四视图两轮共 7,372,800 输出像素精确核对。物理工程已布线出 bit，WNS +0.408ns。
串口传输、四种实机图像及回切原图均成功；完整 all 退出0、70行PASS，记录见本轮证据目录。

## 目录与上板安排

- 本需求已说明需要跨至 src/vision、sim/vision、src/pynq_host；其他改动限定
  sim/scripts、docs、data/logs、report/llm_log。保留所有既有未提交改动，不直接提交 main。
- 已使用 codex/pi-hdmi-diagnostics 功能分支；保留旧相机文档改动，不提交。
- 构建完成后保存新/旧 bit 哈希及回退文件，再加载并采集四种视图。
- 使用 COM12 原始二进制 ZIP 传输（239,135 字节），SHA256 与逐文件哈希校验；未挪网线。
- PYNQ 开机自动加载、CNN、自动定位、DDR 显示对照均不在本次实现范围。

## 实际交付归并

1–3：raster_delay / diagnostic_rows / diagnostic_display；单元与半帧复位 tb。
4–5：R0 bit4、video_pipeline/vision_axi 参数路径和真实分析流接入。
6–7：独立非恒定 RGB 黄金计算、四模式帧中提交、标准 1650×750 与复位两轮。
8–9：VisionRegs API、CLI/mock、Tcl 启用、独立构建目录与部署包。
10：Icarus/XSim、Vivado 布线、串口校验传输、四视图采集、回切彩色和实时预览。
另为统一 all 修复既有核的两个声明顺序问题，以及 all 调用但遗漏的 bht_flow_off 入口。
仅移动声明、补充模式选择，不改核功能/契约。
