# 模块二上板证据（2026-10-03）

首次实机加载与全链验证。板卡 PYNQ-Z2（pynq 3.1 镜像），overlay 来自
`sim/build/hdmi-project/vision.xsa`（物理 HDMI 工程，布线收敛、DRC 0 错）。
部署包由 `bash sim/scripts/make_board_pkg.sh` 组装，scp 至板端 `~/vision_m2/`。
视频源 = 笔记本 HDMI→HDMI IN（1280×720）；观测 = 板卡 HDMI OUT→USB 采集卡→本机 UVC
（OpenCV DSHOW idx1，设备名 "USB Video"，VID_345F）。

## 结果总表

| 步骤 | 命令/工具 | 结果 | 证据 |
|:---|:---|:---|:---|
| env | `m2_onboard.py env` | PASS：pynq 3.1，包内文件齐全 | env.log |
| load | `sudo … m2_onboard.py load` | PASS：bit 下载，ip_dict `pipe @ 0x40000000` 与 BD 一致 | load.log |
| smoke | `sudo … m2_onboard.py smoke` | PASS：commit 配置号 0→1→2 帧首确认（视频在位） | smoke.log |
| demo | `sudo … m2_onboard.py demo` | PASS：4 拓扑 + 60 组 OSD 框 + SNAPSHOT，65 次 commit 全帧首确认 | demo.log |
| 直通画面 | OpenCV DSHOW 抓帧 | 1280×720 彩色桌面实时回传，色彩无通道错乱 | capture_idx1_0/1.png |
| 活性+延迟 | `screen_probe.py`（全屏白→黑） | 108 帧连拍全收到；**延迟上界 125 ms**（含采集卡 1-2 帧缓冲，不计指标口径） | probe/probe_0003.png（白）、probe_0008.png（黑） |
| EXE 联调 | `vision_preview.exe --source 1` | 窗口显示采集卡实时视频，横幅 "VIDEO ONLY \| UNASSOCIATED \| no board recognition"，无假框 | exe_preview.png |
| 断连/重连（修复前） | `watch_video.py` 监视 | **复现 PS 挂死**：拔 HDMI 时 PS 轮询在途 → 内核冻结，串口/网口同死 | watch.log / watch2.log（无数据：挂死后页缓存未刷盘） |
| 断连/重连（修复后） | 脱离式 watcher + 实际拔插 | **PASS**：`VIDEO_OK → NO_VIDEO(169.6s) → BUSY(170.6s) → VIDEO_OK cfg=410(180.2s)`；uptime 50min 未重启，串口/网口全程在线；pending 提交在恢复后首帧应用（契约语义） | watch7.log |
| 修复后直通 | OpenCV 抓帧 | 彩色/字节序正确，重建 bit 直通无回归 | capture_postfix_0.png |

smoke 一次 NOVIDEO 为 bit 重载后 dvi2rgb 未及重锁的竞争（同一 shell 紧跟 load），
等待数秒后重跑 PASS；非硬件故障。

## 结论（对照离板验收边界）

- 实机下载、TMDS 引脚、真实源锁定、采集卡显示闭环：**今日成立**。
- 端到端延迟：经采集卡观测上界 125 ms，其中采集卡缓冲占大头；PL 直通本体远小于此。
- 仍待实测（次晨）：源断连/重连恢复、EDID 换源、真实 HDMI 摄像头源、DDR 对照。

## 断连实测暴露的真 bug 与修复（2026-10-03 深夜）

断连/重连实测两次复现**PS 总线挂死**：拔 HDMI IN 瞬间串口与网口同时失联（系统级冻结），
板卡断电重启可恢复。根因：`vision_axi` 把 `video_locked` 并入整个 `rst_n`，连带复位
axi_regs/config_bridge——PS 轮询的在途 AXI 事务响应永不返回（BRESP/RRESP 丢失）→ 内核冻结。
网线/供电排除（12V 适配器、dmesg 无网口断链记录）。

修复：AXI 域新增独立 `axi_rst_n`（只随 s_axi_aresetn），像素域保持 `video_locked` 组合复位；
已提交配置随之保留，恢复后未确认提交在首帧生效（契约语义不变）。

- 复现 tb：`sim/vision/tb_axi_lock_reset.v`（基线/写在途/读在途/恢复保持），已入 `all` 回归。
- 修复前失败证据：`axi-lock/axi-lock-before.log`（FATAL: write response lost on lock drop）。
- 修复后：`axi-lock/axi-lock-after.log` PASS；全量回归 `all-after-fix.log` 48 PASS
  （FAIL/FATAL 行均为门禁自检 8 例故意注入）。
- 物理 bit 重建：`hdmi-rebuild-after-fix.log` PASS——布线后 **WNS +0.956 / WHS +0.054**（12397 端点全收敛，
  优于离板轮次 +0.330）；bitgen 成功、XSA 含 bit+hwh（zip 高压缩故文件小）、DRC 无阻塞项、
  引脚全分配（脚本三重门禁）。重部署 + 修复后拔插复测已过（结果表）。

## 板端环境备忘（本镜像与官方默认的差异，复现必读）

- pynq 装于 `/usr/local/share/pynq-venv`（裸 `python3` 无 pynq）；PATH 中 `/opt/python3.10` 为陈旧项。
- `/dev/dri/renderD128` 属 root:render——`xilinx` 原不在 render/video 组，已 `usermod -aG`；
  Overlay/MMIO/SLCR 均需 root（Jupyter 服务以 root 运行故此前未暴露）。
- eth0 无 DHCP 时仅静态别名 192.168.2.99；本次以直连 PC + link-local
  169.254.87.99/16 建链（运行时临时地址，重启即失）。
- bit 为易失配置：板卡断电后需重新 `m2_onboard.py load`。

## 复现入口

PC 侧（仓库内工具在 `sim/build/tools/`，构建产物不入库）：
`grab_capture.py`（UVC 抓帧）、`screen_probe.py`（活性/延迟探针）、`screenshot.ps1`（截屏）。
板侧四步见 `src/pynq_host/m2_onboard.py`；断连监视 `src/pynq_host/watch_video.py`。
