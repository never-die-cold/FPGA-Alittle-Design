# src/vision —— HDMI 图像预处理流水线 RTL

HDMI 视频流逐像素实时处理：灰度化 → 3×3 高斯滤波 → 双线性缩放 → 可选 Sobel 边缘。

## 规划内容

- `vision_top.v`：流水线顶层（HDMI IN 解码 → 处理链 → OSD/HDMI OUT）
- `rgb2gray.v`：RGB 转灰度
- `gaussian_3x3.v`：高斯滤波（行缓存调度）
- `scaler.v`：双线性缩放至网络输入尺寸
- `sobel.v`：Sobel 边缘检测（可选级）
- `line_buffer.v`：行缓存
- `osd_overlay.v`：检测结果叠加显示
- `axi_regs.v`：AXI-Lite 参数寄存器（滤波系数、缩放尺寸、ROI）

## 设计要求

- 全流水无帧缓存依赖，像素级延迟固定可测
- 参数经 AXI-Lite 由 PS / RISC-V 动态配置

> 状态：🚧 待开发（M2 里程碑）
