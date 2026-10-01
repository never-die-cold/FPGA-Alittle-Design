# src/vision —— HDMI 图像预处理流水线 RTL

HDMI 视频流逐像素实时处理：灰度化 → 3×3 高斯滤波 → 双线性缩放 → 可选 Sobel 边缘。

## 当前状态（2026-09-29，单元级超前完成）

回归入口 `bash sim/scripts/run_vision_iverilog.sh all`，10/10 tb PASS；日志 `data/logs/2026-09-29-vision-m2-kickoff/vision-all-10tb.log`。

| 模块 | 状态 | 要点 |
|:---|:---|:---|
| `rgb2gray.v` | 已实现 | BT.601 定点，黄金参考逐像素对拍 |
| `line_buffer.v` | 已实现 | 同步读、同拍同址先读后写（旧值） |
| `gaussian_3x3.v` | 已实现 | 双行缓存轮替、边界钳位、vblank 冲刷末行 |
| `scaler.v` | 已实现 | 16.16 定点双线性、行槽滑动、自产 `out_vs/out_hs` 标记；2026-09-30 插值链切拍（错半拍预寻址），real 档 OOC ≈94.9 MHz，720p60 达标 |
| `sobel.v` | 已实现 | Gx/Gy L1 幅值饱和；单元级 PASS，未接入 `vision_top` |
| `osd_overlay.v` | 已实现 | box/roi 双框叠加、帧首参数锁存 |
| `axi_regs.v` | 已实现 | AXI-Lite 16 寄存器；`AW` 须满足 `2^AW > NREG*4` |
| `vision_top.v` | 骨架 | rgb2gray 恒接 + gauss/scaler/osd 开关，帧首拓扑锁存 |

实现口径见 [design_v0.md](design_v0.md) §3.1/§3.2；接口契约仍为草案，10/5 评审后升格冻结。

## 验证与复现（watercopper 评审入口）

全部验证可由仓库内脚本一键复现（前置：MSYS2 UCRT64 的 iverilog 13.0+；OOC 另需 Vivado 2026.1）：

| 步骤 | 命令 | 期望 |
|:---|:---|:---|
| 黄金参考再生成 | `python data/golden/vision/rgb2gray/gen_rgb2gray.py`（另 gaussian3x3/scaler/sobel/osd/fullchain 各自目录下 `gen_*.py`） | 每个 `PASS`（含定点 vs 浮点自检） |
| 单元+链路回归 | `bash sim/scripts/run_vision_iverilog.sh all` | 10/10 tb `PASS`，逐像素 0 错误 |
| 单项回归 | `bash sim/scripts/run_vision_iverilog.sh <rgb2gray\|linebuf\|gaussian\|scaler\|sobel\|chain\|fullchain\|osd\|axi\|top>` | 对应 tb `PASS` |
| OOC 综合（单元参数） | `bash sim/scripts/run_vivado_vision_ooc.sh unit` | 各模块 `OOC_RESULT` 行 |
| OOC 综合（720p 行宽） | `bash sim/scripts/run_vivado_vision_ooc.sh real` | 同上，含 BRAM 推断 |

验证方法：每个处理模块由 `data/golden/vision/<模块>/gen_*.py` 生成输入 hex 与期望 hex，tb 逐像素 `!==` 比对，错 1 像素即 FAIL；链路 tb（chain/fullchain/top）中间级与末端同时对拍；OSD 双帧 golden 验证"参数帧首锁存"；tb_scaler 含标记协议断言（vs 每帧 1 次、hs 每行 1 次、vs 先于首个 de）。tb 清单与断言点见 [design_v0.md](design_v0.md) §3.1。

评审关注点（模块二特有的坑，均有 tb 用例覆盖）：line_buffer 先读后写语义、gaussian 末行 vblank 冲刷 + 合成 hs、直通行尾 hs 门控（输入行 0 的 hs 不对应输出行）、scaler 发射/写入解耦与多帧复位、axi_regs 地址空间约束 `2^AW > NREG*4`。

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
