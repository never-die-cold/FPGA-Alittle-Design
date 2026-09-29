# src/vision —— HDMI 图像预处理流水线 RTL

HDMI 视频流逐像素实时处理：灰度化 → 3×3 高斯滤波 → 双线性缩放 → 可选 Sobel 边缘。

## 当前状态（2026-09-29，单元级超前完成）

回归入口 `bash sim/scripts/run_vision_iverilog.sh all`，10/10 tb PASS；日志 `data/logs/2026-09-29-vision-m2-kickoff/vision-all-10tb.log`。

| 模块 | 状态 | 要点 |
|:---|:---|:---|
| `rgb2gray.v` | 已实现 | BT.601 定点，黄金参考逐像素对拍 |
| `line_buffer.v` | 已实现 | 同步读、同拍同址先读后写（旧值） |
| `gaussian_3x3.v` | 已实现 | 双行缓存轮替、边界钳位、vblank 冲刷末行 |
| `scaler.v` | 已实现 | 16.16 定点双线性、行槽滑动、自产 `out_vs/out_hs` 标记 |
| `sobel.v` | 已实现 | Gx/Gy L1 幅值饱和；单元级 PASS，未接入 `vision_top` |
| `osd_overlay.v` | 已实现 | box/roi 双框叠加、帧首参数锁存 |
| `axi_regs.v` | 已实现 | AXI-Lite 16 寄存器；`AW` 须满足 `2^AW > NREG*4` |
| `vision_top.v` | 骨架 | rgb2gray 恒接 + gauss/scaler/osd 开关，帧首拓扑锁存 |

实现口径见 [design_v0.md](design_v0.md) §3.1/§3.2；接口契约仍为草案，10/5 评审后升格冻结。

## 未完成

- HDMI 输入/输出通路选型（ADV7611 I2C/EDID vs Vivado IP）、分辨率/色彩空间、pclk 频率——见 [design_v0.md](design_v0.md) §5。
- 缩放目标尺寸待模块三网络输入拍板；`sobel` 接入位置待评审。
- PS↔PL 跨时钟、A2 直通 vs 帧缓存对比、端到端指标与上板演示（10/12 M2 验收）。

## 设计要求

- 全流水无帧缓存依赖，像素级延迟固定可测
- 参数经 AXI-Lite 由 PS / RISC-V 动态配置

## 设计参考

- 往届获奖作品深度拆解：[docs/track_research.md](../../docs/track_research.md)——Ultra-Vision（2024 易灵思国一）的乒乓缓冲、尺寸切换延迟对齐、数据修饰模块、输出画布填充与 ADV7611/EDID 初始化链路
- 演示层升级任务（A1 参数化链路、A2 直通 vs 帧缓存对比、A4 OSD 动效）：[docs/proposal_upgrade.md](../../docs/proposal_upgrade.md)
