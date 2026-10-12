# C01 集成与取帧方案：2026-10-11 审查稿

状态：方案草稿，未冻结；不代表集成 RTL、位流或 N03 已验收。
基线：dev/model @ c292038；现场接线依据用户本次说明。

## 当前系统

```text
CM3 → 树莓派（外部电源）→ HDMI → PYNQ-Z2 HDMI IN
                                      │ PYNQ 外部电源
                                      └ HDMI OUT → 采集卡 → USB → 电脑
电脑 USB → COM12/115200 → PYNQ shell
电脑 Ethernet → 树莓派 SSH（PYNQ eth0 当前 DOWN）
```

当前视频自定义位流只有 PS GP0→AXI-Lite 配置和 RGB 直通显示。
`create_hdmi_bd.tcl` 未例化 VDMA、RISC-V SoC 或 CNN；snapshot_debug 仅接 ILA。
不能从显示成功推断 PS 能读取原图，也不能把 224×224 灰度分析快照当原彩色 ROI。

## 两个交付阶段

1. 软件诊断：加载 PYNQ base，HDMI IN→VDMA→DDR 完整 BGR 帧副本，
   用同帧做定位/ROI/FP32诊断；配置并启动 HDMI OUT，验证与取帧共存。
   base 是整片替换，期间自定义视觉/RISC-V/CNN不运行。
2. 最终集成：保留自定义 RGB 显示支路，增加独立原彩色捕获支路与 AXI-stream/VDMA，
   PS 从 DDR 读取本轮完整副本，定位/共享 ROI 后把输入送往 CNN；
   RISC-V 调度、汇总并按工单判定，PS 服务管理检查及结果。
   此阶段需要 JL/WC/NC 冻结接口、生成新 bit/hwh 并上板验收。

## 内存与接口审查表

| 通路/存储 | 当前状态 | 建议与预算 |
| --- | --- | --- |
| 视觉配置 | 已有：pipe 0x40000000，64 KiB | 保留现有地址和帧首提交语义 |
| 原帧 DDR | 自定义位流未实现 | 1280×720×3=2,764,800 字节/帧；3帧约7.91 MiB |
| 完整帧副本 | N03未验证 | uint8 BGR，720×1280×3；必须先复制再释放DMA缓冲 |
| 捕获写DDR带宽 | 未实测 | 720p60纯像素约165.9 MB/s，不含协议/仲裁开销 |
| 显示支路 | 已有彩色直通 | 捕获拥塞不得向显示施加反压；拥塞时丢弃整帧并记录 |
| 像素→AXI时钟域 | 新捕获链未实现 | 显式异步FIFO/时钟转换、完整帧和溢出规则 |
| PS DDR接口 | 新捕获链未实现 | 需启用HP口并审查突发、缓存一致性、中断和驱动 |
| ROI输入 | 离板共享模块已验证 | 同一capture的半开框→64×64 GRAY8，4096字节/目标 |
| CNN权重/激活 | 正式INT8未实现 | C02冻结量化、排布和缓存，不能沿用FP32预算作为实测 |
| 核/CNN/PS寄存器 | 未冻结/未实现 | C03明确地址、握手、超时、复位、目标关联及结果布局 |
| 网络结果 | PYNQ当前无网口链路 | 首先串口诊断；N06/N09前需独立提供PYNQ网络路由 |

165.9 MB/s仅为捕获写入理想字节率；PS复制/处理与VDMA显示回读另增DDR流量。
最终设计若保留直接显示，不能引用base经DDR显示的延迟作为自定义直通延迟。

## N03 具体下一步

- 先加载并烟测现有vision，确认采集卡实际画面恢复，保存boot_id与位流指纹。
- 核实板端base路径/哈希、OpenCV/NumPy/PYNQ及视频驱动版本。
- 现有`n03_board_capture.py`只启动HDMI IN；需补HDMI OUT配置/启动/关联及finally清理。
- 用新的capture文件名；现有n03-base-001.png若已存在不能覆盖。
- 按实际驱动核对mode/shape/dtype/stride；复制后释放DMA缓冲，PNG逐像素回读与SHA256。
- 同时取得UVC画面；两个来源未做帧号关联，不宣称逐帧对应。
- 验证结束恢复原vision位流，重建驱动后再烟测与UVC取图。
- base取帧成功仅算软件诊断；自定义原帧捕获/核/CNN集成仍未实现。

依据：仓库`docs/inspection-v0-contract.md`、`sim/scripts/create_hdmi_bd.tcl`、
`src/vision/vision_axi.v`、`sim/scripts/n03_board_capture.py`及本次现场日志。
PYNQ官方视频API：<https://pynq.readthedocs.io/en/latest/pynq_libraries/video.html>；
文档支持hdmi_in.tie(hdmi_out)后读取输入帧，实际板端版本仍需核实。

## 2026-10-11实机进展（补记）

现有vision位流重载与帧首烟测通过，UVC真实画面恢复，已留日志。
N03首试输出全零PS帧；暖机复验读到5帧非零像素后停滞并超时，随后vision恢复进程段错误。
已软件重启PYNQ并确认启动输出；原视频恢复待用户登录/sudo后完成。
最终取帧脚本使用PIXEL_BGR、HDMI OUT共存、独立副本和每帧5秒异步超时；四类离板检查通过，实机未复验。
因此C01仍为未冻结草稿，N03仍未通过。详细证据：data/logs/2026-10-11-onboard-resume/README.md。


## 输入隔离诊断补记

此前重启后vision加载/烟测及UVC真画面已恢复。后续仅HDMI IN模式读到两帧非零像素后段错误139，未完成清理；新进程的PL元数据查询也段错误，已再次发起软件重启。
实际缓冲函数离板复现了缓存归还后第二次释放会munmap的分支，尚不能定为唯一根因；未修改板端驱动。最终恢复待认证后复验。C01仍未冻结，N03仍未通过；不推进N04/N05正式采集。


## 最终恢复完成

第二次重启后认证成功，vision加载/帧首smoke及24帧UVC抓图均退出0，实际视频已恢复。boot_id=f3321177-d8ab-4db8-9c1e-04f9f0cfe40f，恢复过程未再重启，bit/hwh指纹与原版本一致。本节替代之前恢复待认证的状态。N03仍未通过，C01仍未冻结；本轮不继续base取帧。
